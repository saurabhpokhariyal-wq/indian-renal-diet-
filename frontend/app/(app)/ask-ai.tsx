import { Ionicons } from "@expo/vector-icons";
import { useCallback, useRef, useState } from "react";
import { ActivityIndicator, FlatList, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { KeyboardAvoidingView } from "react-native-keyboard-controller";
import { SafeAreaView } from "react-native-safe-area-context";

import { api } from "@/src/lib/api";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE } from "@/src/theme";

interface Msg { id: string; role: "user" | "ai"; text: string }

export default function AskAiScreen() {
  const { t } = useLang();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);
  const listRef = useRef<FlatList<Msg>>(null);

  const send = useCallback(async () => {
    const question = input.trim();
    if (!question || loading) return;
    const userMsg: Msg = { id: `u-${Date.now()}`, role: "user", text: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const { answer } = await api.askAi(question);
      const aiMsg: Msg = { id: `a-${Date.now()}`, role: "ai", text: answer };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "AI is temporarily unavailable";
      setMessages((prev) => [...prev, { id: `e-${Date.now()}`, role: "ai", text: `⚠️ ${msg}` }]);
    } finally {
      setLoading(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }, [input, loading]);

  const data: Msg[] = messages.length === 0
    ? [{ id: "welcome", role: "ai", text: t("askAiWelcome") }]
    : messages;

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <View style={styles.header}>
        <View style={styles.headerIcon}><Ionicons name="sparkles" size={22} color={COLORS.textInverse} /></View>
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>{t("askAiTitle")}</Text>
          <Text style={styles.subtitle}>{t("askAiSubtitle")}</Text>
        </View>
      </View>

      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} keyboardVerticalOffset={80} style={{ flex: 1 }}>
        <FlatList
          ref={listRef}
          testID="ai-messages"
          data={data}
          keyExtractor={(m) => m.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <View
              testID={`ai-msg-${item.role}`}
              style={[styles.bubble, item.role === "user" ? styles.userBubble : styles.aiBubble]}
            >
              <Text style={[styles.bubbleText, item.role === "user" && { color: COLORS.textInverse }]}>
                {item.text}
              </Text>
            </View>
          )}
        />

        {loading ? (
          <View testID="ai-loading" style={styles.typing}>
            <ActivityIndicator size="small" color={COLORS.aiBlue} />
            <Text style={styles.typingText}>Thinking...</Text>
          </View>
        ) : null}

        <View style={styles.inputBar}>
          <TextInput
            testID="ai-input"
            value={input}
            onChangeText={setInput}
            placeholder={t("askAiPlaceholder")}
            placeholderTextColor="#A8A29E"
            style={styles.input}
            multiline
            maxLength={500}
          />
          <TouchableOpacity
            testID="ai-send-button"
            style={[styles.sendBtn, (!input.trim() || loading) && { opacity: 0.5 }]}
            onPress={send}
            disabled={!input.trim() || loading}
          >
            <Ionicons name="arrow-up" size={22} color={COLORS.textInverse} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  header: { flexDirection: "row", alignItems: "center", gap: 12, padding: SIZE.m },
  headerIcon: { width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.aiBlue, alignItems: "center", justifyContent: "center" },
  title: { fontSize: FONT.h2, fontWeight: "800", color: COLORS.textPrimary },
  subtitle: { fontSize: FONT.label, color: COLORS.textSecondary },
  list: { padding: SIZE.m, gap: SIZE.s, paddingBottom: SIZE.m },
  bubble: { padding: SIZE.m, borderRadius: SIZE.radiusLg, marginBottom: SIZE.s, maxWidth: "88%" },
  aiBubble: { backgroundColor: COLORS.bgSurface, borderWidth: 1, borderColor: COLORS.border, alignSelf: "flex-start" },
  userBubble: { backgroundColor: COLORS.aiBlue, alignSelf: "flex-end" },
  bubbleText: { fontSize: FONT.bodyL, color: COLORS.textPrimary, lineHeight: 24 },
  typing: { flexDirection: "row", alignItems: "center", gap: 8, padding: SIZE.m },
  typingText: { color: COLORS.textSecondary, fontSize: FONT.body },
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    padding: SIZE.m,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    backgroundColor: COLORS.bgSurface,
  },
  input: {
    flex: 1,
    minHeight: SIZE.touchPrimary,
    maxHeight: 120,
    borderRadius: SIZE.radiusLg,
    borderWidth: 2,
    borderColor: COLORS.border,
    paddingHorizontal: SIZE.m,
    paddingVertical: 12,
    fontSize: FONT.bodyL,
    color: COLORS.textPrimary,
    backgroundColor: COLORS.bgDefault,
  },
  sendBtn: {
    width: SIZE.touchPrimary,
    height: SIZE.touchPrimary,
    borderRadius: 28,
    backgroundColor: COLORS.aiBlue,
    alignItems: "center",
    justifyContent: "center",
  },
});
