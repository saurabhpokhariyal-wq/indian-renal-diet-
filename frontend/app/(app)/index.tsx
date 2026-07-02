import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ActivityIndicator, FlatList, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SafetyCard } from "@/src/components/SafetyCard";
import { api, type FoodOut } from "@/src/lib/api";
import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE } from "@/src/theme";

const QUICK_CHIPS: { label: string; query: string }[] = [
  { label: "Palak Paneer", query: "palak" },
  { label: "Besan Chilla", query: "besan" },
  { label: "Lauki", query: "lauki" },
  { label: "Rajma", query: "rajma" },
  { label: "Apple", query: "apple" },
  { label: "Roti", query: "roti" },
];

export default function SearchScreen() {
  const { user } = useAuth();
  const { t } = useLang();
  const [query, setQuery] = useState("");
  const [foods, setFoods] = useState<FoodOut[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (q: string) => {
    setLoading(true);
    try {
      const list = await api.listFoods(q || undefined);
      setFoods(list);
    } catch {
      setFoods([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load("");
  }, [load]);

  useEffect(() => {
    const handle = setTimeout(() => void load(query), 250);
    return () => clearTimeout(handle);
  }, [query, load]);

  const header = useMemo(
    () => (
      <View style={styles.header}>
        <View style={styles.greetRow}>
          <View>
            <Text style={styles.greetHi}>{t("greeting")},</Text>
            <Text testID="user-greeting" style={styles.greetName} numberOfLines={1}>
              {user?.full_name || user?.email?.split("@")[0] || "Friend"}
            </Text>
          </View>
          <View style={styles.logo}>
            <Ionicons name="leaf" size={22} color={COLORS.textInverse} />
          </View>
        </View>

        <View style={styles.searchBar}>
          <Ionicons name="search" size={22} color={COLORS.textSecondary} />
          <TextInput
            testID="search-input"
            style={styles.searchInput}
            value={query}
            onChangeText={setQuery}
            placeholder={t("searchPlaceholder")}
            placeholderTextColor="#A8A29E"
            returnKeyType="search"
            autoCorrect={false}
          />
          {query.length > 0 ? (
            <TouchableOpacity testID="search-clear" onPress={() => setQuery("")} hitSlop={12}>
              <Ionicons name="close-circle" size={22} color={COLORS.textSecondary} />
            </TouchableOpacity>
          ) : null}
        </View>

        <View style={styles.chipsRow}>
          {QUICK_CHIPS.map((c) => (
            <TouchableOpacity
              key={c.query}
              testID={`chip-${c.query}`}
              onPress={() => setQuery(c.query)}
              style={styles.chip}
            >
              <Text style={styles.chipText}>{c.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.legendRow}>
          {[
            { tier: "GREEN", label: t("summarySafe"), color: COLORS.greenStrong },
            { tier: "YELLOW", label: t("summaryCaution"), color: COLORS.yellowStrong },
            { tier: "RED", label: t("summaryAvoid"), color: COLORS.redStrong },
          ].map((it) => (
            <View key={it.tier} style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: it.color }]} />
              <Text style={styles.legendText}>{it.label}</Text>
            </View>
          ))}
        </View>
      </View>
    ),
    [user, t, query],
  );

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <FlatList
        testID="food-list"
        data={foods}
        keyExtractor={(f) => f.id}
        ListHeaderComponent={header}
        contentContainerStyle={styles.list}
        keyboardShouldPersistTaps="handled"
        renderItem={({ item }) => (
          <View style={{ marginBottom: SIZE.m }}>
            <SafetyCard food={item} onPress={() => router.push(`/food/${item.id}`)} />
          </View>
        )}
        ListEmptyComponent={
          loading ? (
            <View style={styles.emptyBox}>
              <ActivityIndicator size="large" color={COLORS.brand} />
            </View>
          ) : (
            <View style={styles.emptyBox}>
              <Ionicons name="search" size={36} color={COLORS.textSecondary} />
              <Text style={styles.emptyText}>{t("noResults")}</Text>
            </View>
          )
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  list: { padding: SIZE.m, paddingBottom: SIZE.xxl },
  header: { gap: SIZE.m, marginBottom: SIZE.m },
  greetRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  greetHi: { fontSize: FONT.body, color: COLORS.textSecondary },
  greetName: { fontSize: FONT.h2, fontWeight: "800", color: COLORS.textPrimary, maxWidth: 260 },
  logo: { width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center" },
  searchBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    height: SIZE.touchPrimary,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.bgSurface,
    borderWidth: 2,
    borderColor: COLORS.border,
    paddingHorizontal: SIZE.m,
  },
  searchInput: { flex: 1, fontSize: FONT.bodyL, color: COLORS.textPrimary, height: "100%" },
  chipsRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: COLORS.brandLight, borderWidth: 1, borderColor: COLORS.brand },
  chipText: { color: COLORS.brand, fontSize: FONT.label, fontWeight: "700" },
  legendRow: { flexDirection: "row", gap: SIZE.m, marginTop: 4 },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 6 },
  legendDot: { width: 12, height: 12, borderRadius: 6 },
  legendText: { fontSize: FONT.label, color: COLORS.textSecondary, fontWeight: "600" },
  emptyBox: { alignItems: "center", padding: SIZE.xl, gap: SIZE.s },
  emptyText: { fontSize: FONT.body, color: COLORS.textSecondary, textAlign: "center" },
});
