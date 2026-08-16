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

import type { SafetyTier } from "@/src/lib/api";
import { useAuth } from "@/src/lib/auth-context";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

/**
 * Reusable curated food-guide layout used by:
 *  - fruits.tsx        (entries key: "fruits")
 *  - beverages.tsx     (entries key: "beverages", showFluidChip)
 *  - vegetables.tsx    (entries key: "vegetables")
 *  - snacks.tsx        (entries key: "snacks")
 *  - proteins.tsx      (entries key: "proteins")
 *  - grains.tsx        (entries key: "grains")
 *
 * A single component keeps testIDs, animations, and clinical UX consistent.
 */

export interface GuideEntry {
  name: string;
  hindi?: string;
  serving: string;
  potassium_mg: number;
  /** Derived server-side: potassium_mg / 39.1, rounded to 1 dp. */
  potassium_meq?: number;
  fluid_ml?: number; // only used for beverages
  /** Sourced sodium content in mg. Missing values are `null` (never guessed). */
  sodium_mg?: number | null;
  /** Sourced phosphorus content in mg. Missing values are `null`. Rarely rendered
   *  directly on guide rows — kept on the model for AI grounding and detail views. */
  phosphorus_mg?: number | null;
  /** Derived server-side: true when sodium_mg >= 400 (matches seed-DB RED threshold). */
  high_sodium?: boolean;
  note: string;
  linked_food_id?: string | null;
  /** Provenance string when the entry was sourced from a primary dataset
   *  (e.g. "IFCT 2017, code E046"). Absent for legacy web-sourced entries. */
  source?: string;
}

export interface GuideSection {
  title: string;
  subtitle: string;
  [key: string]: unknown; // entries array under `entriesKey`
}

export type GuideData = Record<SafetyTier, GuideSection>;

export type IntroTheme = "brand" | "aiBlue";

export interface FoodGuideLayoutProps {
  /** Function that fetches the guide payload (e.g. api.getFruitGuide). */
  fetchGuide: () => Promise<GuideData>;
  /** Header title text (already translated). */
  title: string;
  /** Header subtitle text (already translated). */
  subtitle: string;
  /** Intro card body text (already translated). */
  intro: string;
  /** Icon shown inside the intro card. */
  introIcon: keyof typeof Ionicons.glyphMap;
  /** Intro card + icon color palette. Defaults to "brand" (green). */
  introTheme?: IntroTheme;
  /** Key inside each tier section holding the entries array (e.g. "fruits"). */
  entriesKey: "fruits" | "beverages" | "vegetables" | "snacks" | "proteins" | "grains";
  /** Prefix used for stable testIDs on tier sections and rows. */
  testIdPrefix: string;
  /** Prefix used for back-button testID (e.g. "fruits" → "fruits-back"). */
  backTestIdPrefix: string;
  /** Show the fluid_ml chip on each row (beverages only). */
  showFluidChip?: boolean;
  /** Optional error message override (already translated). */
  errorLabel?: string;
}

const TIER_ORDER: SafetyTier[] = ["GREEN", "YELLOW", "RED"];

const TIER_ICON: Record<SafetyTier, keyof typeof Ionicons.glyphMap> = {
  GREEN: "checkmark-circle",
  YELLOW: "warning",
  RED: "close-circle",
};

function slug(v: string): string {
  return v
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function FoodGuideLayout({
  fetchGuide,
  title,
  subtitle,
  intro,
  introIcon,
  introTheme = "brand",
  entriesKey,
  testIdPrefix,
  backTestIdPrefix,
  showFluidChip = false,
  errorLabel,
}: FoodGuideLayoutProps) {
  const { user } = useAuth();
  const unit = user?.nutrient_unit ?? "mg";
  const [guide, setGuide] = useState<GuideData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const g = await fetchGuide();
        if (!cancelled) setGuide(g);
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : errorLabel ?? "Failed to load guide"
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // fetchGuide is expected to be stable in call sites; we intentionally only rerun on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const introBg = introTheme === "aiBlue" ? "#E0F2FE" : COLORS.brandLight;
  const introBorder = introTheme === "aiBlue" ? COLORS.aiBlue : COLORS.brand;
  const introIconColor = introTheme === "aiBlue" ? COLORS.aiBlue : COLORS.brand;

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <View style={styles.header}>
        <TouchableOpacity
          testID={`${backTestIdPrefix}-back`}
          style={styles.backBtn}
          onPress={() => router.back()}
          accessibilityLabel="Back"
        >
          <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>
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
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
        >
          <View
            style={[
              styles.introCard,
              { backgroundColor: introBg, borderColor: introBorder },
            ]}
          >
            <Ionicons name={introIcon} size={20} color={introIconColor} />
            <Text style={styles.introText}>{intro}</Text>
          </View>

          {TIER_ORDER.map((tier) => {
            const section = guide[tier];
            const entries = (section?.[entriesKey] as GuideEntry[] | undefined) ?? [];
            const meta = TIER_META[tier];
            return (
              <View
                key={tier}
                style={styles.section}
                testID={`${testIdPrefix}-section-${tier}`}
              >
                <View
                  style={[
                    styles.sectionHeader,
                    { backgroundColor: meta.bg, borderColor: meta.border },
                  ]}
                >
                  <Ionicons name={TIER_ICON[tier]} size={22} color={meta.strong} />
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.sectionTitle, { color: meta.text }]}>
                      {section.title}
                    </Text>
                    <Text style={[styles.sectionSubtitle, { color: meta.text }]}>
                      {section.subtitle}
                    </Text>
                  </View>
                </View>

                {entries.map((entry, idx) => (
                  <GuideRow
                    key={`${tier}-${idx}`}
                    entry={entry}
                    tier={tier}
                    testId={`${testIdPrefix}-row-${slug(entry.name)}`}
                    showFluidChip={showFluidChip}
                    unit={unit}
                  />
                ))}
              </View>
            );
          })}

          <View style={{ height: SIZE.xl }} />
        </ScrollView>
      ) : null}
    </SafeAreaView>
  );
}

