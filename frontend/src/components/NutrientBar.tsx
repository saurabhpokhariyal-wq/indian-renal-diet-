import { StyleSheet, Text, View } from "react-native";

import { COLORS, FONT, SIZE } from "@/src/theme";

interface Props {
  label: string;
  value: number;
  limit: number;
  unit?: string;
  testID?: string;
}

function tierColor(pct: number): { fill: string; text: string } {
  if (pct < 60) return { fill: COLORS.greenStrong, text: COLORS.greenText };
  if (pct < 90) return { fill: COLORS.yellowStrong, text: COLORS.yellowText };
  return { fill: COLORS.redStrong, text: COLORS.redText };
}

export function NutrientBar({ label, value, limit, unit = "mg", testID }: Props) {
  const rawPct = limit > 0 ? (value * 100) / limit : 0;
  const clampedPct = Math.max(0, Math.min(100, rawPct));
  const { fill, text } = tierColor(rawPct);
  const over = rawPct > 100;
  return (
    <View testID={testID} style={styles.row}>
      <View style={styles.header}>
        <Text style={styles.label}>{label}</Text>
        <Text testID={testID ? `${testID}-value` : undefined} style={[styles.value, { color: over ? COLORS.redStrong : COLORS.textPrimary }]}>
          {Math.round(value)}
          <Text style={styles.limitText}> / {Math.round(limit)}{unit}</Text>
        </Text>
      </View>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${clampedPct}%`, backgroundColor: fill }]} />
      </View>
      <Text style={[styles.pctText, { color: text }]}>{Math.round(rawPct)}%</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { gap: 4 },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  label: { fontSize: FONT.body, fontWeight: "700", color: COLORS.textPrimary },
  value: { fontSize: FONT.body, fontWeight: "700" },
  limitText: { fontSize: FONT.label, fontWeight: "500", color: COLORS.textSecondary },
  track: {
    height: 10,
    borderRadius: 5,
    backgroundColor: COLORS.bgAlt,
    overflow: "hidden",
    marginTop: 4,
  },
  fill: { height: "100%", borderRadius: 5 },
  pctText: { fontSize: 12, fontWeight: "700", alignSelf: "flex-end", marginTop: 2 },
});

export { tierColor };
export const _internal = { SIZE };
