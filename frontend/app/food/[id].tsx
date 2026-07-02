import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SafetyBadge } from "@/src/components/SafetyBadge";
import { SmartSwapCard } from "@/src/components/SmartSwapCard";
import { api, type FoodDetail, type SafetyTier } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

function today(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function NutriCell({ label, value, testID }: { label: string; value: string; testID?: string }) {
  return (
    <View testID={testID} style={styles.nutriCell}>
      <Text style={styles.nutriLabel}>{label}</Text>
      <Text style={styles.nutriValue}>{value}</Text>
    </View>
  );
}

export default function FoodDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { t, lang } = useLang();
  const [detail, setDetail] = useState<FoodDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [added, setAdded] = useState(false);
  const [adding, setAdding] = useState(false);
  const [favBusy, setFavBusy] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const d = await api.getFood(id);
      setDetail(d);
    } catch {
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const onAdd = async () => {
    if (!detail || adding) return;
    setAdding(true);
    try {
      await api.addMealLog(detail.food.id, today());
      setAdded(true);
      setTimeout(() => setAdded(false), 2500);
    } finally {
      setAdding(false);
    }
  };

  const onToggleFav = async () => {
    if (!detail || favBusy) return;
    setFavBusy(true);
    try {
      const res = await api.toggleFavorite(detail.food.id);
      setDetail((prev) => (prev ? { ...prev, food: { ...prev.food, is_favorite: res.is_favorite } } : prev));
    } finally {
      setFavBusy(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}><ActivityIndicator size="large" color={COLORS.brand} /></View>
      </SafeAreaView>
    );
  }
  if (!detail) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}><Text style={styles.emptyText}>Food not found</Text></View>
      </SafeAreaView>
    );
  }

  const displayTier: SafetyTier = (detail.food.personal_tier as SafetyTier | undefined) || detail.food.safety_tier;
  const meta = TIER_META[displayTier];
  const wasTightened = detail.food.personal_tier && detail.food.personal_tier !== detail.food.safety_tier;

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.topBar}>
        <TouchableOpacity testID="detail-back" onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="chevron-back" size={26} color={COLORS.textPrimary} />
          <Text style={styles.backText}>{t("back")}</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="detail-favorite" onPress={onToggleFav} disabled={favBusy} style={styles.favBtn}>
          <Ionicons
            name={detail.food.is_favorite ? "star" : "star-outline"}
            size={26}
            color={detail.food.is_favorite ? COLORS.yellowStrong : COLORS.textSecondary}
          />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={[styles.heroCard, { borderColor: meta.border, backgroundColor: meta.bg }]}>
          <SafetyBadge tier={displayTier} labelOverride={lang === "hi" ? meta.labelHi : meta.label} />
          <Text testID="detail-name" style={styles.name}>{detail.food.name}</Text>
          <Text style={styles.hindi}>{detail.food.hindi_name}</Text>
          {wasTightened ? (
            <View style={styles.personalizedNote}>
              <Ionicons name="pulse" size={14} color={meta.text} />
              <Text style={[styles.personalizedText, { color: meta.text }]}>
                Personalized for dialysis stage
              </Text>
            </View>
          ) : null}
          {detail.food.primary_risk_factor !== "NONE" ? (
            <View style={styles.riskChip}>
              <Ionicons name="alert" size={14} color={meta.text} />
              <Text style={[styles.riskText, { color: meta.text }]}>
                {t("riskFactor")}: {detail.food.primary_risk_factor}
              </Text>
            </View>
          ) : null}
        </View>

        <View style={styles.section}>
          <View style={styles.sectionHead}>
            <Ionicons name="restaurant-outline" size={20} color={COLORS.brand} />
            <Text style={styles.sectionTitle}>{t("portion")}</Text>
          </View>
          <Text testID="detail-portion" style={styles.sectionBody}>{detail.food.portion_limit_text}</Text>
        </View>

        <View style={styles.section}>
          <View style={styles.sectionHead}>
            <Ionicons name="medkit-outline" size={20} color={COLORS.brand} />
            <Text style={styles.sectionTitle}>{t("clinicalTip")}</Text>
          </View>
          <Text testID="detail-tip" style={styles.sectionBody}>{detail.food.actionable_clinical_tip}</Text>
        </View>

        {detail.food.personalized_note ? (
          <View testID="personalized-note" style={styles.personalCard}>
            <Ionicons name="person" size={20} color={COLORS.aiBlue} />
            <View style={{ flex: 1, gap: 4 }}>
              <Text style={styles.personalTitle}>{t("personalisedForYou")}</Text>
              <Text style={styles.personalBody}>{detail.food.personalized_note}</Text>
            </View>
          </View>
        ) : null}

        <View testID="nutrient-table" style={styles.section}>
          <View style={styles.sectionHead}>
            <Ionicons name="analytics-outline" size={20} color={COLORS.brand} />
            <Text style={styles.sectionTitle}>{t("perPortion")} ({Math.round(detail.food.portion_g)}g)</Text>
          </View>
          <View style={styles.nutriRow}>
            <NutriCell label={t("nutrientPotassium")} value={`${Math.round(detail.food.potassium_mg)} mg`} testID="nutri-potassium" />
            <NutriCell label={t("nutrientPhosphorus")} value={`${Math.round(detail.food.phosphorus_mg)} mg`} testID="nutri-phosphorus" />
          </View>
          <View style={styles.nutriRow}>
            <NutriCell label={t("nutrientSodium")} value={`${Math.round(detail.food.sodium_mg)} mg`} testID="nutri-sodium" />
            <NutriCell label={t("nutrientProtein")} value={`${detail.food.protein_g.toFixed(1)} g`} testID="nutri-protein" />
          </View>
          {detail.food.fluid_ml > 0 ? (
            <View style={styles.nutriRow}>
              <NutriCell label={t("nutrientFluid")} value={`${Math.round(detail.food.fluid_ml)} ml`} testID="nutri-fluid" />
              <View style={{ flex: 1 }} />
            </View>
          ) : null}
        </View>

        {detail.swap ? (
          <SmartSwapCard
            swap={detail.swap}
            onPress={() => detail.swap && router.push(`/food/${detail.swap.recommended_swap_food_id}`)}
          />
        ) : null}

        <TouchableOpacity
          testID="add-to-log-button"
          style={[styles.addBtn, added && { backgroundColor: COLORS.greenStrong }]}
          onPress={onAdd}
          disabled={adding}
        >
          <Ionicons name={added ? "checkmark-circle" : "add-circle"} size={22} color={COLORS.textInverse} />
          <Text style={styles.addBtnText}>{added ? t("added") : t("addToLog")}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  emptyText: { fontSize: FONT.bodyL, color: COLORS.textSecondary },
  topBar: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", padding: SIZE.m, paddingBottom: 0 },
  backBtn: { flexDirection: "row", alignItems: "center", gap: 4, paddingVertical: 6 },
  backText: { fontSize: FONT.bodyL, fontWeight: "600", color: COLORS.textPrimary },
  favBtn: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  container: { padding: SIZE.m, gap: SIZE.m, paddingBottom: SIZE.xxl },
  heroCard: { borderWidth: 2, borderRadius: SIZE.radiusLg, padding: SIZE.l, gap: SIZE.s },
  name: { fontSize: FONT.h1, fontWeight: "800", color: COLORS.textPrimary },
  hindi: { fontSize: FONT.h3, color: COLORS.textSecondary, fontWeight: "500" },
  personalizedNote: {
    marginTop: SIZE.s,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: "rgba(255,255,255,0.65)",
  },
  personalizedText: { fontSize: FONT.label, fontWeight: "700" },
  riskChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.75)",
  },
  riskText: { fontSize: FONT.label, fontWeight: "700" },
  section: {
    backgroundColor: COLORS.bgSurface,
    borderRadius: SIZE.radiusLg,
    padding: SIZE.m,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: 6,
  },
  sectionHead: { flexDirection: "row", alignItems: "center", gap: 8 },
  sectionTitle: { fontSize: FONT.bodyL, fontWeight: "800", color: COLORS.textPrimary },
  sectionBody: { fontSize: FONT.bodyL, color: COLORS.textPrimary, lineHeight: 26 },
  nutriRow: { flexDirection: "row", gap: SIZE.s, marginTop: 4 },
  nutriCell: {
    flex: 1,
    padding: 12,
    backgroundColor: COLORS.bgAlt,
    borderRadius: SIZE.radiusMd,
    gap: 2,
  },
  nutriLabel: { fontSize: FONT.label, color: COLORS.textSecondary, fontWeight: "600" },
  nutriValue: { fontSize: FONT.bodyL, fontWeight: "800", color: COLORS.textPrimary },
  personalCard: {
    flexDirection: "row",
    gap: 12,
    padding: SIZE.m,
    backgroundColor: "#EFF6FF",
    borderWidth: 1,
    borderColor: COLORS.aiBlue,
    borderRadius: SIZE.radiusLg,
    alignItems: "flex-start",
  },
  personalTitle: { fontSize: FONT.body, fontWeight: "800", color: COLORS.aiBlueDark },
  personalBody: { fontSize: FONT.body, color: COLORS.textPrimary, lineHeight: 22 },
  addBtn: {
    marginTop: SIZE.s,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    height: SIZE.touchPrimary,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand,
  },
  addBtnText: { color: COLORS.textInverse, fontSize: FONT.bodyL, fontWeight: "700" },
});
