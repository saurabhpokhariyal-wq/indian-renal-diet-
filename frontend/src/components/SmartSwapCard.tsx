import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { SafetyBadge } from "@/src/components/SafetyBadge";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE } from "@/src/theme";
import type { SwapOut } from "@/src/lib/api";

interface Props {
  swap: SwapOut;
  onPress?: () => void;
}

export function SmartSwapCard({ swap, onPress }: Props) {
  const { t } = useLang();
  const rec = swap.recommended_food;
  return (
    <View testID={`smart-swap-${swap.id}`} style={styles.wrap}>
      <View style={styles.connector} />
      <View style={styles.card}>
        <View style={styles.headerRow}>
          <View style={styles.iconBubble}>
            <Ionicons name="leaf" size={22} color={COLORS.textInverse} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.header}>{t("swapHeader")}</Text>
            <Text style={styles.headerSub}>Kidney-friendly alternative</Text>
          </View>
        </View>

        <TouchableOpacity testID={`swap-food-${rec.id}`} activeOpacity={0.85} onPress={onPress} style={styles.foodRow}>
          <View style={{ flex: 1, gap: 4 }}>
            <Text style={styles.foodName}>{rec.name}</Text>
            <Text style={styles.foodHindi}>{rec.hindi_name}</Text>
          </View>
          <SafetyBadge tier="GREEN" compact />
        </TouchableOpacity>

        <View style={styles.benefitBox}>
          <Text style={styles.benefitLabel}>{t("whyBetter")}</Text>
          <Text style={styles.benefitText}>{swap.clinical_benefit_explanation}</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    marginTop: 4,
    alignItems: "stretch",
  },
  connector: {
    width: 3,
    height: 14,
    backgroundColor: COLORS.swapBorder,
    marginLeft: SIZE.l,
  },
  card: {
    backgroundColor: COLORS.swapBg,
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: COLORS.swapBorder,
    borderRadius: SIZE.radiusLg,
    padding: SIZE.m,
    gap: 12,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  iconBubble: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.greenStrong,
    alignItems: "center",
    justifyContent: "center",
  },
  header: {
    fontSize: FONT.h3,
    fontWeight: "800",
    color: COLORS.greenText,
  },
  headerSub: {
    fontSize: FONT.label,
    color: COLORS.textSecondary,
    fontWeight: "500",
  },
  foodRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: COLORS.bgSurface,
    padding: SIZE.m,
    borderRadius: SIZE.radiusMd,
    borderWidth: 1,
    borderColor: COLORS.greenBorder,
  },
  foodName: {
    fontSize: FONT.h3,
    fontWeight: "700",
    color: COLORS.textPrimary,
  },
  foodHindi: {
    fontSize: FONT.body,
    color: COLORS.textSecondary,
  },
  benefitBox: {
    gap: 6,
  },
  benefitLabel: {
    fontSize: FONT.label,
    fontWeight: "800",
    color: COLORS.greenText,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  benefitText: {
    fontSize: FONT.body,
    color: COLORS.textPrimary,
    lineHeight: 22,
  },
});
