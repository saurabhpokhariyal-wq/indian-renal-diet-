import { Ionicons } from "@expo/vector-icons";
import { router, useFocusEffect } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ActivityIndicator, FlatList, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SafetyCard } from "@/src/components/SafetyCard";
import { api, type FoodOut, type SafetyTier } from "@/src/lib/api";
import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

const QUICK_CHIPS: { label: string; query: string }[] = [
  { label: "Palak Paneer", query: "palak" },
  { label: "Besan Chilla", query: "besan" },
  { label: "Lauki", query: "lauki" },
  { label: "Rajma", query: "rajma" },
  { label: "Apple", query: "apple" },
  { label: "Roti", query: "roti" },
];

const TIER_FILTERS: { tier: SafetyTier; color: string; textKey: "summarySafe" | "summaryCaution" | "summaryAvoid" }[] = [
  { tier: "GREEN", color: COLORS.greenStrong, textKey: "summarySafe" },
  { tier: "YELLOW", color: COLORS.yellowStrong, textKey: "summaryCaution" },
  { tier: "RED", color: COLORS.redStrong, textKey: "summaryAvoid" },
];

export default function SearchScreen() {
  const { user } = useAuth();
  const { t } = useLang();
  const [query, setQuery] = useState("");
  const [selectedTiers, setSelectedTiers] = useState<Set<SafetyTier>>(new Set());
  const [foods, setFoods] = useState<FoodOut[]>([]);
  const [favorites, setFavorites] = useState<FoodOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (q: string, tiers: Set<SafetyTier>) => {
    setLoading(true);
    setError(null);
    try {
      const tierParam = tiers.size ? Array.from(tiers).join(",") : undefined;
      const list = await api.listFoods(q || undefined, tierParam);
      setFoods(list);
    } catch (e) {
      setFoods([]);
      setError(e instanceof Error ? e.message : "Could not load foods");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadFavorites = useCallback(async () => {
    try {
      const list = await api.listFoods(undefined, undefined, true);
      setFavorites(list);
    } catch {
      // favorites are best-effort; a failure here shouldn't block the screen
      setFavorites([]);
    }
  }, []);

  useFocusEffect(useCallback(() => {
    void loadFavorites();
  }, [loadFavorites]));

  useEffect(() => {
    const handle = setTimeout(() => void load(query, selectedTiers), 250);
    return () => clearTimeout(handle);
  }, [query, selectedTiers, load]);

  const toggleTier = (tier: SafetyTier) => {
    setSelectedTiers((prev) => {
      const next = new Set(prev);
      if (next.has(tier)) next.delete(tier);
      else next.add(tier);
      return next;
    });
  };

  const quickLog = async (food: FoodOut) => {
    try {
      const today = new Date();
      const pad = (n: number) => String(n).padStart(2, "0");
      const date = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
      await api.addMealLog(food.id, date);
    } catch {
      // ignore — background quick action
    }
  };

  const retry = () => void load(query, selectedTiers);

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

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.tierRow}
        >
          {TIER_FILTERS.map((f) => {
            const active = selectedTiers.has(f.tier);
            return (
              <TouchableOpacity
                key={f.tier}
                testID={`tier-filter-${f.tier.toLowerCase()}`}
                onPress={() => toggleTier(f.tier)}
                style={[
                  styles.tierChip,
                  { borderColor: f.color },
                  active && { backgroundColor: f.color },
                ]}
              >
                <View style={[styles.tierDot, { backgroundColor: active ? COLORS.textInverse : f.color }]} />
                <Text
                  style={[
                    styles.tierChipText,
                    { color: active ? COLORS.textInverse : f.color },
                  ]}
                >
                  {t(f.textKey)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

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

        {favorites.length > 0 && !query && selectedTiers.size === 0 ? (
          <View style={styles.favBlock}>
            <View style={styles.favHeader}>
              <Ionicons name="star" size={18} color={COLORS.yellowStrong} />
              <Text style={styles.favTitle}>{t("favoritesTitle")}</Text>
            </View>
            <FlatList
              data={favorites}
              horizontal
              keyExtractor={(f) => f.id}
              contentContainerStyle={{ gap: SIZE.s }}
              showsHorizontalScrollIndicator={false}
              renderItem={({ item }) => {
                const dt = (item.personal_tier || item.safety_tier) as keyof typeof TIER_META;
                const meta = TIER_META[dt];
                return (
                  <View testID={`fav-item-${item.id}`} style={[styles.favCard, { borderColor: meta.border }]}>
                    <TouchableOpacity style={{ flex: 1 }} onPress={() => router.push(`/food/${item.id}`)}>
                      <View style={[styles.favDot, { backgroundColor: meta.strong }]} />
                      <Text style={styles.favName} numberOfLines={1}>{item.name}</Text>
                      <Text style={styles.favHindi} numberOfLines={1}>{item.hindi_name}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      testID={`fav-log-${item.id}`}
                      style={styles.favLogBtn}
                      onPress={() => quickLog(item)}
                    >
                      <Ionicons name="add" size={16} color={COLORS.textInverse} />
                      <Text style={styles.favLogText}>{t("quickLog")}</Text>
                    </TouchableOpacity>
                  </View>
                );
              }}
            />
          </View>
        ) : null}
      </View>
    ),
    [user, t, query, favorites, selectedTiers],
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
          ) : error ? (
            <View testID="search-error" style={styles.emptyBox}>
              <Ionicons name="cloud-offline-outline" size={40} color={COLORS.redStrong} />
              <Text style={styles.errorTitle}>{t("somethingWrong")}</Text>
              <Text style={styles.errorBody}>{t("couldNotLoad")}</Text>
              <TouchableOpacity testID="search-retry" style={styles.retryBtn} onPress={retry}>
                <Ionicons name="refresh" size={18} color={COLORS.textInverse} />
                <Text style={styles.retryText}>{t("retry")}</Text>
              </TouchableOpacity>
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
  tierRow: { gap: SIZE.s, paddingRight: SIZE.m },
  tierChip: {
    flexShrink: 0,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 14,
    height: 36,
    borderRadius: 18,
    borderWidth: 2,
    backgroundColor: COLORS.bgSurface,
  },
  tierDot: { width: 10, height: 10, borderRadius: 5 },
  tierChipText: { fontSize: FONT.label, fontWeight: "700" },
  emptyBox: { alignItems: "center", padding: SIZE.xl, gap: SIZE.s },
  emptyText: { fontSize: FONT.body, color: COLORS.textSecondary, textAlign: "center" },
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
  favBlock: { gap: 10, marginTop: 4 },
  favHeader: { flexDirection: "row", alignItems: "center", gap: 6 },
  favTitle: { fontSize: FONT.bodyL, fontWeight: "800", color: COLORS.textPrimary },
  favCard: {
    width: 170,
    padding: 12,
    backgroundColor: COLORS.bgSurface,
    borderWidth: 2,
    borderRadius: SIZE.radiusMd,
    gap: 6,
  },
  favDot: { width: 10, height: 10, borderRadius: 5, marginBottom: 6 },
  favName: { fontSize: FONT.body, fontWeight: "700", color: COLORS.textPrimary },
  favHindi: { fontSize: FONT.label, color: COLORS.textSecondary },
  favLogBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    marginTop: 6,
    paddingVertical: 6,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand,
  },
  favLogText: { color: COLORS.textInverse, fontSize: FONT.label, fontWeight: "700" },
});
