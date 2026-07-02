import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";

import { COLORS, FONT, SIZE, TIER_META, type SafetyTier } from "@/src/theme";

interface Props {
  tier: SafetyTier;
  labelOverride?: string;
  compact?: boolean;
}

export function SafetyBadge({ tier, labelOverride, compact = false }: Props) {
  const meta = TIER_META[tier];
  const label = labelOverride ?? meta.label;
  return (
    <View
      testID={`safety-badge-${tier.toLowerCase()}`}
      style={[
        styles.badge,
        { backgroundColor: meta.bg, borderColor: meta.border },
        compact && styles.compact,
      ]}
    >
      <Ionicons name={meta.icon} size={compact ? 16 : 20} color={meta.strong} />
      <Text
        style={[
          styles.text,
          { color: meta.text, fontSize: compact ? FONT.label : FONT.body },
        ]}
        numberOfLines={1}
      >
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: SIZE.m,
    paddingVertical: 6,
    borderRadius: SIZE.radiusPill,
    borderWidth: 2,
    alignSelf: "flex-start",
  },
  compact: {
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  text: {
    fontWeight: "700",
    letterSpacing: 0.2,
    color: COLORS.textPrimary,
  },
});
