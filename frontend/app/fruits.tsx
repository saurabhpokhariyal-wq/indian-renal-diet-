import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api, type FruitEntry, type FruitGuide, type SafetyTier } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

const TIER_ORDER: SafetyTier[] = ["GREEN", "YELLOW", "RED"];

const TIER_ICON: Record<SafetyTier, keyof typeof Ionicons.glyphMap> = {
  GREEN: "checkmark-circle",
  YELLOW: "warning",
  RED: "close-circle",
};

export default function FruitsGuideScreen() {
  const { t } = useLang();
  const [guide, setGuide] = useState<FruitGuide | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const g = await api.getFruitGuide();
        if (!cancelled) setGuide(g);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load fruits guide");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.header}>
        <TouchableOpacity
          testID="fruits-back"
          style={styles.backBtn}
          onPress={() => router.back()}
          accessibilityLabel={t("back")}
        >
          <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{t("fruitGuideTitle")}</Text>
          <Text style={styles.subtitle}>{t("fruitGuideSubtitle")}</Text>
        </View>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.brand} />
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Ionicons name="alert-circle" size={40} color={COLORS.redStrong} />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : guide ? (
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.introCard}>
            <Ionicons name="information-circle" size={20} color={COLORS.brand} />
            <Text style={styles.introText}>{t("fruitGuideIntro")}</Text>
          </View>
          {TIER_ORDER.map((tier) => (
            <TierSection key={tier} tier={tier} data={guide[tier]} />
          ))}
          <View style={{ height: SIZE.xl }} />
        </ScrollView>
      ) : null}
    </SafeAreaView>
  );
}

function TierSection({ tier, data }: { tier: SafetyTier; data: FruitGuide["GREEN"] }) {
  const meta = TIER_META[tier];
  return (
    <View style={styles.section} testID={`fruit-section-${tier}`}>
      <View style={[styles.sectionHeader, { backgroundColor: meta.bg, borderColor: meta.border }]}>
        <Ionicons name={TIER_ICON[tier]} size={22} color={meta.strong} />
        <View style={{ flex: 1 }}>
          <Text style={[styles.sectionTitle, { color: meta.text }]}>{data.title}</Text>
          <Text style={[styles.sectionSubtitle, { color: meta.text }]}>{data.subtitle}</Text>
        </View>
      </View>
      {data.fruits.map((fruit, idx) => (
        <FruitRow key={`${tier}-${idx}`} fruit={fruit} tier={tier} />
      ))}
    </View>
  );
}

function FruitRow({ fruit, tier }: { fruit: FruitEntry; tier: SafetyTier }) {
  const meta = TIER_META[tier];
  const tappable = !!fruit.linked_food_id;
  const Wrapper: any = tappable ? TouchableOpacity : View;
  const wrapperProps = tappable
    ? {
        activeOpacity: 0.7,
        onPress: () => router.push(`/food/${fruit.linked_food_id}`),
        testID: `fruit-row-${fruit.name.toLowerCase().replace(/\s+/g, "-")}`,
      }
    : { testID: `fruit-row-${fruit.name.toLowerCase().replace(/\s+/g, "-")}` };
  return (
    <Wrapper style={styles.fruitRow} {...wrapperProps}>
      <View style={[styles.fruitDot, { backgroundColor: meta.strong }]} />
      <View style={{ flex: 1 }}>
        <View style={styles.fruitTitleRow}>
          <Text style={styles.fruitName}>{fruit.name}</Text>
          <Text style={styles.fruitK}>K {fruit.potassium_mg} mg</Text>
        </View>
        {fruit.hindi ? <Text style={styles.fruitHindi}>{fruit.hindi}</Text> : null}
        <Text style={styles.fruitServing}>{fruit.serving}</Text>
        <Text style={styles.fruitNote}>{fruit.note}</Text>
      </View>
      {tappable ? <Ionicons name="chevron-forward" size={18} color={COLORS.textSecondary} /> : null}
    </Wrapper>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: SIZE.m,
    paddingVertical: SIZE.s,
    gap: SIZE.s,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: COLORS.bgAlt,
  },
  title: { fontSize: FONT.h2, fontWeight: "800", color: COLORS.textPrimary },
  subtitle: { fontSize: FONT.label, color: COLORS.textSecondary },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: SIZE.m, padding: SIZE.l },
  errorText: { fontSize: FONT.body, color: COLORS.textPrimary, textAlign: "center" },
  content: { padding: SIZE.m, paddingBottom: SIZE.xxl, gap: SIZE.m },
  introCard: {
    flexDirection: "row",
    gap: 10,
    backgroundColor: COLORS.brandLight,
    borderRadius: SIZE.radiusLg,
    padding: SIZE.m,
    borderWidth: 1,
    borderColor: COLORS.brand,
  },
  introText: { flex: 1, fontSize: FONT.body, color: COLORS.textPrimary, lineHeight: 22 },
  section: { gap: SIZE.s },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    padding: SIZE.m,
    borderRadius: SIZE.radiusLg,
    borderWidth: 2,
  },
  sectionTitle: { fontSize: FONT.bodyL, fontWeight: "800" },
  sectionSubtitle: { fontSize: FONT.label, marginTop: 2, lineHeight: 18 },
  fruitRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    padding: SIZE.m,
    backgroundColor: COLORS.bgSurface,
    borderRadius: SIZE.radiusMd,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  fruitDot: { width: 10, height: 10, borderRadius: 5, marginTop: 6 },
  fruitTitleRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  fruitName: { fontSize: FONT.bodyL, fontWeight: "700", color: COLORS.textPrimary, flex: 1 },
  fruitK: { fontSize: FONT.label, fontWeight: "700", color: COLORS.textSecondary },
  fruitHindi: { fontSize: FONT.label, color: COLORS.textSecondary, marginTop: 1 },
  fruitServing: { fontSize: FONT.label, color: COLORS.brand, fontWeight: "700", marginTop: 4 },
  fruitNote: { fontSize: FONT.body, color: COLORS.textPrimary, lineHeight: 22, marginTop: 4 },
});
