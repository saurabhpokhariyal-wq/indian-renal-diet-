import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Switch, Text, TextInput, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import type { Stage } from "@/src/lib/api";
import { COLORS, FONT, SIZE } from "@/src/theme";

export default function SettingsScreen() {
  const { user, signOut, setStage, updateProfile } = useAuth();
  const { lang, setLang, t } = useLang();
  const [diabetic, setDiabetic] = useState<boolean>(user?.diabetic ?? false);
  const [k, setK] = useState<string>("");
  const [p, setP] = useState<string>("");
  const [na, setNa] = useState<string>("");
  const [savingLimits, setSavingLimits] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);

  useEffect(() => {
    if (!user) return;
    setDiabetic(!!user.diabetic);
    const dl = user.doctor_limits;
    setK(dl?.potassium_mg ? String(dl.potassium_mg) : "");
    setP(dl?.phosphorus_mg ? String(dl.phosphorus_mg) : "");
    setNa(dl?.sodium_mg ? String(dl.sodium_mg) : "");
  }, [user]);

  const doSignOut = async () => {
    await signOut();
    router.replace("/(auth)/login");
  };

  const toggleDiabetic = async (v: boolean) => {
    setDiabetic(v);
    try { await updateProfile({ diabetic: v }); } catch { /* ignore */ }
  };

  const changeStage = async (s: Stage) => {
    if (s === user?.stage) return;
    try { await setStage(s); } catch { /* ignore */ }
  };

  const saveLimits = async () => {
    if (savingLimits) return;
    setSavingLimits(true);
    try {
      await updateProfile({
        doctor_limits: {
          potassium_mg: k ? Number(k) : null,
          phosphorus_mg: p ? Number(p) : null,
          sodium_mg: na ? Number(na) : null,
        },
      });
      setSavedFlash(true);
      setTimeout(() => setSavedFlash(false), 2000);
    } finally {
      setSavingLimits(false);
    }
  };

  const clearLimits = async () => {
    setK(""); setP(""); setNa("");
    try { await updateProfile({ doctor_limits: null }); } catch { /* ignore */ }
  };

  const stageLabel = user?.stage === "dialysis"
    ? t("stageDialysis")
    : user?.stage === "pre_dialysis"
      ? t("stagePreDialysis")
      : "—";

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
          <Text style={styles.title}>{t("settingsTitle")}</Text>

          <View style={styles.card}>
            <View style={styles.userRow}>
              <View style={styles.avatar}>
                <Ionicons name="person" size={26} color={COLORS.textInverse} />
              </View>
              <View style={{ flex: 1 }}>
                <Text testID="settings-user-name" style={styles.userName} numberOfLines={1}>
                  {user?.full_name || "Friend"}
                </Text>
                <Text style={styles.userEmail} numberOfLines={1}>{user?.email}</Text>
              </View>
            </View>
          </View>

          {/* Health profile */}
          <View style={styles.card}>
            <Text style={styles.section}>{t("healthProfile")}</Text>

            <View style={styles.rowBetween}>
              <View style={{ flex: 1 }}>
                <Text style={styles.rowLabel}>{t("stage")}</Text>
                <Text testID="settings-stage" style={styles.rowValue}>{stageLabel}</Text>
              </View>
            </View>
            <View style={styles.stageRow}>
              <TouchableOpacity
                testID="settings-stage-pre-dialysis"
                style={[styles.stageBtn, user?.stage === "pre_dialysis" && styles.stageBtnActive]}
                onPress={() => changeStage("pre_dialysis")}
              >
                <Text style={[styles.stageBtnText, user?.stage === "pre_dialysis" && styles.stageBtnTextActive]}>
                  {t("stagePreDialysis")}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                testID="settings-stage-dialysis"
                style={[styles.stageBtn, user?.stage === "dialysis" && styles.stageBtnActive]}
                onPress={() => changeStage("dialysis")}
              >
                <Text style={[styles.stageBtnText, user?.stage === "dialysis" && styles.stageBtnTextActive]}>
                  {t("stageDialysis")}
                </Text>
              </TouchableOpacity>
            </View>

            <View style={[styles.rowBetween, { marginTop: SIZE.s }]}>
              <View style={{ flex: 1 }}>
                <Text style={styles.rowLabel}>{t("diabetic")}</Text>
                <Text style={styles.rowSubtle}>{t("diabeticSub")}</Text>
              </View>
              <Switch
                testID="settings-diabetic-toggle"
                value={diabetic}
                onValueChange={toggleDiabetic}
                trackColor={{ true: COLORS.brand, false: COLORS.border }}
                thumbColor={COLORS.bgSurface}
              />
            </View>
          </View>

          {/* Doctor limits */}
          <View style={styles.card}>
            <Text style={styles.section}>{t("editLimits")}</Text>
            <Text style={styles.rowSubtle}>{t("doctorLimitsSub")}</Text>
            {!user?.doctor_limits ? (
              <Text testID="settings-limits-default" style={styles.defaultsPill}>{t("usingDefaults")}</Text>
            ) : null}

            <View style={styles.field}>
              <Text style={styles.fieldLabel}>{t("nutrientPotassium")} (mg)</Text>
              <TextInput
                testID="settings-limit-potassium"
                style={styles.input}
                value={k}
                onChangeText={(v) => setK(v.replace(/[^0-9]/g, ""))}
                keyboardType="number-pad"
                placeholder="e.g. 2000"
                placeholderTextColor="#A8A29E"
              />
            </View>
            <View style={styles.field}>
              <Text style={styles.fieldLabel}>{t("nutrientPhosphorus")} (mg)</Text>
              <TextInput
                testID="settings-limit-phosphorus"
                style={styles.input}
                value={p}
                onChangeText={(v) => setP(v.replace(/[^0-9]/g, ""))}
                keyboardType="number-pad"
                placeholder="e.g. 1000"
                placeholderTextColor="#A8A29E"
              />
            </View>
            <View style={styles.field}>
              <Text style={styles.fieldLabel}>{t("nutrientSodium")} (mg)</Text>
              <TextInput
                testID="settings-limit-sodium"
                style={styles.input}
                value={na}
                onChangeText={(v) => setNa(v.replace(/[^0-9]/g, ""))}
                keyboardType="number-pad"
                placeholder="e.g. 2000"
                placeholderTextColor="#A8A29E"
              />
            </View>

            <View style={{ flexDirection: "row", gap: SIZE.s }}>
              <TouchableOpacity
                testID="settings-save-limits"
                style={[styles.primaryBtn, savingLimits && { opacity: 0.6 }]}
                onPress={saveLimits}
                disabled={savingLimits}
              >
                <Text style={styles.primaryText}>
                  {savedFlash ? "✓" : t("doctorLimitsSave")}
                </Text>
              </TouchableOpacity>
              {user?.doctor_limits ? (
                <TouchableOpacity testID="settings-clear-limits" style={styles.linkBtn} onPress={clearLimits}>
                  <Text style={styles.linkText}>{t("usingDefaults")}</Text>
                </TouchableOpacity>
              ) : null}
            </View>
          </View>

          {/* Language */}
          <View style={styles.card}>
            <Text style={styles.section}>{t("language")}</Text>
            <View style={styles.langRow}>
              <LangButton testID="lang-en" label={t("english")} active={lang === "en"} onPress={() => setLang("en")} />
              <LangButton testID="lang-hi" label={t("hindi")} active={lang === "hi"} onPress={() => setLang("hi")} />
            </View>
          </View>

          {/* Disclaimer */}
          <View style={[styles.card, { backgroundColor: COLORS.brandLight, borderColor: COLORS.brand }]}>
            <View style={{ flexDirection: "row", gap: 10 }}>
              <Ionicons name="information-circle" size={22} color={COLORS.brand} />
              <Text style={styles.disclaimer}>{t("disclaimer")}</Text>
            </View>
            <TouchableOpacity
              testID="review-disclaimer-button"
              style={styles.reviewBtn}
              onPress={() => router.push({ pathname: "/disclaimer", params: { readonly: "1" } })}
            >
              <Ionicons name="document-text-outline" size={18} color={COLORS.brand} />
              <Text style={styles.reviewBtnText}>{t("reviewDisclaimer")}</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity testID="signout-button" style={styles.signOutBtn} onPress={doSignOut}>
            <Ionicons name="log-out-outline" size={22} color={COLORS.redStrong} />
            <Text style={styles.signOutText}>{t("signOut")}</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function LangButton({ label, active, onPress, testID }: { label: string; active: boolean; onPress: () => void; testID: string }) {
  return (
    <TouchableOpacity testID={testID} onPress={onPress} style={[styles.langBtn, active && styles.langBtnActive]}>
      <Text style={[styles.langBtnText, active && styles.langBtnTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  container: { padding: SIZE.m, gap: SIZE.m, paddingBottom: SIZE.xxl },
  title: { fontSize: FONT.h1, fontWeight: "800", color: COLORS.textPrimary },
  card: {
    backgroundColor: COLORS.bgSurface,
    borderRadius: SIZE.radiusLg,
    padding: SIZE.m,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: SIZE.s,
  },
  section: { fontSize: FONT.bodyL, fontWeight: "700", color: COLORS.textPrimary },
  userRow: { flexDirection: "row", gap: 14, alignItems: "center" },
  avatar: { width: 52, height: 52, borderRadius: 26, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center" },
  userName: { fontSize: FONT.h3, fontWeight: "700", color: COLORS.textPrimary },
  userEmail: { fontSize: FONT.body, color: COLORS.textSecondary },
  rowBetween: { flexDirection: "row", alignItems: "center", gap: SIZE.m },
  rowLabel: { fontSize: FONT.body, fontWeight: "700", color: COLORS.textPrimary },
  rowValue: { fontSize: FONT.body, color: COLORS.textSecondary, marginTop: 2 },
  rowSubtle: { fontSize: FONT.label, color: COLORS.textSecondary, lineHeight: 20 },
  stageRow: { flexDirection: "row", gap: SIZE.s },
  stageBtn: {
    flex: 1, height: 44, borderRadius: SIZE.radiusPill, borderWidth: 2, borderColor: COLORS.border,
    backgroundColor: COLORS.bgDefault, alignItems: "center", justifyContent: "center", paddingHorizontal: 6,
  },
  stageBtnActive: { borderColor: COLORS.brand, backgroundColor: COLORS.brandLight },
  stageBtnText: { color: COLORS.textSecondary, fontWeight: "700", fontSize: FONT.label },
  stageBtnTextActive: { color: COLORS.brand },
  field: { gap: 4 },
  fieldLabel: { fontSize: FONT.body, color: COLORS.textPrimary, fontWeight: "600" },
  input: {
    height: 48, borderRadius: SIZE.radiusMd, borderWidth: 2, borderColor: COLORS.border,
    backgroundColor: COLORS.bgDefault, paddingHorizontal: SIZE.m, fontSize: FONT.bodyL, color: COLORS.textPrimary,
  },
  defaultsPill: {
    alignSelf: "flex-start", fontSize: FONT.label, fontWeight: "700",
    color: COLORS.brand, backgroundColor: COLORS.brandLight,
    paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12,
  },
  primaryBtn: {
    flex: 1, height: SIZE.touchPrimary, borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center",
  },
  primaryText: { color: COLORS.textInverse, fontSize: FONT.bodyL, fontWeight: "700" },
  linkBtn: { height: SIZE.touchPrimary, paddingHorizontal: SIZE.m, alignItems: "center", justifyContent: "center" },
  linkText: { color: COLORS.textSecondary, fontWeight: "700", fontSize: FONT.body },
  langRow: { flexDirection: "row", gap: SIZE.s },
  langBtn: {
    flex: 1, height: SIZE.touchPrimary, borderRadius: SIZE.radiusMd, borderWidth: 2,
    borderColor: COLORS.border, alignItems: "center", justifyContent: "center", backgroundColor: COLORS.bgDefault,
  },
  langBtnActive: { borderColor: COLORS.brand, backgroundColor: COLORS.brandLight },
  langBtnText: { fontSize: FONT.bodyL, color: COLORS.textSecondary, fontWeight: "600" },
  langBtnTextActive: { color: COLORS.brand, fontWeight: "800" },
  disclaimer: { flex: 1, color: COLORS.textPrimary, fontSize: FONT.body, lineHeight: 22 },
  reviewBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 10, paddingHorizontal: SIZE.m, borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.bgSurface, borderWidth: 1, borderColor: COLORS.brand,
  },
  reviewBtnText: { color: COLORS.brand, fontWeight: "700", fontSize: FONT.body },
  signOutBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10,
    height: SIZE.touchPrimary, borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.redBg, borderWidth: 2, borderColor: COLORS.redBorder,
  },
  signOutText: { color: COLORS.redStrong, fontSize: FONT.bodyL, fontWeight: "700" },
});
