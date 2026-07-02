import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE } from "@/src/theme";

export default function SettingsScreen() {
  const { user, signOut } = useAuth();
  const { lang, setLang, t } = useLang();

  const doSignOut = async () => {
    await signOut();
    router.replace("/(auth)/login");
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{t("settingsTitle")}</Text>

        <View style={styles.card}>
          <View style={styles.userRow}>
            <View style={styles.avatar}>
              <Ionicons name="person" size={26} color={COLORS.textInverse} />
            </View>
            <View style={{ flex: 1 }}>
              <Text testID="settings-user-name" style={styles.userName} numberOfLines={1}>
                {user?.full_name || "Friend"}
              </Text>
              <Text style={styles.userEmail} numberOfLines={1}>{user?.email}</Text>
            </View>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.section}>{t("language")}</Text>
          <View style={styles.langRow}>
            <LangButton
              testID="lang-en"
              label={t("english")}
              active={lang === "en"}
              onPress={() => setLang("en")}
            />
            <LangButton
              testID="lang-hi"
              label={t("hindi")}
              active={lang === "hi"}
              onPress={() => setLang("hi")}
            />
          </View>
        </View>

        <View style={[styles.card, { backgroundColor: COLORS.brandLight, borderColor: COLORS.brand }]}>
          <View style={{ flexDirection: "row", gap: 10 }}>
            <Ionicons name="information-circle" size={22} color={COLORS.brand} />
            <Text style={styles.disclaimer}>{t("disclaimer")}</Text>
          </View>
        </View>

        <TouchableOpacity testID="signout-button" style={styles.signOutBtn} onPress={doSignOut}>
          <Ionicons name="log-out-outline" size={22} color={COLORS.redStrong} />
          <Text style={styles.signOutText}>{t("signOut")}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function LangButton({ label, active, onPress, testID }: { label: string; active: boolean; onPress: () => void; testID: string }) {
  return (
    <TouchableOpacity
      testID={testID}
      onPress={onPress}
      style={[styles.langBtn, active && styles.langBtnActive]}
    >
      <Text style={[styles.langBtnText, active && styles.langBtnTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  container: { padding: SIZE.m, gap: SIZE.m, paddingBottom: SIZE.xxl },
  title: { fontSize: FONT.h1, fontWeight: "800", color: COLORS.textPrimary },
  card: {
    backgroundColor: COLORS.bgSurface,
    borderRadius: SIZE.radiusLg,
    padding: SIZE.m,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: SIZE.m,
  },
  userRow: { flexDirection: "row", gap: 14, alignItems: "center" },
  avatar: { width: 52, height: 52, borderRadius: 26, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center" },
  userName: { fontSize: FONT.h3, fontWeight: "700", color: COLORS.textPrimary },
  userEmail: { fontSize: FONT.body, color: COLORS.textSecondary },
  section: { fontSize: FONT.bodyL, fontWeight: "700", color: COLORS.textPrimary },
  langRow: { flexDirection: "row", gap: SIZE.s },
  langBtn: {
    flex: 1,
    height: SIZE.touchPrimary,
    borderRadius: SIZE.radiusMd,
    borderWidth: 2,
    borderColor: COLORS.border,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: COLORS.bgDefault,
  },
  langBtnActive: { borderColor: COLORS.brand, backgroundColor: COLORS.brandLight },
  langBtnText: { fontSize: FONT.bodyL, color: COLORS.textSecondary, fontWeight: "600" },
  langBtnTextActive: { color: COLORS.brand, fontWeight: "800" },
  disclaimer: { flex: 1, color: COLORS.textPrimary, fontSize: FONT.body, lineHeight: 22 },
  signOutBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    height: SIZE.touchPrimary,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.redBg,
    borderWidth: 2,
    borderColor: COLORS.redBorder,
  },
  signOutText: { color: COLORS.redStrong, fontSize: FONT.bodyL, fontWeight: "700" },
});
