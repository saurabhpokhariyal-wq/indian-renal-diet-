import { Ionicons } from "@expo/vector-icons";
import { router, useFocusEffect } from "expo-router";
import { useCallback, useMemo, useState } from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SafetyBadge } from "@/src/components/SafetyBadge";
import { api, type MealLogOut } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

function today(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export default function MealLogScreen() {
  const { t, lang } = useLang();
  const date = today();
  const [logs, setLogs] = useState<MealLogOut[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await api.listMealLogs(date);
      setLogs(list);
    } catch {
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [date]);

  useFocusEffect(useCallback(() => {
    void load();
  }, [load]));

  const summary = useMemo(() => {
    const s = { GREEN: 0, YELLOW: 0, RED: 0 };
    for (const l of logs) s[l.food.safety_tier] += 1;
    return s;
  }, [logs]);

  const onRemove = async (id: string) => {
    try {
      await api.deleteMealLog(id);
      setLogs((prev) => prev.filter((l) => l.id !== id));
    } catch {
      // no-op
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <View style={styles.header}>
        <Text style={styles.title}>{t("mealLog")}</Text>
        <Text style={styles.date}>{new Date().toDateString()}</Text>

        <View style={styles.summaryRow}>
          <SummaryPill label={t("summarySafe")} count={summary.GREEN} tier="GREEN" />
          <SummaryPill label={t("summaryCaution")} count={summary.YELLOW} tier="YELLOW" />
          <SummaryPill label={t("summaryAvoid")} count={summary.RED} tier="RED" />
        </View>
      </View>

      {loading ? (
        <View style={styles.centerBox}><ActivityIndicator size="large" color={COLORS.brand} /></View>
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

function SummaryPill({ label, count, tier }: { label: string; count: number; tier: "GREEN" | "YELLOW" | "RED" }) {
  const meta = TIER_META[tier];
  return (
    <View style={[styles.sumPill, { backgroundColor: meta.bg, borderColor: meta.border }]}>
      <Text style={[styles.sumCount, { color: meta.text }]}>{count}</Text>
      <Text style={[styles.sumLabel, { color: meta.text }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  header: { padding: SIZE.m, gap: 6 },
  title: { fontSize: FONT.h1, fontWeight: "800", color: COLORS.textPrimary },
  date: { fontSize: FONT.body, color: COLORS.textSecondary, marginBottom: SIZE.s },
  summaryRow: { flexDirection: "row", gap: SIZE.s },
  sumPill: { flex: 1, alignItems: "center", padding: 12, borderWidth: 2, borderRadius: SIZE.radiusMd },
  sumCount: { fontSize: 28, fontWeight: "800" },
  sumLabel: { fontSize: FONT.label, fontWeight: "700", marginTop: 2 },
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
  centerBox: { flex: 1, alignItems: "center", justifyContent: "center" },
});
