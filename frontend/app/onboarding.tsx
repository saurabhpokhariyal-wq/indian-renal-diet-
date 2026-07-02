import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useState } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import type { Stage } from "@/src/lib/api";
import { COLORS, FONT, SIZE } from "@/src/theme";

export default function Onboarding() {
  const { setStage } = useAuth();
  const { t } = useLang();
  const [selected, setSelected] = useState<Stage | null>(null);
  const [saving, setSaving] = useState(false);

  const commit = async (stage: Stage) => {
    setSaving(true);
    try {
      await setStage(stage);
      router.replace("/(app)");
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.logo}><Ionicons name="leaf" size={40} color={COLORS.textInverse} /></View>
        <Text style={styles.title}>{t("onboardingWelcome")}</Text>
        <Text style={styles.subtitle}>{t("onboardingIntro")}</Text>

        <TouchableOpacity
          testID="stage-pre-dialysis"
          style={[styles.card, selected === "pre_dialysis" && styles.cardActive]}
          activeOpacity={0.85}
          onPress={() => setSelected("pre_dialysis")}
        >
          <View style={styles.cardIcon}><Ionicons name="water" size={26} color={COLORS.brand} /></View>
          <View style={{ flex: 1 }}>
            <Text style={styles.cardTitle}>{t("stagePreDialysis")}</Text>
            <Text style={styles.cardDesc}>{t("stagePreDialysisDesc")}</Text>
          </View>
          {selected === "pre_dialysis" && <Ionicons name="checkmark-circle" size={26} color={COLORS.brand} />}
        </TouchableOpacity>

        <TouchableOpacity
          testID="stage-dialysis"
          style={[styles.card, selected === "dialysis" && styles.cardActive]}
          activeOpacity={0.85}
          onPress={() => setSelected("dialysis")}
        >
          <View style={styles.cardIcon}><Ionicons name="pulse" size={26} color={COLORS.brand} /></View>
          <View style={{ flex: 1 }}>
            <Text style={styles.cardTitle}>{t("stageDialysis")}</Text>
            <Text style={styles.cardDesc}>{t("stageDialysisDesc")}</Text>
          </View>
          {selected === "dialysis" && <Ionicons name="checkmark-circle" size={26} color={COLORS.brand} />}
        </TouchableOpacity>

        <TouchableOpacity
          testID="onboarding-continue"
          style={[styles.primaryBtn, (!selected || saving) && { opacity: 0.5 }]}
          onPress={() => selected && commit(selected)}
          disabled={!selected || saving}
        >
          <Text style={styles.primaryText}>{t("stageContinue")}</Text>
        </TouchableOpacity>

        <TouchableOpacity testID="onboarding-skip" style={styles.skipBtn} onPress={() => commit("pre_dialysis")}>
          <Text style={styles.skipText}>{t("stageSkip")}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  container: { padding: SIZE.l, gap: SIZE.m, paddingBottom: SIZE.xxl },
  logo: { width: 72, height: 72, borderRadius: 36, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center", alignSelf: "center", marginTop: SIZE.l },
  title: { fontSize: FONT.h1, fontWeight: "800", color: COLORS.textPrimary, textAlign: "center", marginTop: 12 },
  subtitle: { fontSize: FONT.bodyL, color: COLORS.textSecondary, textAlign: "center", lineHeight: 26, marginBottom: SIZE.m },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: SIZE.m,
    padding: SIZE.m,
    backgroundColor: COLORS.bgSurface,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderRadius: SIZE.radiusLg,
  },
  cardActive: { borderColor: COLORS.brand, backgroundColor: COLORS.brandLight },
  cardIcon: { width: 48, height: 48, borderRadius: 24, backgroundColor: COLORS.brandLight, alignItems: "center", justifyContent: "center" },
  cardTitle: { fontSize: FONT.h3, fontWeight: "700", color: COLORS.textPrimary },
  cardDesc: { fontSize: FONT.body, color: COLORS.textSecondary, marginTop: 4, lineHeight: 22 },
  primaryBtn: { height: SIZE.touchPrimary, borderRadius: SIZE.radiusPill, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center", marginTop: SIZE.m },
  primaryText: { color: COLORS.textInverse, fontSize: FONT.bodyL, fontWeight: "700" },
  skipBtn: { alignItems: "center", padding: SIZE.m },
  skipText: { color: COLORS.textSecondary, fontSize: FONT.body, fontWeight: "600" },
});
