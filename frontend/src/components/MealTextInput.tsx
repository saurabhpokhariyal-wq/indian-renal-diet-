/**
 * Natural-language meal-logging UI, extracted from the old standalone
 * /log-meal-nl route so it can be embedded as the "text" mode inside
 * scan.tsx (iter-28 nav consolidation — one screen, three input methods).
 *
 * The component owns nothing about camera/permission — that's scan.tsx's
 * job. It just renders the "describe your meal → parse → confirm items →
 * commit as meal-logs" flow.
 */
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import { SafetyBadge } from "@/src/components/SafetyBadge";
import { api, type MealItemCandidate, type ParsedMealItem } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE, TIER_META } from "@/src/theme";

type ItemState = ParsedMealItem & {
  selected_food_id: string | null;
  quantity: number;
};

function isoToday(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function MealTextInput({
  date,
  mealType = "meal",
}: {
  date?: string;
  mealType?: string;
}) {
  const { t, lang } = useLang();
  const initialDate = date || isoToday();

  const [text, setText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [items, setItems] = useState<ItemState[] | null>(null);
  const [committing, setCommitting] = useState(false);

  const readyToLog = useMemo(
    () => !!items && items.some((it) => !!it.selected_food_id),
    [items],
  );

  const doParse = async () => {
    if (!text.trim()) {
      Alert.alert("", t("emptyMealText"));
      return;
    }
    setParsing(true);
    try {
      const res = await api.parseMealText(text, initialDate, mealType, lang);
      const staged: ItemState[] = res.parsed_items.map((p) => ({
        ...p,
        selected_food_id:
          p.outcome === "match_single" && p.candidates.length === 1
            ? p.candidates[0].food_id
            : null,
        quantity: p.quantity_multiplier || 1,
      }));
      setItems(staged);
      if (res.notice) Alert.alert("", res.notice);
    } catch (e) {
      Alert.alert("Error", e instanceof Error ? e.message : "Failed to parse");
    } finally {
      setParsing(false);
    }
  };

  const pickCandidate = (idx: number, foodId: string) =>
    setItems((prev) =>
      prev
        ? prev.map((it, i) => (i === idx ? { ...it, selected_food_id: foodId } : it))
        : prev,
    );

  const skipItem = (idx: number) =>
    setItems((prev) =>
      prev
        ? prev.map((it, i) => (i === idx ? { ...it, selected_food_id: null } : it))
        : prev,
    );

  const updateQty = (idx: number, delta: number) =>
    setItems((prev) =>
      prev
        ? prev.map((it, i) =>
            i === idx
              ? {
                  ...it,
                  quantity: Math.max(0.5, Math.min(10, +(it.quantity + delta).toFixed(1))),
                }
              : it,
          )
        : prev,
    );

  const commit = async () => {
    if (!items || committing) return;
    setCommitting(true);
    let count = 0;
    let failed = 0;
    try {
      for (const it of items) {
        if (!it.selected_food_id) continue;
        try {
          await api.addMealLog(it.selected_food_id, initialDate, mealType, it.quantity);
          count += 1;
        } catch {
          failed += 1;
        }
      }
      const msg = t("loggedCount").replace("{n}", String(count));
      Alert.alert("", failed > 0 ? `${msg} (${failed} failed)` : msg);
      router.replace("/(app)/meal-log");
    } finally {
      setCommitting(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      style={{ flex: 1 }}
      testID="meal-text-input"
    >
      <ScrollView contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
        <View style={s.headerRow}>
          <Text style={s.title}>{t("logByTextTitle")}</Text>
          <Text style={s.subtitle}>{initialDate} · {mealType}</Text>
        </View>

        <View style={s.introCard}>
          <Ionicons name="sparkles" size={20} color={COLORS.brand} />
          <Text style={s.introText}>{t("logByTextSub")}</Text>
        </View>

        <TextInput
          testID="logmeal-input"
          style={s.input}
          multiline
          value={text}
          onChangeText={setText}
          placeholder="2 rotis, 1 katori dal, small bowl of curd"
          placeholderTextColor="#A8A29E"
        />

        <TouchableOpacity
          testID="logmeal-parse"
          style={[s.primaryBtn, (parsing || !text.trim()) && { opacity: 0.6 }]}
          onPress={doParse}
          disabled={parsing || !text.trim()}
        >
          {parsing ? (
            <ActivityIndicator color={COLORS.textInverse} />
          ) : (
            <>
              <Ionicons name="search" size={18} color={COLORS.textInverse} />
              <Text style={s.primaryText}>{t("parseMeal")}</Text>
            </>
          )}
        </TouchableOpacity>

        {items && items.length > 0 ? (
          <View style={{ gap: SIZE.m, marginTop: SIZE.s }}>
            {items.map((it, idx) => (
              <ItemCard
                key={idx}
                idx={idx}
                item={it}
                onPick={pickCandidate}
                onSkip={skipItem}
                onQtyChange={updateQty}
                tSkip={t("skipItem")}
                tPick={t("pickMatch")}
                tNoMatch={t("noMatch")}
                tQty={t("quantityLabel")}
              />
            ))}
            <TouchableOpacity
              testID="logmeal-commit"
              style={[s.primaryBtn, (!readyToLog || committing) && { opacity: 0.6 }]}
              onPress={commit}
              disabled={!readyToLog || committing}
            >
              {committing ? (
                <ActivityIndicator color={COLORS.textInverse} />
              ) : (
                <>
                  <Ionicons name="checkmark-circle" size={20} color={COLORS.textInverse} />
                  <Text style={s.primaryText}>{t("confirmAndLog")}</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        ) : items && items.length === 0 ? (
          <Text style={s.emptyText}>{t("noMatch")}</Text>
        ) : null}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function ItemCard({
  idx,
  item,
  onPick,
  onSkip,
  onQtyChange,
  tSkip,
  tPick,
  tNoMatch,
  tQty,
}: {
  idx: number;
  item: ItemState;
  onPick: (idx: number, foodId: string) => void;
  onSkip: (idx: number) => void;
  onQtyChange: (idx: number, delta: number) => void;
  tSkip: string;
  tPick: string;
  tNoMatch: string;
  tQty: string;
}) {
  const skipped = item.selected_food_id === null && item.outcome !== "no_match";
  return (
    <View testID={`logmeal-item-${idx}`} style={s.itemCard}>
      <View style={s.itemHeader}>
        <Text style={s.itemText} numberOfLines={2}>{`"${item.item_text}"`}</Text>
        <View style={s.qtyRow}>
          <Text style={s.qtyLabel}>{tQty}</Text>
          <TouchableOpacity
            testID={`logmeal-qty-minus-${idx}`}
            style={s.qtyBtn}
            onPress={() => onQtyChange(idx, -0.5)}
          >
            <Text style={s.qtyBtnText}>−</Text>
          </TouchableOpacity>
          <Text testID={`logmeal-qty-${idx}`} style={s.qtyVal}>{item.quantity}</Text>
          <TouchableOpacity
            testID={`logmeal-qty-plus-${idx}`}
            style={s.qtyBtn}
            onPress={() => onQtyChange(idx, 0.5)}
          >
            <Text style={s.qtyBtnText}>+</Text>
          </TouchableOpacity>
        </View>
      </View>

      {item.outcome === "no_match" ? (
        <View style={s.noMatchPill}>
          <Ionicons name="alert-circle" size={16} color={COLORS.yellowStrong} />
          <Text style={s.noMatchText}>{tNoMatch}</Text>
        </View>
      ) : (
        <>
          {item.outcome === "match_multiple" ? (
            <Text style={s.pickHint}>{tPick}</Text>
          ) : null}
          <View style={{ gap: 8 }}>
            {item.candidates.map((c) => (
              <CandidateRow
                key={c.food_id}
                cand={c}
                selected={item.selected_food_id === c.food_id}
                onPress={() => onPick(idx, c.food_id)}
                testID={`logmeal-cand-${idx}-${c.food_id}`}
              />
            ))}
          </View>
          <TouchableOpacity
            testID={`logmeal-skip-${idx}`}
            style={[s.skipBtn, skipped && s.skipBtnActive]}
            onPress={() => onSkip(idx)}
          >
            <Text style={[s.skipText, skipped && s.skipTextActive]}>{tSkip}</Text>
          </TouchableOpacity>
        </>
      )}
    </View>
  );
}

function CandidateRow({
  cand,
  selected,
  onPress,
  testID,
}: {
  cand: MealItemCandidate;
  selected: boolean;
  onPress: () => void;
  testID: string;
}) {
  const meta = TIER_META[cand.safety_tier];
  return (
    <TouchableOpacity
      testID={testID}
      onPress={onPress}
      style={[
        s.cand,
        {
          borderColor: selected ? COLORS.brand : COLORS.border,
          backgroundColor: selected ? COLORS.brandLight : COLORS.bgSurface,
        },
      ]}
    >
      <View style={{ flex: 1 }}>
        <Text style={s.candName} numberOfLines={1}>{cand.name}</Text>
        <Text style={s.candHindi} numberOfLines={1}>{cand.hindi_name}</Text>
        <Text style={s.candPortion} numberOfLines={2}>{cand.portion_limit_text}</Text>
      </View>
      <View style={{ alignItems: "flex-end", gap: 6 }}>
        <SafetyBadge tier={cand.safety_tier} labelOverride={meta.label} compact />
        <Ionicons
          name={selected ? "radio-button-on" : "radio-button-off"}
          size={20}
          color={selected ? COLORS.brand : COLORS.textSecondary}
        />
      </View>
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  content: { padding: SIZE.m, paddingBottom: SIZE.xxl, gap: SIZE.m },
  headerRow: { gap: 4 },
  title: { fontSize: FONT.h2, fontWeight: "800", color: COLORS.textPrimary },
  subtitle: { fontSize: FONT.label, color: COLORS.textSecondary },
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
  input: {
    minHeight: 120,
    borderRadius: SIZE.radiusLg,
    borderWidth: 2,
    borderColor: COLORS.border,
    padding: SIZE.m,
    fontSize: FONT.bodyL,
    color: COLORS.textPrimary,
    backgroundColor: COLORS.bgSurface,
    textAlignVertical: "top",
  },
  primaryBtn: {
    flexDirection: "row",
    gap: 8,
    height: SIZE.touchPrimary,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryText: { color: COLORS.textInverse, fontSize: FONT.bodyL, fontWeight: "700" },
  itemCard: {
    backgroundColor: COLORS.bgSurface,
    borderRadius: SIZE.radiusLg,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: SIZE.m,
    gap: SIZE.s,
  },
  itemHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8, flexWrap: "wrap" },
  itemText: { flex: 1, fontSize: FONT.bodyL, fontWeight: "700", color: COLORS.textPrimary, fontStyle: "italic" },
  qtyRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  qtyLabel: { fontSize: FONT.label, color: COLORS.textSecondary, marginRight: 4 },
  qtyBtn: { width: 30, height: 30, borderRadius: 15, alignItems: "center", justifyContent: "center", backgroundColor: COLORS.bgAlt, borderWidth: 1, borderColor: COLORS.border },
  qtyBtnText: { fontSize: 18, fontWeight: "800", color: COLORS.textPrimary },
  qtyVal: { fontSize: FONT.body, fontWeight: "800", color: COLORS.textPrimary, minWidth: 32, textAlign: "center" },
  pickHint: { fontSize: FONT.label, fontWeight: "700", color: COLORS.textSecondary },
  cand: { flexDirection: "row", alignItems: "center", gap: 10, borderWidth: 1, borderRadius: SIZE.radiusMd, padding: SIZE.s },
  candName: { fontSize: FONT.body, fontWeight: "700", color: COLORS.textPrimary },
  candHindi: { fontSize: FONT.label, color: COLORS.textSecondary },
  candPortion: { fontSize: FONT.label, color: COLORS.brand, marginTop: 2 },
  skipBtn: { alignSelf: "flex-start", paddingHorizontal: 12, paddingVertical: 6, borderRadius: SIZE.radiusPill, backgroundColor: COLORS.bgAlt, borderWidth: 1, borderColor: COLORS.border },
  skipBtnActive: { backgroundColor: COLORS.yellowBg, borderColor: COLORS.yellowBorder },
  skipText: { fontSize: FONT.label, fontWeight: "700", color: COLORS.textSecondary },
  skipTextActive: { color: COLORS.yellowText },
  noMatchPill: { flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "flex-start", paddingHorizontal: 10, paddingVertical: 4, borderRadius: SIZE.radiusPill, backgroundColor: COLORS.yellowBg, borderWidth: 1, borderColor: COLORS.yellowBorder },
  noMatchText: { fontSize: FONT.label, fontWeight: "700", color: COLORS.yellowText },
  emptyText: { fontSize: FONT.body, color: COLORS.textSecondary, textAlign: "center", padding: SIZE.l },
});
