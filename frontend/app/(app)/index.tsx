import { Ionicons } from "@expo/vector-icons";
import { router, type Href } from "expo-router";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE } from "@/src/theme";

type MenuItem = {
  key: string;
  icon: keyof typeof Ionicons.glyphMap;
  titleKey: string;
  subtitleKey: string;
  href: Href;
  accent: string;
  accentBg: string;
};

const MENU: MenuItem[] = [
  {
    key: "search",
    icon: "search",
    titleKey: "tabSearch",
    subtitleKey: "menuSearchSub",
    href: "/(app)/search",
    accent: COLORS.brand,
    accentBg: COLORS.brandLight,
  },
  {
    key: "fruits",
    icon: "nutrition",
    titleKey: "menuFruits",
    subtitleKey: "menuFruitsSub",
    href: "/fruits",
    accent: COLORS.greenStrong,
    accentBg: COLORS.greenBg,
  },
  {
    key: "scan",
    icon: "camera",
    titleKey: "menuScan",
    subtitleKey: "menuScanSub",
    href: "/(app)/scan",
    accent: COLORS.yellowStrong,
    accentBg: COLORS.yellowBg,
  },
  {
    key: "meals",
    icon: "restaurant",
    titleKey: "tabMeals",
    subtitleKey: "menuMealsSub",
    href: "/(app)/meal-log",
    accent: COLORS.greenStrong,
    accentBg: COLORS.greenBg,
  },
  {
    key: "report",
    icon: "document-text",
    titleKey: "menuReport",
    subtitleKey: "menuReportSub",
    href: "/report",
    accent: COLORS.redStrong,
    accentBg: COLORS.redBg,
  },
  {
    key: "ai",
    icon: "sparkles",
    titleKey: "tabAI",
    subtitleKey: "menuAISub",
    href: "/(app)/ask-ai",
    accent: COLORS.aiBlue,
    accentBg: "#E0F2FE",
  },
  {
    key: "settings",
    icon: "settings",
    titleKey: "tabSettings",
    subtitleKey: "menuSettingsSub",
    href: "/(app)/settings",
    accent: COLORS.textSecondary,
    accentBg: COLORS.bgAlt,
  },
];

export default function HomeScreen() {
  const { user } = useAuth();
  const { t } = useLang();

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.greetRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.greetHi}>{t("greeting")},</Text>
            <Text testID="user-greeting" style={styles.greetName} numberOfLines={1}>
              {user?.full_name || user?.email?.split("@")[0] || "Friend"}
            </Text>
          </View>
          <View style={styles.logo}>
            <Ionicons name="leaf" size={22} color={COLORS.textInverse} />
          </View>
        </View>

        <Text style={styles.menuTitle}>{t("menuTitle")}</Text>

        <View style={styles.grid}>
          {MENU.map((item) => (
            <TouchableOpacity
              key={item.key}
              testID={`home-menu-${item.key}`}
              style={styles.card}
              activeOpacity={0.75}
              onPress={() => router.push(item.href)}
              accessibilityRole="button"
              accessibilityLabel={t(item.titleKey)}
            >
              <View style={[styles.iconBubble, { backgroundColor: item.accentBg }]}>
                <Ionicons name={item.icon} size={28} color={item.accent} />
              </View>
              <Text style={styles.cardTitle} numberOfLines={1}>
                {t(item.titleKey)}
              </Text>
              <Text style={styles.cardSubtitle} numberOfLines={2}>
                {t(item.subtitleKey)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  container: { padding: SIZE.m, paddingBottom: SIZE.xxl, gap: SIZE.m },
  greetRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  greetHi: { fontSize: FONT.body, color: COLORS.textSecondary },
  greetName: { fontSize: FONT.h2, fontWeight: "800", color: COLORS.textPrimary },
  logo: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.brand,
    alignItems: "center",
    justifyContent: "center",
  },
  menuTitle: { fontSize: FONT.h3, fontWeight: "800", color: COLORS.textPrimary, marginTop: SIZE.s },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: SIZE.m },
  card: {
    // Two columns: half the row minus half the gap.
    flexBasis: "47%",
    flexGrow: 1,
    minHeight: 150,
    padding: SIZE.m,
    backgroundColor: COLORS.bgSurface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: SIZE.radiusLg,
    gap: 8,
  },
  iconBubble: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
  },
  cardTitle: { fontSize: FONT.bodyL, fontWeight: "800", color: COLORS.textPrimary },
  cardSubtitle: { fontSize: FONT.label, color: COLORS.textSecondary, lineHeight: 19 },
});
