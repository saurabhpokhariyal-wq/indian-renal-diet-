import { Ionicons } from "@expo/vector-icons";
import { CameraView, useCameraPermissions, type BarcodeScanningResult, type BarcodeType } from "expo-camera";
import * as ImageManipulator from "expo-image-manipulator";
import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Image, Linking, Platform, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { NutrientBar } from "@/src/components/NutrientBar";
import { CheckFoodModeSwitcher } from "@/src/components/CheckFoodModeSwitcher";
import { MealTextInput } from "@/src/components/MealTextInput";
import { SafetyBadge } from "@/src/components/SafetyBadge";
import { api, type FoodScan, type NutrientLimits, type ScanTier } from "@/src/lib/api";
import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import { mgToUserUnit } from "@/src/lib/units";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

type Mode = "vision" | "barcode" | "text";

function isoToday(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

const BARCODE_TYPES: BarcodeType[] = [
  "ean13",
  "ean8",
  "upc_a",
  "upc_e",
  "code128",
  "code39",
  "code93",
  "codabar",
  "itf14",
];

export default function ScanScreen() {
  const { t } = useLang();
  const params = useLocalSearchParams<{ mode?: string; date?: string; meal_type?: string }>();
  const initialMode: Mode = params.mode === "text" ? "text" : params.mode === "barcode" ? "barcode" : "vision";
  const [permission, requestPermission] = useCameraPermissions();
  const camRef = useRef<CameraView>(null);
  const [mode, setMode] = useState<Mode>(initialMode);
  const [photo, setPhoto] = useState<{ uri: string; base64: string } | null>(null);
  const [result, setResult] = useState<FoodScan | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [barcodeLookup, setBarcodeLookup] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastScannedRef = useRef<string | null>(null);
  const [limits, setLimits] = useState<NutrientLimits | null>(null);
  const [favorited, setFavorited] = useState(false);
  const [logged, setLogged] = useState(false);
  const [actionBusy, setActionBusy] = useState<"none" | "log" | "fav">("none");

  // Lazily load today's nutrient limits once the user opens the screen
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await api.getMealSummary(isoToday());
        if (!cancelled) setLimits(s.limits);
      } catch {
        /* offline / unauth — bars will simply not render */
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // On web the CameraView is replaced by a static placeholder anyway, so
  // we skip the permission bubble entirely — otherwise the mode chips are
  // hidden by the early return and web users can't switch to Text/Barcode.
  const skipPermCheck = Platform.OS === "web" || mode === "text";

  if (!permission && !skipPermCheck) {
    return (
      <SafeAreaView style={styles.safe}><View style={styles.center}><ActivityIndicator color={COLORS.brand} /></View></SafeAreaView>
    );
  }

  if (permission && !permission.granted && !skipPermCheck) {
    return (
      <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
        <CheckFoodModeSwitcher current={mode === "text" ? "voice" : "photo"} />
        <View style={styles.center}>
          <View style={styles.permBubble}><Ionicons name="camera" size={40} color={COLORS.textInverse} /></View>
          <Text style={styles.title}>{t("scanPermissionTitle")}</Text>
          <Text style={styles.subtitle}>{t("scanPermissionBody")}</Text>
          {permission.canAskAgain ? (
            <TouchableOpacity testID="grant-camera" style={styles.primaryBtn} onPress={requestPermission}>
              <Text style={styles.primaryText}>{t("grantPermission")}</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity testID="open-settings" style={styles.primaryBtn} onPress={() => Linking.openSettings()}>
              <Text style={styles.primaryText}>{t("openSettings")}</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity
            testID="scan-switch-to-text"
            style={[styles.secondaryBtn, { marginTop: SIZE.s }]}
            onPress={() => setMode("text")}
          >
            <Ionicons name="mic" size={18} color={COLORS.brand} />
            <Text style={styles.secondaryText}>{t("checkModeVoice")}</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const switchMode = (m: Mode) => {
    if (m === mode) return;
    setMode(m);
    setPhoto(null);
    setResult(null);
    setError(null);
    lastScannedRef.current = null;
  };

  const takePhoto = async () => {
    if (!camRef.current) return;
    setError(null);
    try {
      const shot = await camRef.current.takePictureAsync({ quality: 0.6, base64: false, skipProcessing: true });
      if (!shot?.uri) return;
      const manipulated = await ImageManipulator.manipulateAsync(
        shot.uri,
        [{ resize: { width: 900 } }],
        { compress: 0.7, format: ImageManipulator.SaveFormat.JPEG, base64: true },
      );
      if (!manipulated.base64) throw new Error("Could not encode image");
      setPhoto({ uri: manipulated.uri, base64: manipulated.base64 });
      setResult(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Camera error");
    }
  };

  const analyze = async () => {
    if (!photo || analyzing) return;
    setAnalyzing(true);
    setError(null);
    try {
      const r = await api.scanFood(photo.base64);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const onBarcode = async (r: BarcodeScanningResult) => {
    const data = (r?.data || "").trim();
    if (!data || barcodeLookup) return;
    if (lastScannedRef.current === data) return;
    lastScannedRef.current = data;
    setBarcodeLookup(true);
    setError(null);
    setFavorited(false);
    setLogged(false);
    try {
      const scan = await api.scanBarcode(data);
      setResult(scan);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Barcode lookup failed";
      setError(msg.toLowerCase().includes("not found") ? t("barcodeNotFound") : msg);
      setTimeout(() => { lastScannedRef.current = null; }, 1500);
    } finally {
      setBarcodeLookup(false);
    }
  };

  const reset = () => {
    setPhoto(null);
    setResult(null);
    setError(null);
    setFavorited(false);
    setLogged(false);
    setActionBusy("none");
    lastScannedRef.current = null;
  };

  const doLogPack = async () => {
    if (!result?.matched_food_id || actionBusy !== "none") return;
    setActionBusy("log");
    try {
      await api.addMealLog(result.matched_food_id, isoToday(), "snack");
      setLogged(true);
      // refresh limits/totals so the badge reflects new state on next open
      try { const s = await api.getMealSummary(isoToday()); setLimits(s.limits); } catch { /* noop */ }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not log pack");
    } finally {
      setActionBusy("none");
    }
  };

  const doToggleFavorite = async () => {
    if (!result?.matched_food_id || actionBusy !== "none") return;
    setActionBusy("fav");
    try {
      const r = await api.toggleFavorite(result.matched_food_id);
      setFavorited(r.is_favorite);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not toggle favorite");
    } finally {
      setActionBusy("none");
    }
  };

  const showingResult = !!result;

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <CheckFoodModeSwitcher current={mode === "text" ? "voice" : "photo"} />
      <View style={styles.header}>
        <View style={styles.headerIcon}>
          <Ionicons name={mode === "vision" ? "camera" : mode === "barcode" ? "barcode" : "mic"} size={22} color={COLORS.textInverse} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{mode === "text" ? t("logByTextTitle") : t("scanTitle")}</Text>
          <Text style={styles.subtitle}>
            {mode === "vision" ? t("scanIntro") : mode === "barcode" ? t("barcodeIntro") : t("logByTextSub")}
          </Text>
        </View>
      </View>

      {/* Mode toggle — 3 pills: photo / barcode / text (natural-language) */}
      <View style={styles.modeRow}>
        <ModeChip
          testID="scan-mode-vision"
          label={t("scanModeVision")}
          icon="camera"
          active={mode === "vision"}
          onPress={() => switchMode("vision")}
        />
        <ModeChip
          testID="scan-mode-barcode"
          label={t("scanModeBarcode")}
          icon="barcode"
          active={mode === "barcode"}
          onPress={() => switchMode("barcode")}
        />
        <ModeChip
          testID="scan-mode-text"
          label={t("scanModeText")}
          icon="mic"
          active={mode === "text"}
          onPress={() => switchMode("text")}
        />
      </View>

      <View style={styles.body}>
        {mode === "text" ? (
          <MealTextInput date={params.date} mealType={params.meal_type || "meal"} />
        ) : mode === "vision" ? (
          !photo ? (
            <View style={styles.camWrap}>
              {Platform.OS === "web" ? (
                <View style={styles.webPlaceholder}>
                  <Ionicons name="phone-portrait" size={48} color={COLORS.textSecondary} />
                  <Text style={styles.webPlaceholderText}>
                    Camera preview is best on the mobile device. Open this app on your phone via Expo Go to scan foods.
                  </Text>
                </View>
              ) : (
                <CameraView ref={camRef} style={StyleSheet.absoluteFill} facing="back" />
              )}
              <View style={styles.shutterRow}>
                <TouchableOpacity testID="scan-take-photo" style={styles.shutter} onPress={takePhoto}>
                  <Ionicons name="camera" size={28} color={COLORS.textInverse} />
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <View style={{ flex: 1, gap: SIZE.m }}>
              <View style={styles.preview}>
                <Image source={{ uri: photo.uri }} style={styles.previewImg} />
              </View>

              {result ? (
                <ScanResultCard
                  result={result}
                  onSeeMore={() => result.matched_food_id && router.push(`/food/${result.matched_food_id}`)}
                  tSeeMore={t("seeMore")}
                  tBrand={t("brand")}
                />
              ) : null}

              {error ? <Text testID="scan-error" style={styles.error}>{error}</Text> : null}

              <View style={styles.actionRow}>
                <TouchableOpacity testID="scan-retake" style={styles.secondaryBtn} onPress={reset}>
                  <Ionicons name="refresh" size={20} color={COLORS.brand} />
                  <Text style={styles.secondaryText}>{t("scanRetake")}</Text>
                </TouchableOpacity>
                {!result ? (
                  <TouchableOpacity
                    testID="scan-analyze"
                    style={[styles.primaryBtn, { flex: 1 }, analyzing && { opacity: 0.5 }]}
                    onPress={analyze}
                    disabled={analyzing}
                  >
                    {analyzing ? (
                      <View style={{ flexDirection: "row", gap: 8, alignItems: "center" }}>
                        <ActivityIndicator size="small" color={COLORS.textInverse} />
                        <Text style={styles.primaryText}>{t("scanAnalyzing")}</Text>
                      </View>
                    ) : (
                      <Text style={styles.primaryText}>{t("scanAnalyze")}</Text>
                    )}
                  </TouchableOpacity>
                ) : null}
              </View>
            </View>
          )
        ) : (
          // Barcode mode
          <View style={{ flex: 1, gap: SIZE.m }}>
            {!showingResult ? (
              <View style={styles.camWrap}>
                {Platform.OS === "web" ? (
                  <View style={styles.webPlaceholder}>
                    <Ionicons name="barcode" size={48} color={COLORS.textSecondary} />
                    <Text style={styles.webPlaceholderText}>
                      Barcode scanning is available on the mobile device. Open this app on your phone via Expo Go.
                    </Text>
                  </View>
                ) : (
                  <CameraView
                    ref={camRef}
                    style={StyleSheet.absoluteFill}
                    facing="back"
                    barcodeScannerSettings={{ barcodeTypes: BARCODE_TYPES }}
                    onBarcodeScanned={onBarcode}
                  />
                )}
                {/* Overlay frame */}
                <View style={[styles.barcodeOverlay, { pointerEvents: "none" }]}>
                  <View style={styles.barcodeFrame} />
                  <Text style={styles.barcodeHint}>
                    {barcodeLookup ? t("barcodeLookingUp") : t("barcodeAlignHint")}
                  </Text>
                  {barcodeLookup ? (
                    <ActivityIndicator size="small" color={COLORS.textInverse} style={{ marginTop: 8 }} />
                  ) : null}
                </View>
              </View>
            ) : null}

            {result ? (
              <>
                <ScanResultCard
                  result={result}
                  onSeeMore={() => result.matched_food_id && router.push(`/food/${result.matched_food_id}`)}
                  tSeeMore={t("seeMore")}
                  tBrand={t("brand")}
                />
                <PackNutrientPanel result={result} limits={limits} title={t("perPackNutrients")} labels={{
                  potassium: t("nutrientPotassium"),
                  phosphorus: t("nutrientPhosphorus"),
                  sodium: t("nutrientSodium"),
                }} />
                {logged ? (
                  <View testID="pack-logged-flash" style={styles.loggedFlash}>
                    <Ionicons name="checkmark-circle" size={18} color={COLORS.greenText} />
                    <Text style={styles.loggedFlashText}>{t("packLogged")}</Text>
                  </View>
                ) : null}
              </>
            ) : null}

            {error && !showingResult ? <Text testID="scan-error" style={styles.error}>{error}</Text> : null}
            {error && showingResult ? <Text testID="scan-action-error" style={styles.error}>{error}</Text> : null}

            {showingResult ? (
              <View style={styles.packActionsWrap}>
                <TouchableOpacity
                  testID="pack-favorite"
                  style={[styles.iconAction, favorited && styles.iconActionActive]}
                  onPress={doToggleFavorite}
                  disabled={!result?.matched_food_id || actionBusy !== "none"}
                  accessibilityLabel={favorited ? t("unfavorite") : t("favorite")}
                >
                  {actionBusy === "fav" ? (
                    <ActivityIndicator size="small" color={favorited ? COLORS.textInverse : COLORS.brand} />
                  ) : (
                    <Ionicons
                      name={favorited ? "star" : "star-outline"}
                      size={22}
                      color={favorited ? COLORS.textInverse : COLORS.brand}
                    />
                  )}
                </TouchableOpacity>
                <TouchableOpacity
                  testID="pack-log"
                  style={[styles.primaryBtn, { flex: 1 }, (logged || actionBusy === "log") && { opacity: 0.85 }]}
                  onPress={doLogPack}
                  disabled={!result?.matched_food_id || actionBusy !== "none" || logged}
                >
                  {actionBusy === "log" ? (
                    <ActivityIndicator size="small" color={COLORS.textInverse} />
                  ) : (
                    <Ionicons name={logged ? "checkmark" : "add-circle"} size={20} color={COLORS.textInverse} />
                  )}
                  <Text style={[styles.primaryText, { marginLeft: 6 }]}>
                    {logged ? t("added") : t("logThisPack")}
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity testID="barcode-rescan" style={styles.secondaryBtn} onPress={reset}>
                  <Ionicons name="scan" size={20} color={COLORS.brand} />
                  <Text style={styles.secondaryText}>{t("barcodeRescan")}</Text>
                </TouchableOpacity>
              </View>
            ) : null}
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

function ModeChip({
  label, icon, active, onPress, testID,
}: {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  active: boolean;
  onPress: () => void;
  testID: string;
}) {
  return (
    <TouchableOpacity testID={testID} style={[styles.modeChip, active && styles.modeChipActive]} onPress={onPress}>
      <Ionicons name={icon} size={18} color={active ? COLORS.textInverse : COLORS.brand} />
      <Text style={[styles.modeChipText, active && styles.modeChipTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

function ScanResultCard({
  result, onSeeMore, tSeeMore, tBrand,
}: {
  result: FoodScan;
  onSeeMore: () => void;
  tSeeMore: string;
  tBrand: string;
}) {
  const rawTier = (result.safety_tier || "UNVERIFIED") as ScanTier;
  const tier: ScanTier = ["GREEN", "YELLOW", "RED", "UNVERIFIED"].includes(rawTier) ? rawTier : "UNVERIFIED";
  const meta = TIER_META[tier];
  const isUnverified = tier === "UNVERIFIED";
  return (
    <View testID="scan-result" style={[styles.resultCard, { borderColor: meta.border, backgroundColor: meta.bg }]}>
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
        <View style={{ flex: 1, marginRight: 10 }}>
          <Text style={styles.resultName}>{result.food_name}</Text>
          {result.brand ? <Text style={styles.resultHindi}>{tBrand}: {result.brand}</Text> : null}
          {result.hindi_name ? <Text style={styles.resultHindi}>{result.hindi_name}</Text> : null}
        </View>
        <SafetyBadge tier={tier} compact />
      </View>
      {isUnverified ? null : (
        <Text style={styles.resultLine}><Text style={styles.bold}>Risk: </Text>{result.primary_risk_factor}</Text>
      )}
      <Text style={styles.resultLine}><Text style={styles.bold}>Portion: </Text>{result.portion_limit_text}</Text>
      <Text style={styles.resultLine}>{result.clinical_tip}</Text>
      {result.matched_food_id && !isUnverified ? (
        <TouchableOpacity testID="scan-see-details" style={styles.linkBtn} onPress={onSeeMore}>
          <Text style={styles.linkText}>{tSeeMore}</Text>
          <Ionicons name="arrow-forward" size={16} color={COLORS.brand} />
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

function PackNutrientPanel({
  result, limits, title, labels,
}: {
  result: FoodScan;
  limits: NutrientLimits | null;
  title: string;
  labels: { potassium: string; phosphorus: string; sodium: string };
}) {
  const { user } = useAuth();
  const unit = user?.nutrient_unit ?? "mg";
  const kMg = result.potassium_mg ?? 0;
  const p = result.phosphorus_mg ?? 0;
  const naMg = result.sodium_mg ?? 0;
  // If limits aren't loaded yet, use sensible defaults so bars still convey magnitude
  const kLimitMg = limits?.potassium_mg ?? 2000;
  const pLimit = limits?.phosphorus_mg ?? 1000;
  const naLimitMg = limits?.sodium_mg ?? 2000;

  // Only render if we actually have nutrient values (i.e., barcode result)
  if (kMg <= 0 && p <= 0 && naMg <= 0) return null;

  const kVal = mgToUserUnit("K", kMg, unit);
  const kLim = mgToUserUnit("K", kLimitMg, unit);
  const naVal = mgToUserUnit("Na", naMg, unit);
  const naLim = mgToUserUnit("Na", naLimitMg, unit);
  const dec = unit === "mEq" ? 1 : 0;

  return (
    <View testID="pack-nutrient-panel" style={styles.packPanel}>
      <View style={styles.packPanelHeader}>
        <Ionicons name="stats-chart" size={16} color={COLORS.brand} />
        <Text style={styles.packPanelTitle}>{title}</Text>
      </View>
      <NutrientBar testID="pack-potassium" label={labels.potassium} value={kVal} limit={kLim} unit={unit} decimals={dec} />
      <NutrientBar testID="pack-phosphorus" label={labels.phosphorus} value={p} limit={pLimit} />
      <NutrientBar testID="pack-sodium" label={labels.sodium} value={naVal} limit={naLim} unit={unit} decimals={dec} />
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  header: { flexDirection: "row", alignItems: "center", gap: 12, padding: SIZE.m, paddingBottom: 4 },
  headerIcon: { width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center" },
  title: { fontSize: FONT.h2, fontWeight: "800", color: COLORS.textPrimary },
  subtitle: { fontSize: FONT.label, color: COLORS.textSecondary },

  modeRow: {
    flexDirection: "row", gap: SIZE.s, paddingHorizontal: SIZE.m, paddingVertical: SIZE.s,
  },
  modeChip: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    height: 40, borderRadius: SIZE.radiusPill, borderWidth: 2, borderColor: COLORS.brand,
    backgroundColor: COLORS.brandLight,
  },
  modeChipActive: { backgroundColor: COLORS.brand },
  modeChipText: { color: COLORS.brand, fontWeight: "700", fontSize: FONT.body },
  modeChipTextActive: { color: COLORS.textInverse },

  body: { flex: 1, padding: SIZE.m, paddingTop: SIZE.s },
  camWrap: { flex: 1, borderRadius: SIZE.radiusLg, overflow: "hidden", backgroundColor: "#000", position: "relative" },
  webPlaceholder: { flex: 1, alignItems: "center", justifyContent: "center", padding: SIZE.l, gap: SIZE.m, backgroundColor: COLORS.bgAlt },
  webPlaceholderText: { fontSize: FONT.body, color: COLORS.textSecondary, textAlign: "center", lineHeight: 22 },
  shutterRow: { position: "absolute", bottom: 24, left: 0, right: 0, alignItems: "center" },
  shutter: {
    width: 74, height: 74, borderRadius: 37, backgroundColor: COLORS.brand,
    alignItems: "center", justifyContent: "center", borderWidth: 4, borderColor: "#fff",
  },

  barcodeOverlay: {
    position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
    alignItems: "center", justifyContent: "center",
  },
  barcodeFrame: {
    width: "78%", height: 160, borderRadius: 18, borderWidth: 3,
    borderColor: "rgba(255,255,255,0.9)", backgroundColor: "rgba(0,0,0,0.05)",
  },
  barcodeHint: {
    marginTop: 14, color: "#fff", fontWeight: "700", fontSize: FONT.body,
    backgroundColor: "rgba(0,0,0,0.55)", paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12,
    overflow: "hidden", textAlign: "center",
  },

  preview: { height: 240, borderRadius: SIZE.radiusLg, overflow: "hidden", backgroundColor: COLORS.bgAlt },
  previewImg: { width: "100%", height: "100%" },
  actionRow: { flexDirection: "row", gap: SIZE.s, marginTop: "auto" },
  primaryBtn: {
    height: SIZE.touchPrimary, borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center", paddingHorizontal: SIZE.l,
    flexDirection: "row",
  },
  primaryText: { color: COLORS.textInverse, fontSize: FONT.bodyL, fontWeight: "700" },
  secondaryBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    height: SIZE.touchPrimary, paddingHorizontal: SIZE.m, borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brandLight, borderWidth: 2, borderColor: COLORS.brand,
  },
  secondaryText: { color: COLORS.brand, fontWeight: "700", fontSize: FONT.body },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: SIZE.m, padding: SIZE.l },
  permBubble: { width: 72, height: 72, borderRadius: 36, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center" },
  error: { color: COLORS.redStrong, fontWeight: "600" },
  resultCard: { borderWidth: 2, borderRadius: SIZE.radiusLg, padding: SIZE.m, gap: 6 },
  resultName: { fontSize: FONT.h3, fontWeight: "800", color: COLORS.textPrimary },
  resultHindi: { fontSize: FONT.body, color: COLORS.textSecondary },
  resultLine: { fontSize: FONT.body, color: COLORS.textPrimary, lineHeight: 22 },
  bold: { fontWeight: "700" },
  linkBtn: { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 4, alignSelf: "flex-start" },
  linkText: { color: COLORS.brand, fontWeight: "700", fontSize: FONT.body },

  packPanel: {
    backgroundColor: COLORS.bgSurface, borderRadius: SIZE.radiusLg, padding: SIZE.m,
    borderWidth: 1, borderColor: COLORS.border, gap: SIZE.s,
  },
  packPanelHeader: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 4 },
  packPanelTitle: { fontSize: FONT.body, fontWeight: "700", color: COLORS.textPrimary },

  packActionsWrap: {
    flexDirection: "row", gap: SIZE.s, marginTop: "auto",
  },
  iconAction: {
    width: SIZE.touchPrimary, height: SIZE.touchPrimary, borderRadius: SIZE.radiusPill,
    borderWidth: 2, borderColor: COLORS.brand, backgroundColor: COLORS.brandLight,
    alignItems: "center", justifyContent: "center",
  },
  iconActionActive: { backgroundColor: COLORS.brand, borderColor: COLORS.brand },

  loggedFlash: {
    flexDirection: "row", alignItems: "center", gap: 8,
    alignSelf: "flex-start", paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: SIZE.radiusPill, backgroundColor: COLORS.greenBg, borderWidth: 1, borderColor: COLORS.greenBorder,
  },
  loggedFlashText: { color: COLORS.greenText, fontWeight: "700", fontSize: FONT.body },
});
