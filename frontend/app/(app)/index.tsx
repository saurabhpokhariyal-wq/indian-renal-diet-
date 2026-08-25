import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { NutrientBar } from "@/src/components/NutrientBar";
import { api, type MealLogSummary } from "@/src/lib/api";
import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import { mgToUserUnit } from "@/src/lib/units";
import { COLORS, FONT, SIZE } from "@/src/theme";

/**
 * Home is deliberately dominated by ONE action — "Check a food" — instead of a
 * 12-card menu grid that made new patients choose between "twelve things I
 * don't know" on first launch (see iter-26 nav consolidation prompt).
 *
 * Layout (top-down):
 *   1. Greeting header
 *   2. Big hero card: "Check a food" → /search (Type mode is the default)
 *   3. Today's Budget bars (K / P / Na / Fluid), fetched from
 *      /api/meal-logs/summary — same limits/totals the Meals tab uses.
 *   4. Small secondary "More" section: Weekly Report + Settings (Meals, Scan,
 *      Ask AI already live in the bottom tab bar).
 *
 * The six standalone guide screens (fruits/vegetables/grains/snacks/proteins/
 * beverages) plus the recently-added oils guide were deleted in this pass —
 * they were the same underlying question ("is this food safe") sliced six ways.
 * Category filter chips now live inside /search alongside the tier chips.
 */

