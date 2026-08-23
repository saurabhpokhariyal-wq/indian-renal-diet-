import { Ionicons } from "@expo/vector-icons";
import { router, useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { NutrientBar } from "@/src/components/NutrientBar";
import { SafetyBadge } from "@/src/components/SafetyBadge";
import { api, type MealLogOut, type MealLogSummary } from "@/src/lib/api";
import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import { mgToUserUnit } from "@/src/lib/units";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

function isoDate(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function shiftDate(iso: string, days: number): string {
  const [y, m, dd] = iso.split("-").map(Number);
  const d = new Date(y, m - 1, dd);
  d.setDate(d.getDate() + days);
  return isoDate(d);
}

function prettyDate(iso: string, todayIso: string, todayLabel: string): string {
  if (iso === todayIso) return todayLabel;
  const [y, m, dd] = iso.split("-").map(Number);
  return new Date(y, m - 1, dd).toDateString();
}

export default function MealLogScreen() {
  const { t, lang } = useLang();
  const { user } = useAuth();
  const unit = user?.nutrient_unit ?? "mg";
  const todayIso = isoDate(new Date());
  const [date, setDate] = useState(todayIso);
  const [logs, setLogs] = useState<MealLogOut[]>([]);
  const [summary, setSummary] = useState<MealLogSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [list, sum] = await Promise.all([
        api.listMealLogs(date),
        api.getMealSummary(date),
      ]);
      setLogs(list);
      setSummary(sum);
    } catch (e) {
      setLogs([]);
      setSummary(null);
      setError(e instanceof Error ? e.message : "Could not load logs");
    } finally {
      setLoading(false);
    }
  }, [date]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  const onRemove = async (id: string) => {
    try {
      await api.deleteMealLog(id);
      void load();
    } catch {
      void load();
    }
  };

  const canGoNext = date !== todayIso;

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.title}>{t("mealLog")}</Text>
          </View>
          <TouchableOpacity testID="open-report" onPress={() => router.push("/report")} style={styles.reportBtn}>
            <Ionicons name="document-text" size={18} color={COLORS.brand} />
            <Text style={styles.reportBtnText}>{t("weeklyReport")}</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          testID="open-log-by-text"
          style={styles.logByTextBtn}
          onPress={() => router.push({ pathname: "/log-meal-nl", params: { date, meal_type: "meal" } })}
        >
          <Ionicons name="sparkles" size={18} color={COLORS.textInverse} />
          <Text style={styles.logByTextText}>{t("logByText")}</Text>
        </TouchableOpacity>

        <View style={styles.dateNav}>
          <TouchableOpacity
            testID="prev-day"
            style={styles.arrowBtn}
            onPress={() => setDate((d) => shiftDate(d, -1))}
            accessibilityLabel={t("prevDay")}
          >
            <Ionicons name="chevron-back" size={22} color={COLORS.brand} />
          </TouchableOpacity>
          <View style={styles.dateBox}>
            <Text testID="meal-log-date" style={styles.dateText}>
              {prettyDate(date, todayIso, t("today"))}
            </Text>
            <Text style={styles.dateSub}>{date}</Text>
          </View>
          <TouchableOpacity
            testID="next-day"
            style={[styles.arrowBtn, !canGoNext && styles.arrowDisabled]}
            onPress={() => canGoNext && setDate((d) => shiftDate(d, 1))}
            disabled={!canGoNext}
            accessibilityLabel={t("nextDay")}
          >
            <Ionicons name="chevron-forward" size={22} color={canGoNext ? COLORS.brand : COLORS.border} />
          </TouchableOpacity>
        </View>

        <View style={styles.budgetCard}>
          <View style={styles.budgetHeader}>
            <Ionicons name="stats-chart" size={18} color={COLORS.brand} />
            <Text style={styles.budgetTitle}>{t("todaysBudget")}</Text>
          </View>
          <NutrientBar
            testID="budget-potassium"
            label={t("nutrientPotassium")}
            value={mgToUserUnit("K", summary?.totals.potassium_mg ?? 0, unit)}
            limit={mgToUserUnit("K", summary?.limits.potassium_mg ?? 2000, unit)}
            unit={unit}
            decimals={unit === "mEq" ? 1 : 0}
          />
          <NutrientBar
            testID="budget-phosphorus"
            label={t("nutrientPhosphorus")}
            value={summary?.totals.phosphorus_mg ?? 0}
            limit={summary?.limits.phosphorus_mg ?? 1000}
          />
          <NutrientBar
            testID="budget-sodium"
            label={t("nutrientSodium")}
            value={mgToUserUnit("Na", summary?.totals.sodium_mg ?? 0, unit)}
            limit={mgToUserUnit("Na", summary?.limits.sodium_mg ?? 2000, unit)}
            unit={unit}
            decimals={unit === "mEq" ? 1 : 0}
          />
          <NutrientBar
            testID="budget-fluid"
            label={t("nutrientFluid")}
            value={summary?.totals.fluid_ml ?? 0}
            limit={summary?.limits.fluid_ml ?? 2000}
            unit="ml"
          />
        </View>
      </View>

      {loading ? (
        <View style={styles.centerBox}><ActivityIndicator size="large" color={COLORS.brand} /></View>
      ) : error ? (
        <View testID="meal-log-error" style={styles.centerBox}>
          <Ionicons name="cloud-offline-outline" size={40} color={COLORS.redStrong} />
          <Text style={styles.errorTitle}>{t("somethingWrong")}</Text>
          <Text style={styles.errorBody}>{t("couldNotLoad")}</Text>
          <TouchableOpacity testID="meal-log-retry" style={styles.retryBtn} onPress={load}>
            <Ionicons name="refresh" size={18} color={COLORS.textInverse} />
            <Text style={styles.retryText}>{t("retry")}</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          testID="meal-log-list"
          data={logs}
          keyExtractor={(l) => l.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => {
            const meta = TIER_META[item.food.safety_tier];
            return (
              <View testID={`meal-log-${item.id}`} style={[styles.row, { borderColor: meta.border }]}>
                <TouchableOpacity style={{ flex: 1 }} activeOpacity={0.8} onPress={() => router.push(`/food/${item.food_id}`)}>
                  <Text style={styles.foodName} numberOfLines={1}>{item.food.name}</Text>
                  <Text style={styles.foodHindi} numberOfLines={1}>{item.food.hindi_name}</Text>
                  <View style={{ marginTop: 6 }}>
                    <SafetyBadge tier={item.food.safety_tier} labelOverride={lang === "hi" ? meta.labelHi : meta.label} compact />
                  </View>
                </TouchableOpacity>
                <TouchableOpacity testID={`remove-log-${item.id}`} onPress={() => onRemove(item.id)} hitSlop={12} style={styles.removeBtn}>
                  <Ionicons name="trash-outline" size={22} color={COLORS.redStrong} />
                </TouchableOpacity>
              </View>
            );
          }}
          ListEmptyComponent={
            <View style={styles.emptyBox}>
              <Ionicons name="restaurant-outline" size={40} color={COLORS.textSecondary} />
              <Text style={styles.emptyText}>{t("emptyMeals")}</Text>
              <TouchableOpacity testID="empty-goto-search" style={styles.ctaBtn} onPress={() => router.push("/(app)")}>
                <Text style={styles.ctaText}>{t("tabSearch")}</Text>
              </TouchableOpacity>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  header: { padding: SIZE.m, gap: SIZE.s },
  headerRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 12 },
  reportBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brandLight,
    borderWidth: 1,
    borderColor: COLORS.brand,
  },
  reportBtnText: { color: COLORS.brand, fontWeight: "700", fontSize: FONT.label },
  logByTextBtn: {
    marginTop: SIZE.s,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 12,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand,
  },
  logByTextText: { color: COLORS.textInverse, fontWeight: "700", fontSize: FONT.body },
  title: { fontSize: FONT.h1, fontWeight: "800", color: COLORS.textPrimary },
  dateNav: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.bgSurface,
    borderRadius: SIZE.radiusPill,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 6,
  },
  arrowBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: COLORS.brandLight,
  },
  arrowDisabled: { backgroundColor: COLORS.bgAlt },
  dateBox: { flex: 1, alignItems: "center" },
  dateText: { fontSize: FONT.bodyL, fontWeight: "800", color: COLORS.textPrimary },
  dateSub: { fontSize: 12, color: COLORS.textSecondary, marginTop: 2 },
  budgetCard: {
    marginTop: 4,
    padding: SIZE.m,
    backgroundColor: COLORS.bgSurface,
    borderRadius: SIZE.radiusLg,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: 12,
  },
  budgetHeader: { flexDirection: "row", alignItems: "center", gap: 6 },
  budgetTitle: { fontSize: FONT.bodyL, fontWeight: "800", color: COLORS.textPrimary },
  list: { padding: SIZE.m, paddingBottom: SIZE.xxl, gap: SIZE.s },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: SIZE.m,
    backgroundColor: COLORS.bgSurface,
    borderWidth: 2,
    borderRadius: SIZE.radiusLg,
    padding: SIZE.m,
    marginBottom: SIZE.s,
  },
  foodName: { fontSize: FONT.bodyL, fontWeight: "700", color: COLORS.textPrimary },
  foodHindi: { fontSize: FONT.body, color: COLORS.textSecondary },
  removeBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  emptyBox: { alignItems: "center", padding: SIZE.xl, gap: SIZE.m },
  emptyText: { fontSize: FONT.body, color: COLORS.textSecondary, textAlign: "center", lineHeight: 24 },
  ctaBtn: { paddingHorizontal: SIZE.l, paddingVertical: 12, borderRadius: SIZE.radiusPill, backgroundColor: COLORS.brand },
  ctaText: { color: COLORS.textInverse, fontWeight: "700" },
  centerBox: { flex: 1, alignItems: "center", justifyContent: "center", padding: SIZE.l, gap: SIZE.s },
  errorTitle: { fontSize: FONT.h3, fontWeight: "800", color: COLORS.textPrimary },
  errorBody: { fontSize: FONT.body, color: COLORS.textSecondary, textAlign: "center", lineHeight: 22 },
  retryBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: SIZE.l,
    paddingVertical: 10,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand,
    marginTop: SIZE.s,
  },
  retryText: { color: COLORS.textInverse, fontWeight: "700", fontSize: FONT.body },
});
