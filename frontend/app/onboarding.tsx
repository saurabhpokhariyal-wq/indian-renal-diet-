import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import type { DoctorLimits, Stage } from "@/src/lib/api";
import { COLORS, FONT, SIZE } from "@/src/theme";

type Step = "stage" | "diabetic" | "limits";

const STEPS: Step[] = ["stage", "diabetic", "limits"];

export default function Onboarding() {
  const { setStage, updateProfile } = useAuth();
  const { t } = useLang();
  const [step, setStep] = useState<Step>("stage");
  const [stage, setStageValue] = useState<Stage | null>(null);
  const [diabetic, setDiabetic] = useState<boolean | null>(null);
  const [k, setK] = useState("");
  const [p, setP] = useState("");
  const [na, setNa] = useState("");
  const [saving, setSaving] = useState(false);

  const stepIdx = STEPS.indexOf(step);
  const goNext = () => setStep(STEPS[Math.min(stepIdx + 1, STEPS.length - 1)]);
  const goBack = () => setStep(STEPS[Math.max(stepIdx - 1, 0)]);

  const finish = async (withLimits: boolean) => {
    if (!stage || diabetic === null || saving) return;
    setSaving(true);
    try {
      await setStage(stage);
      const limits: DoctorLimits | null = withLimits
        ? {
            potassium_mg: k ? Number(k) : null,
            phosphorus_mg: p ? Number(p) : null,
            sodium_mg: na ? Number(na) : null,
          }
        : null;
      await updateProfile({ diabetic, doctor_limits: limits });
      router.replace("/");
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <View style={styles.progressRow}>
            {STEPS.map((s, i) => (
              <View key={s} style={[styles.progressDot, i <= stepIdx && styles.progressDotActive]} />
            ))}
          </View>
          <Text style={styles.stepLabel}>{t("stageStep")} {stepIdx + 1} / {STEPS.length}</Text>

          {step === "stage" ? (
            <>
              <View style={styles.logo}><Ionicons name="leaf" size={40} color={COLORS.textInverse} /></View>
              <Text style={styles.title}>{t("onboardingWelcome")}</Text>
              <Text style={styles.subtitle}>{t("onboardingIntro")}</Text>

              <TouchableOpacity
                testID="stage-pre-dialysis"
                style={[styles.card, stage === "pre_dialysis" && styles.cardActive]}
                onPress={() => setStageValue("pre_dialysis")}
              >
                <View style={styles.cardIcon}><Ionicons name="water" size={24} color={COLORS.brand} /></View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>{t("stagePreDialysis")}</Text>
                  <Text style={styles.cardDesc}>{t("stagePreDialysisDesc")}</Text>
                </View>
                {stage === "pre_dialysis" && <Ionicons name="checkmark-circle" size={24} color={COLORS.brand} />}
              </TouchableOpacity>

              <TouchableOpacity
                testID="stage-dialysis"
                style={[styles.card, stage === "dialysis" && styles.cardActive]}
                onPress={() => setStageValue("dialysis")}
              >
                <View style={styles.cardIcon}><Ionicons name="pulse" size={24} color={COLORS.brand} /></View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.cardTitle}>{t("stageDialysis")}</Text>
                  <Text style={styles.cardDesc}>{t("stageDialysisDesc")}</Text>
                </View>
                {stage === "dialysis" && <Ionicons name="checkmark-circle" size={24} color={COLORS.brand} />}
              </TouchableOpacity>

              <TouchableOpacity
                testID="onboarding-continue"
                style={[styles.primaryBtn, !stage && { opacity: 0.5 }]}
                disabled={!stage}
                onPress={goNext}
              >
                <Text style={styles.primaryText}>{t("stageContinue")}</Text>
              </TouchableOpacity>
            </>
          ) : null}

          {step === "diabetic" ? (
            <>
              <View style={styles.logo}><Ionicons name="water-outline" size={40} color={COLORS.textInverse} /></View>
              <Text style={styles.title}>{t("diabeticQuestion")}</Text>
              <Text style={styles.subtitle}>{t("diabeticSub")}</Text>

              <View style={styles.pillRow}>
                <TouchableOpacity
                  testID="diabetic-yes"
                  style={[styles.pillBtn, diabetic === true && styles.pillActive]}
                  onPress={() => setDiabetic(true)}
                >
                  <Text style={[styles.pillText, diabetic === true && styles.pillTextActive]}>{t("yes")}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  testID="diabetic-no"
                  style={[styles.pillBtn, diabetic === false && styles.pillActive]}
                  onPress={() => setDiabetic(false)}
                >
                  <Text style={[styles.pillText, diabetic === false && styles.pillTextActive]}>{t("no")}</Text>
                </TouchableOpacity>
              </View>

              <View style={styles.buttonRow}>
                <TouchableOpacity testID="onboarding-back" style={styles.secondaryBtn} onPress={goBack}>
                  <Ionicons name="chevron-back" size={20} color={COLORS.brand} />
                  <Text style={styles.secondaryText}>{t("stageBack")}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  testID="diabetic-continue"
                  style={[styles.primaryBtn, { flex: 1 }, diabetic === null && { opacity: 0.5 }]}
                  disabled={diabetic === null}
                  onPress={goNext}
                >
                  <Text style={styles.primaryText}>{t("stageContinue")}</Text>
                </TouchableOpacity>
              </View>
            </>
          ) : null}

          {step === "limits" ? (
            <>
              <View style={styles.logo}><Ionicons name="clipboard" size={40} color={COLORS.textInverse} /></View>
              <Text style={styles.title}>{t("doctorLimitsTitle")}</Text>
              <Text style={styles.subtitle}>{t("doctorLimitsSub")}</Text>

              <LimitInput testID="limit-potassium" label={`${t("nutrientPotassium")} (mg)`} value={k} onChange={setK} placeholder="e.g. 2000" />
              <LimitInput testID="limit-phosphorus" label={`${t("nutrientPhosphorus")} (mg)`} value={p} onChange={setP} placeholder="e.g. 1000" />
              <LimitInput testID="limit-sodium" label={`${t("nutrientSodium")} (mg)`} value={na} onChange={setNa} placeholder="e.g. 2000" />

              <View style={styles.buttonRow}>
                <TouchableOpacity testID="limits-back" style={styles.secondaryBtn} onPress={goBack}>
                  <Ionicons name="chevron-back" size={20} color={COLORS.brand} />
                  <Text style={styles.secondaryText}>{t("stageBack")}</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  testID="limits-save"
                  style={[styles.primaryBtn, { flex: 1 }, saving && { opacity: 0.6 }]}
                  disabled={saving}
                  onPress={() => finish(true)}
                >
                  <Text style={styles.primaryText}>{t("doctorLimitsSave")}</Text>
                </TouchableOpacity>
              </View>

              <TouchableOpacity testID="limits-skip" style={styles.skipBtn} onPress={() => finish(false)} disabled={saving}>
                <Text style={styles.skipText}>{t("stageSkip")}</Text>
              </TouchableOpacity>
            </>
          ) : null}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function LimitInput({ label, value, onChange, placeholder, testID }: {
  label: string; value: string; onChange: (v: string) => void; placeholder: string; testID: string;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        testID={testID}
        style={styles.input}
        value={value}
        onChangeText={(v) => onChange(v.replace(/[^0-9]/g, ""))}
        placeholder={placeholder}
        placeholderTextColor="#A8A29E"
        keyboardType="number-pad"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  container: { padding: SIZE.l, gap: SIZE.m, paddingBottom: SIZE.xxl },
  progressRow: { flexDirection: "row", gap: 6, alignSelf: "center", marginTop: 4 },
  progressDot: { width: 24, height: 6, borderRadius: 3, backgroundColor: COLORS.border },
  progressDotActive: { backgroundColor: COLORS.brand },
  stepLabel: { textAlign: "center", fontSize: FONT.label, color: COLORS.textSecondary, fontWeight: "600" },
  logo: { width: 72, height: 72, borderRadius: 36, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center", alignSelf: "center", marginTop: SIZE.m },
  title: { fontSize: FONT.h1, fontWeight: "800", color: COLORS.textPrimary, textAlign: "center", marginTop: 4 },
  subtitle: { fontSize: FONT.bodyL, color: COLORS.textSecondary, textAlign: "center", lineHeight: 26, marginBottom: SIZE.s },
  card: {
    flexDirection: "row", alignItems: "center", gap: SIZE.m, padding: SIZE.m,
    backgroundColor: COLORS.bgSurface, borderWidth: 2, borderColor: COLORS.border, borderRadius: SIZE.radiusLg,
  },
  cardActive: { borderColor: COLORS.brand, backgroundColor: COLORS.brandLight },
  cardIcon: { width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.brandLight, alignItems: "center", justifyContent: "center" },
  cardTitle: { fontSize: FONT.h3, fontWeight: "700", color: COLORS.textPrimary },
  cardDesc: { fontSize: FONT.body, color: COLORS.textSecondary, marginTop: 4, lineHeight: 22 },
  pillRow: { flexDirection: "row", gap: SIZE.s },
  pillBtn: {
    flex: 1, height: SIZE.touchPrimary, borderRadius: SIZE.radiusPill,
    alignItems: "center", justifyContent: "center", borderWidth: 2, borderColor: COLORS.border, backgroundColor: COLORS.bgSurface,
  },
  pillActive: { borderColor: COLORS.brand, backgroundColor: COLORS.brandLight },
  pillText: { fontSize: FONT.bodyL, color: COLORS.textSecondary, fontWeight: "700" },
  pillTextActive: { color: COLORS.brand },
  field: { gap: 4 },
  fieldLabel: { fontSize: FONT.body, color: COLORS.textPrimary, fontWeight: "600" },
  input: {
    height: SIZE.touchPrimary, borderRadius: SIZE.radiusMd, borderWidth: 2,
    borderColor: COLORS.border, backgroundColor: COLORS.bgSurface,
    paddingHorizontal: SIZE.m, fontSize: FONT.bodyL, color: COLORS.textPrimary,
  },
  primaryBtn: {
    height: SIZE.touchPrimary, borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center", marginTop: SIZE.m,
    paddingHorizontal: SIZE.l,
  },
  primaryText: { color: COLORS.textInverse, fontSize: FONT.bodyL, fontWeight: "700" },
  secondaryBtn: {
    marginTop: SIZE.m, flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: SIZE.m,
    height: SIZE.touchPrimary, borderRadius: SIZE.radiusPill,
    borderWidth: 2, borderColor: COLORS.brand, backgroundColor: COLORS.bgSurface,
  },
  secondaryText: { color: COLORS.brand, fontWeight: "700", fontSize: FONT.body },
  buttonRow: { flexDirection: "row", gap: SIZE.s },
  skipBtn: { alignItems: "center", padding: SIZE.m },
  skipText: { color: COLORS.textSecondary, fontSize: FONT.body, fontWeight: "600" },
});