function isoToday(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export default function HomeScreen() {
  const { user } = useAuth();
  const { t } = useLang();
  const unit = user?.nutrient_unit ?? "mg";
  const [summary, setSummary] = useState<MealLogSummary | null>(null);

  const loadSummary = useCallback(async () => {
    try {
      const s = await api.getMealSummary(isoToday());
      setSummary(s);
    } catch {
      // offline / not-yet-logged-in — hero still works without the bars
      setSummary(null);
    }
  }, []);

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  const kMg = summary?.totals.potassium_mg ?? 0;
  const kLimMg = summary?.limits.potassium_mg ?? 2000;
  const naMg = summary?.totals.sodium_mg ?? 0;
  const naLimMg = summary?.limits.sodium_mg ?? 2000;
  const kVal = mgToUserUnit("K", kMg, unit);
  const kLim = mgToUserUnit("K", kLimMg, unit);
  const naVal = mgToUserUnit("Na", naMg, unit);
  const naLim = mgToUserUnit("Na", naLimMg, unit);
  const dec = unit === "mEq" ? 1 : 0;

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        {/* Greeting */}
        <View style={styles.greetRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.greetHi}>{t("greeting")},</Text>
            <Text testID="user-greeting" style={styles.greetName} numberOfLines={1}>
              {user?.full_name || user?.email?.split("@")[0] || "Friend"}
            </Text>
          </View>
          <View style={styles.logo}>
            <Ionicons name="leaf" size={22} color={COLORS.textInverse} />
          </View>
        </View>

        {/* HERO — the single dominant action on Home */}
        <TouchableOpacity
          testID="home-check-food"
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel={t("heroCheckFood")}
          style={styles.hero}
          onPress={() => router.push("/(app)/search")}
        >
          <View style={styles.heroIconBubble}>
            <Ionicons name="search" size={38} color={COLORS.textInverse} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.heroTitle}>{t("heroCheckFood")}</Text>
            <Text style={styles.heroSubtitle}>{t("heroCheckFoodSub")}</Text>
            <View style={styles.heroMethodsRow}>
              <View style={styles.heroMethodChip}>
                <Ionicons name="search" size={13} color={COLORS.textInverse} />
                <Text style={styles.heroMethodText}>{t("checkModeType")}</Text>
              </View>
              <View style={styles.heroMethodChip}>
                <Ionicons name="camera" size={13} color={COLORS.textInverse} />
                <Text style={styles.heroMethodText}>{t("checkModePhoto")}</Text>
              </View>
              <View style={styles.heroMethodChip}>
                <Ionicons name="mic" size={13} color={COLORS.textInverse} />
                <Text style={styles.heroMethodText}>{t("checkModeVoice")}</Text>
              </View>
            </View>
          </View>
        </TouchableOpacity>

        {/* TODAY'S BUDGET — secondary, at-a-glance */}
        <View style={styles.budgetCard} testID="home-todays-budget">
          <View style={styles.budgetHeader}>
            <Ionicons name="stats-chart" size={18} color={COLORS.brand} />
            <Text style={styles.budgetTitle}>{t("todaysBudget")}</Text>
          </View>
          <NutrientBar
            testID="home-budget-potassium"
            label={t("nutrientPotassium")}
            value={kVal}
            limit={kLim}
            unit={unit}
            decimals={dec}
          />
          <NutrientBar
            testID="home-budget-phosphorus"
            label={t("nutrientPhosphorus")}
            value={summary?.totals.phosphorus_mg ?? 0}
            limit={summary?.limits.phosphorus_mg ?? 1000}
          />
          <NutrientBar
            testID="home-budget-sodium"
            label={t("nutrientSodium")}
            value={naVal}
            limit={naLim}
            unit={unit}
            decimals={dec}
          />
          <NutrientBar
            testID="home-budget-fluid"
            label={t("nutrientFluid")}
            value={summary?.totals.fluid_ml ?? 0}
            limit={summary?.limits.fluid_ml ?? 2000}
            unit="ml"
          />
        </View>

        {/* MORE — small, below-the-fold. Tab bar already covers Meals/Scan/AI. */}
        <Text style={styles.moreTitle}>{t("homeMore")}</Text>
        <View style={styles.moreRow}>
          <TouchableOpacity
            testID="home-more-report"
            style={styles.moreCard}
            onPress={() => router.push("/report")}
            accessibilityRole="button"
            accessibilityLabel={t("menuReport")}
          >
            <View style={[styles.moreIconBubble, { backgroundColor: COLORS.redBg }]}>
              <Ionicons name="document-text" size={22} color={COLORS.redStrong} />
            </View>
            <Text style={styles.moreCardTitle}>{t("menuReport")}</Text>
            <Text style={styles.moreCardSub}>{t("menuReportSub")}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            testID="home-more-settings"
            style={styles.moreCard}
            onPress={() => router.push("/(app)/settings")}
            accessibilityRole="button"
            accessibilityLabel={t("tabSettings")}
          >
            <View style={[styles.moreIconBubble, { backgroundColor: COLORS.bgAlt }]}>
              <Ionicons name="settings" size={22} color={COLORS.textSecondary} />
            </View>
            <Text style={styles.moreCardTitle}>{t("tabSettings")}</Text>
            <Text style={styles.moreCardSub}>{t("menuSettingsSub")}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  container: { padding: SIZE.m, paddingBottom: SIZE.xxl, gap: SIZE.m },
  greetRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  greetHi: { fontSize: FONT.body, color: COLORS.textSecondary },
  greetName: { fontSize: FONT.h2, fontWeight: "800", color: COLORS.textPrimary },
  logo: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.brand,
    alignItems: "center",
    justifyContent: "center",
  },

  hero: {
    flexDirection: "row",
    alignItems: "center",
    gap: SIZE.m,
    padding: SIZE.l,
    minHeight: 148,
    backgroundColor: COLORS.brand,
    borderRadius: SIZE.radiusLg,
    // Elevate visually so it dominates the fold.
    shadowColor: "#000",
    shadowOpacity: 0.12,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  heroIconBubble: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: "rgba(255,255,255,0.18)",
    alignItems: "center",
    justifyContent: "center",
  },
  heroTitle: {
    fontSize: FONT.h2,
    fontWeight: "800",
    color: COLORS.textInverse,
  },
  heroSubtitle: {
    fontSize: FONT.body,
    color: COLORS.textInverse,
    opacity: 0.9,
    marginTop: 2,
    lineHeight: 20,
  },
  heroMethodsRow: {
    flexDirection: "row",
    gap: 6,
    marginTop: 10,
    flexWrap: "wrap",
  },
  heroMethodChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: SIZE.radiusPill,
    backgroundColor: "rgba(255,255,255,0.18)",
  },
  heroMethodText: {
    color: COLORS.textInverse,
    fontSize: FONT.label,
    fontWeight: "700",
  },

  budgetCard: {
    backgroundColor: COLORS.bgSurface,
    borderRadius: SIZE.radiusLg,
    padding: SIZE.m,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: SIZE.s,
  },
  budgetHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 4,
  },
  budgetTitle: {
    fontSize: FONT.bodyL,
    fontWeight: "800",
    color: COLORS.textPrimary,
  },

  moreTitle: {
    fontSize: FONT.body,
    fontWeight: "700",
    color: COLORS.textSecondary,
    marginTop: SIZE.s,
  },
  moreRow: {
    flexDirection: "row",
    gap: SIZE.m,
  },
  moreCard: {
    flex: 1,
    padding: SIZE.m,
    minHeight: 118,
    backgroundColor: COLORS.bgSurface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: SIZE.radiusLg,
    gap: 6,
  },
  moreIconBubble: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
  },
  moreCardTitle: { fontSize: FONT.body, fontWeight: "800", color: COLORS.textPrimary },
  moreCardSub: { fontSize: FONT.label, color: COLORS.textSecondary, lineHeight: 18 },
});
