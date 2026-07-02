import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { SafetyBadge } from "@/src/components/SafetyBadge";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";
import type { FoodOut } from "@/src/lib/api";

interface Props {
  food: FoodOut;
  onPress?: () => void;
  showTip?: boolean;
}

export function SafetyCard({ food, onPress, showTip = true }: Props) {
  const { lang, t } = useLang();
  const meta = TIER_META[food.safety_tier];
  return (
    <TouchableOpacity
      testID={`safety-card-${food.id}`}
      activeOpacity={0.85}
      onPress={onPress}
      style={[styles.card, { borderColor: meta.border, backgroundColor: COLORS.bgSurface }]}
    >
      <View style={styles.headerRow}>
        <View style={{ flex: 1, gap: 4 }}>
          <Text testID={`food-name-${food.id}`} style={styles.title} numberOfLines={2}>
            {food.name}
          </Text>
          <Text style={styles.hindi} numberOfLines={1}>{food.hindi_name}</Text>
        </View>
        <SafetyBadge tier={food.safety_tier} labelOverride={lang === "hi" ? meta.labelHi : meta.label} compact />
      </View>

      <View style={[styles.pill, { backgroundColor: meta.bg, borderColor: meta.border }]}>
        <Ionicons name="restaurant-outline" size={16} color={meta.text} />
        <Text style={[styles.pillText, { color: meta.text }]} numberOfLines={2}>
          <Text style={{ fontWeight: "700" }}>{t("portion")}: </Text>
          {food.portion_limit_text}
        </Text>
      </View>

      {showTip ? (
        <Text style={styles.tip} numberOfLines={3}>
          <Text style={styles.tipLabel}>{t("clinicalTip")}: </Text>
          {food.actionable_clinical_tip}
        </Text>
      ) : null}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 2,
    borderRadius: SIZE.radiusLg,
    padding: SIZE.m,
    gap: 12,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  title: {
    fontSize: FONT.h3,
    fontWeight: "700",
    color: COLORS.textPrimary,
  },
  hindi: {
    fontSize: FONT.bodyL,
    color: COLORS.textSecondary,
    fontWeight: "500",
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderRadius: SIZE.radiusMd,
    paddingHorizontal: SIZE.m,
    paddingVertical: 10,
  },
  pillText: {
    fontSize: FONT.body,
    flex: 1,
    lineHeight: 22,
  },
  tip: {
    fontSize: FONT.body,
    color: COLORS.textSecondary,
    lineHeight: 22,
  },
  tipLabel: {
    fontWeight: "700",
    color: COLORS.textPrimary,
  },
});