function GuideRow({
  entry,
  tier,
  testId,
  showFluidChip,
  unit,
}: {
  entry: GuideEntry;
  tier: SafetyTier;
  testId: string;
  showFluidChip: boolean;
  unit: "mg" | "mEq";
}) {
  const meta = TIER_META[tier];
  const tappable = !!entry.linked_food_id;
  const Wrapper: any = tappable ? TouchableOpacity : View;
  const wrapperProps = tappable
    ? {
        activeOpacity: 0.7,
        onPress: () => router.push(`/food/${entry.linked_food_id}`),
        testID: testId,
      }
    : { testID: testId };

  // Guide rows show BOTH units regardless of the user's global toggle — clinicians and
  // patients need to cross-reference between food-label mg counts and lab-report mEq.
  // The user's preferred unit is placed first for consistency with the rest of the app.
  const mg = Math.round(entry.potassium_mg);
  const meq =
    typeof entry.potassium_meq === "number"
      ? entry.potassium_meq.toFixed(1)
      : (entry.potassium_mg / 39.1).toFixed(1);
  const kStr =
    unit === "mEq"
      ? `${meq} mEq / ${mg} mg`
      : `${mg} mg / ${meq} mEq`;

  return (
    <Wrapper style={styles.row} {...wrapperProps}>
      <View style={[styles.dot, { backgroundColor: meta.strong }]} />
      <View style={{ flex: 1 }}>
        <View style={styles.titleRow}>
          <Text style={styles.name}>{entry.name}</Text>
          <View style={styles.metrics}>
            <Text style={styles.kmg} testID={`${testId}-k`}>K {kStr}</Text>
            {showFluidChip && typeof entry.fluid_ml === "number" ? (
              <View style={styles.fluidChip}>
                <Ionicons name="water" size={12} color={COLORS.aiBlue} />
                <Text style={styles.fluidText}>{entry.fluid_ml} ml</Text>
              </View>
            ) : null}
          </View>
        </View>
        {entry.hindi ? <Text style={styles.hindi}>{entry.hindi}</Text> : null}
        <Text style={styles.serving}>{entry.serving}</Text>
        {entry.high_sodium ? (
          <View style={styles.sodiumBadge} testID={`${testId}-high-sodium`}>
            <Ionicons name="warning" size={12} color={COLORS.redStrong} />
            <Text style={styles.sodiumBadgeText}>
              High Sodium
              {typeof entry.sodium_mg === "number"
                ? ` — ${Math.round(entry.sodium_mg)} mg per serving`
                : ""}
            </Text>
          </View>
        ) : null}
        <Text style={styles.note}>{entry.note}</Text>
        {entry.source ? (
          <Text style={styles.sourceText} testID={`${testId}-source`}>
            Source: {entry.source}
          </Text>
        ) : null}
      </View>
      {tappable ? (
        <Ionicons name="chevron-forward" size={18} color={COLORS.textSecondary} />
      ) : null}
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
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: SIZE.m,
    padding: SIZE.l,
  },
  errorText: { fontSize: FONT.body, color: COLORS.textPrimary, textAlign: "center" },
  content: { padding: SIZE.m, paddingBottom: SIZE.xxl, gap: SIZE.m },
  introCard: {
    flexDirection: "row",
    gap: 10,
    borderRadius: SIZE.radiusLg,
    padding: SIZE.m,
    borderWidth: 1,
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
  row: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    padding: SIZE.m,
    backgroundColor: COLORS.bgSurface,
    borderRadius: SIZE.radiusMd,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  dot: { width: 10, height: 10, borderRadius: 5, marginTop: 6 },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 4,
  },
  name: { fontSize: FONT.bodyL, fontWeight: "700", color: COLORS.textPrimary, flex: 1 },
  metrics: { flexDirection: "row", alignItems: "center", gap: 6 },
  kmg: { fontSize: FONT.label, fontWeight: "700", color: COLORS.textSecondary },
  fluidChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: SIZE.radiusPill,
    backgroundColor: "#E0F2FE",
    borderWidth: 1,
    borderColor: COLORS.aiBlue,
  },
  fluidText: { fontSize: FONT.label, fontWeight: "700", color: COLORS.aiBlue },
  sodiumBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.redBg,
    borderWidth: 1,
    borderColor: COLORS.redBorder,
    marginTop: 6,
  },
  sodiumBadgeText: {
    fontSize: FONT.label,
    fontWeight: "800",
    color: COLORS.redStrong,
  },
  hindi: { fontSize: FONT.label, color: COLORS.textSecondary, marginTop: 1 },
  serving: { fontSize: FONT.label, color: COLORS.brand, fontWeight: "700", marginTop: 4 },
  note: { fontSize: FONT.body, color: COLORS.textPrimary, lineHeight: 22, marginTop: 4 },
  sourceText: {
    fontSize: 11,
    color: COLORS.textSecondary,
    fontStyle: "italic",
    marginTop: 6,
  },
});
