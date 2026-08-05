import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { api, type FruitEntry, type SafetyTier } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

type Section = { title: string; subtitle: string; grains: FruitEntry[] };
type Guide = Record<SafetyTier, Section>;
const TIER_ORDER: SafetyTier[] = ["GREEN", "YELLOW", "RED"];
const TIER_ICON: Record<SafetyTier, keyof typeof Ionicons.glyphMap> = { GREEN: "checkmark-circle", YELLOW: "warning", RED: "close-circle" };

export default function GrainsGuideScreen() {
  const { t } = useLang();
  const [guide, setGuide] = useState<Guide | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let c = false;
    (async () => {
      try { const g = await api.getGrainGuide() as Guide; if (!c) setGuide(g); }
      catch (e) { if (!c) setError(e instanceof Error ? e.message : "Failed"); }
      finally { if (!c) setLoading(false); }
    })();
    return () => { c = true; };
  }, []);
  return (
    <SafeAreaView style={s.safe} edges={["top", "bottom"]}>
      <View style={s.header}>
        <TouchableOpacity testID="grains-back" style={s.backBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={s.title}>{t("grainGuideTitle")}</Text>
          <Text style={s.subtitle}>{t("grainGuideSubtitle")}</Text>
        </View>
      </View>
      {loading ? <View style={s.center}><ActivityIndicator size="large" color={COLORS.brand} /></View>
      : error ? <View style={s.center}><Ionicons name="alert-circle" size={40} color={COLORS.redStrong} /><Text>{error}</Text></View>
      : guide ? (
        <ScrollView contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>
          <View style={s.introCard}>
            <Ionicons name="pizza" size={20} color={COLORS.brand} />
            <Text style={s.introText}>{t("grainGuideIntro")}</Text>
          </View>
          {TIER_ORDER.map((tier) => {
            const data = guide[tier]; const meta = TIER_META[tier];
            return (
              <View key={tier} style={s.section} testID={`grain-section-${tier}`}>
                <View style={[s.secHeader, { backgroundColor: meta.bg, borderColor: meta.border }]}>
                  <Ionicons name={TIER_ICON[tier]} size={22} color={meta.strong} />
                  <View style={{ flex: 1 }}>
                    <Text style={[s.secTitle, { color: meta.text }]}>{data.title}</Text>
                    <Text style={[s.secSub, { color: meta.text }]}>{data.subtitle}</Text>
                  </View>
                </View>
                {data.grains.map((v, i) => {
                  const tap = !!v.linked_food_id;
                  const tid = `grain-row-${v.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
                  const W: any = tap ? TouchableOpacity : View;
                  const p = tap ? { activeOpacity: 0.7, onPress: () => router.push(`/food/${v.linked_food_id}`), testID: tid } : { testID: tid };
                  return (
                    <W key={i} style={s.row} {...p}>
                      <View style={[s.dot, { backgroundColor: meta.strong }]} />
                      <View style={{ flex: 1 }}>
                        <View style={s.titleRow}><Text style={s.name}>{v.name}</Text><Text style={s.kmg}>K {v.potassium_mg} mg</Text></View>
                        {v.hindi ? <Text style={s.hindi}>{v.hindi}</Text> : null}
                        <Text style={s.serving}>{v.serving}</Text>
                        <Text style={s.note}>{v.note}</Text>
                      </View>
                      {tap ? <Ionicons name="chevron-forward" size={18} color={COLORS.textSecondary} /> : null}
                    </W>
                  );
                })}
              </View>
            );
          })}
          <View style={{ height: SIZE.xl }} />
        </ScrollView>
      ) : null}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  header: { flexDirection: "row", alignItems: "center", paddingHorizontal: SIZE.m, paddingVertical: SIZE.s, gap: SIZE.s },
  backBtn: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: COLORS.bgAlt },
  title: { fontSize: FONT.h2, fontWeight: "800", color: COLORS.textPrimary },
  subtitle: { fontSize: FONT.label, color: COLORS.textSecondary },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: SIZE.m, padding: SIZE.l },
  content: { padding: SIZE.m, paddingBottom: SIZE.xxl, gap: SIZE.m },
  introCard: { flexDirection: "row", gap: 10, backgroundColor: COLORS.brandLight, borderRadius: SIZE.radiusLg, padding: SIZE.m, borderWidth: 1, borderColor: COLORS.brand },
  introText: { flex: 1, fontSize: FONT.body, color: COLORS.textPrimary, lineHeight: 22 },
  section: { gap: SIZE.s },
  secHeader: { flexDirection: "row", alignItems: "flex-start", gap: 10, padding: SIZE.m, borderRadius: SIZE.radiusLg, borderWidth: 2 },
  secTitle: { fontSize: FONT.bodyL, fontWeight: "800" },
  secSub: { fontSize: FONT.label, marginTop: 2, lineHeight: 18 },
  row: { flexDirection: "row", alignItems: "flex-start", gap: 12, padding: SIZE.m, backgroundColor: COLORS.bgSurface, borderRadius: SIZE.radiusMd, borderWidth: 1, borderColor: COLORS.border },
  dot: { width: 10, height: 10, borderRadius: 5, marginTop: 6 },
  titleRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  name: { fontSize: FONT.bodyL, fontWeight: "700", color: COLORS.textPrimary, flex: 1 },
  kmg: { fontSize: FONT.label, fontWeight: "700", color: COLORS.textSecondary },
  hindi: { fontSize: FONT.label, color: COLORS.textSecondary, marginTop: 1 },
  serving: { fontSize: FONT.label, color: COLORS.brand, fontWeight: "700", marginTop: 4 },
  note: { fontSize: FONT.body, color: COLORS.textPrimary, lineHeight: 22, marginTop: 4 },
});
