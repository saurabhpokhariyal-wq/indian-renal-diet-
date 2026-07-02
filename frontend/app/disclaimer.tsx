import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { disclaimerKey } from "@/src/lib/storage-keys";
import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import { storage } from "@/src/utils/storage";
import { COLORS, FONT, SIZE } from "@/src/theme";

export default function DisclaimerScreen() {
  const { user } = useAuth();
  const { t } = useLang();
  const params = useLocalSearchParams<{ readonly?: string }>();
  const readOnly = params.readonly === "1";
  const [saving, setSaving] = useState(false);

  const accept = async () => {
    if (!user || saving) return;
    setSaving(true);
    try {
      await storage.setItem(disclaimerKey(user.id), "accepted");
      router.replace("/");
    } finally {
      setSaving(false);
    }
  };

  const close = () => router.back();

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.iconBubble}>
          <Ionicons name="medkit" size={40} color={COLORS.textInverse} />
        </View>

        <Text testID="disclaimer-title" style={styles.title}>{t("disclaimerScreenTitle")}</Text>
        <Text style={styles.lead}>{t("disclaimerScreenLead")}</Text>

        <View style={styles.pointBox}>
          <Ionicons name="information-circle" size={22} color={COLORS.brand} />
          <Text style={styles.pointText}>{t("disclaimerP1")}</Text>
        </View>
        <View style={styles.pointBox}>
          <Ionicons name="pulse" size={22} color={COLORS.brand} />
          <Text style={styles.pointText}>{t("disclaimerP2")}</Text>
        </View>
        <View style={styles.pointBox}>
          <Ionicons name="sparkles" size={22} color={COLORS.brand} />
          <Text style={styles.pointText}>{t("disclaimerP3")}</Text>
        </View>

        {readOnly ? (
          <TouchableOpacity testID="disclaimer-close" style={styles.primaryBtn} onPress={close}>
            <Text style={styles.primaryText}>{t("disclaimerClose")}</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            testID="disclaimer-accept"
            style={[styles.primaryBtn, saving && { opacity: 0.6 }]}
            onPress={accept}
            disabled={saving}
          >
            <Ionicons name="checkmark-circle" size={22} color={COLORS.textInverse} />
            <Text style={styles.primaryText}>{t("disclaimerAccept")}</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  container: { padding: SIZE.l, gap: SIZE.m, paddingBottom: SIZE.xxl },
  iconBubble: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: COLORS.brand,
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "center",
    marginTop: SIZE.l,
  },
  title: { fontSize: FONT.h1, fontWeight: "800", color: COLORS.textPrimary, textAlign: "center", marginTop: 4 },
  lead: {
    fontSize: FONT.bodyL,
    color: COLORS.textPrimary,
    textAlign: "center",
    lineHeight: 26,
    marginBottom: SIZE.s,
    fontWeight: "600",
  },
  pointBox: {
    flexDirection: "row",
    gap: 12,
    padding: SIZE.m,
    backgroundColor: COLORS.bgSurface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: SIZE.radiusLg,
    alignItems: "flex-start",
  },
  pointText: { flex: 1, fontSize: FONT.body, color: COLORS.textPrimary, lineHeight: 22 },
  primaryBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    height: SIZE.touchPrimary,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand,
    marginTop: SIZE.m,
  },
  primaryText: { color: COLORS.textInverse, fontSize: FONT.bodyL, fontWeight: "700" },
});
