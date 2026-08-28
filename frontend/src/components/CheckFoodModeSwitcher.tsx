import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { ScrollView, StyleSheet, Text, TouchableOpacity } from "react-native";

import { COLORS, FONT, SIZE } from "@/src/theme";

export type CheckMode = "type" | "photo" | "voice";

/**
 * Three-tab pill shown at the top of every "check a food" input screen —
 * Type (search), Photo (scan camera), Voice (scan natural-language text).
 *
 * All three modes now live on TWO routes:
 *   type  → /(app)/search
 *   photo → /(app)/scan            (defaults to camera vision mode)
 *   voice → /(app)/scan?mode=text  (natural-language description mode)
 *
 * The camera + text modes share scan.tsx after iter-28 nav consolidation
 * so switching between "snap a photo", "scan a barcode", and "describe
 * what you ate" feels like one screen with three input methods.
 */

const MODE_ROUTE: Record<CheckMode, string> = {
  type: "/(app)/search",
  photo: "/(app)/scan",
  voice: "/(app)/scan?mode=text",
};

const MODE_ICON: Record<CheckMode, keyof typeof import("@expo/vector-icons").Ionicons.glyphMap> = {
  type: "search",
  photo: "camera",
  voice: "mic",
};

const MODE_LABEL: Record<CheckMode, string> = {
  type: "Type",
  photo: "Photo",
  voice: "Voice",
};

export function CheckFoodModeSwitcher({ current }: { current: CheckMode }) {
  const modes: CheckMode[] = ["type", "photo", "voice"];
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.row}
      testID="check-mode-switcher"
    >
      {modes.map((m) => {
        const active = m === current;
        return (
          <TouchableOpacity
            key={m}
            testID={`check-mode-${m}`}
            accessibilityRole="tab"
            accessibilityState={{ selected: active }}
            accessibilityLabel={MODE_LABEL[m]}
            onPress={() => {
              if (!active) router.replace(MODE_ROUTE[m] as never);
            }}
            style={[styles.chip, active && styles.chipActive]}
          >
            <Ionicons
              name={MODE_ICON[m]}
              size={18}
              color={active ? COLORS.textInverse : COLORS.brand}
            />
            <Text style={[styles.text, active && styles.textActive]}>{MODE_LABEL[m]}</Text>
          </TouchableOpacity>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: {
    gap: SIZE.s,
    paddingHorizontal: SIZE.m,
    paddingTop: SIZE.s,
    paddingBottom: 4,
  },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 16,
    height: 40,
    borderRadius: SIZE.radiusPill,
    borderWidth: 2,
    borderColor: COLORS.brand,
    backgroundColor: COLORS.brandLight,
  },
  chipActive: { backgroundColor: COLORS.brand },
  text: { color: COLORS.brand, fontWeight: "700", fontSize: FONT.body },
  textActive: { color: COLORS.textInverse },
});
