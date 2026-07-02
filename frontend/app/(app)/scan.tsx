import { Ionicons } from "@expo/vector-icons";
import { CameraView, useCameraPermissions } from "expo-camera";
import * as ImageManipulator from "expo-image-manipulator";
import { router } from "expo-router";
import { useRef, useState } from "react";
import { ActivityIndicator, Image, Linking, Platform, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SafetyBadge } from "@/src/components/SafetyBadge";
import { api, type FoodScan, type SafetyTier } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

export default function ScanScreen() {
  const { t } = useLang();
  const [permission, requestPermission] = useCameraPermissions();
  const camRef = useRef<CameraView>(null);
  const [photo, setPhoto] = useState<{ uri: string; base64: string } | null>(null);
  const [result, setResult] = useState<FoodScan | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!permission) {
    return (
      <SafeAreaView style={styles.safe}><View style={styles.center}><ActivityIndicator color={COLORS.brand} /></View></SafeAreaView>
    );
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
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
        </View>
      </SafeAreaView>
    );
  }

  const takePhoto = async () => {
    if (!camRef.current) return;
    setError(null);
    try {
      const shot = await camRef.current.takePictureAsync({ quality: 0.6, base64: false, skipProcessing: true });
      if (!shot?.uri) return;
      // Resize + re-encode as JPEG for a small, valid payload
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

  const reset = () => {
    setPhoto(null);
    setResult(null);
    setError(null);
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.header}>
        <View style={styles.headerIcon}><Ionicons name="camera" size={22} color={COLORS.textInverse} /></View>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{t("scanTitle")}</Text>
          <Text style={styles.subtitle}>{t("scanIntro")}</Text>
        </View>
      </View>

      <View style={styles.body}>
        {!photo ? (
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
              <ScanResultCard result={result} onSeeMore={() => result.matched_food_id && router.push(`/food/${result.matched_food_id}`)} tSeeMore={t("seeMore")} />
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
        )}
      </View>
    </SafeAreaView>
  );
}

function ScanResultCard({ result, onSeeMore, tSeeMore }: { result: FoodScan; onSeeMore: () => void; tSeeMore: string }) {
  const tier = (result.safety_tier || "YELLOW") as SafetyTier;
  const meta = TIER_META[tier];
  return (
    <View testID="scan-result" style={[styles.resultCard, { borderColor: meta.border, backgroundColor: meta.bg }]}>
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
        <View style={{ flex: 1, marginRight: 10 }}>
          <Text style={styles.resultName}>{result.food_name}</Text>
          {result.hindi_name ? <Text style={styles.resultHindi}>{result.hindi_name}</Text> : null}
        </View>
        <SafetyBadge tier={tier} compact />
      </View>
      <Text style={styles.resultLine}><Text style={styles.bold}>Risk: </Text>{result.primary_risk_factor}</Text>
      <Text style={styles.resultLine}><Text style={styles.bold}>Portion: </Text>{result.portion_limit_text}</Text>
      <Text style={styles.resultLine}>{result.clinical_tip}</Text>
      {result.matched_food_id ? (
        <TouchableOpacity testID="scan-see-details" style={styles.linkBtn} onPress={onSeeMore}>
          <Text style={styles.linkText}>{tSeeMore}</Text>
          <Ionicons name="arrow-forward" size={16} color={COLORS.brand} />
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  header: { flexDirection: "row", alignItems: "center", gap: 12, padding: SIZE.m },
  headerIcon: { width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center" },
  title: { fontSize: FONT.h2, fontWeight: "800", color: COLORS.textPrimary },
  subtitle: { fontSize: FONT.label, color: COLORS.textSecondary },
  body: { flex: 1, padding: SIZE.m },
  camWrap: { flex: 1, borderRadius: SIZE.radiusLg, overflow: "hidden", backgroundColor: "#000", position: "relative" },
  webPlaceholder: { flex: 1, alignItems: "center", justifyContent: "center", padding: SIZE.l, gap: SIZE.m, backgroundColor: COLORS.bgAlt },
  webPlaceholderText: { fontSize: FONT.body, color: COLORS.textSecondary, textAlign: "center", lineHeight: 22 },
  shutterRow: { position: "absolute", bottom: 24, left: 0, right: 0, alignItems: "center" },
  shutter: {
    width: 74, height: 74, borderRadius: 37, backgroundColor: COLORS.brand,
    alignItems: "center", justifyContent: "center", borderWidth: 4, borderColor: "#fff",
  },
  preview: { height: 240, borderRadius: SIZE.radiusLg, overflow: "hidden", backgroundColor: COLORS.bgAlt },
  previewImg: { width: "100%", height: "100%" },
  actionRow: { flexDirection: "row", gap: SIZE.s, marginTop: "auto" },
  primaryBtn: {
    height: SIZE.touchPrimary, borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center", paddingHorizontal: SIZE.l,
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
});
