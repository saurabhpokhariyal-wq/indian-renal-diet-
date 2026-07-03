import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useLang } from "@/src/lib/language-context";
import { COLORS } from "@/src/theme";

export default function AppTabsLayout() {
  const insets = useSafeAreaInsets();
  const { t } = useLang();
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: COLORS.brand,
        tabBarInactiveTintColor: COLORS.textSecondary,
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
        tabBarStyle: {
          height: 62 + insets.bottom,
          paddingBottom: insets.bottom + 6,
          paddingTop: 6,
          backgroundColor: COLORS.bgSurface,
          borderTopWidth: 1,
          borderTopColor: COLORS.border,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t("tabHome"),
          tabBarIcon: ({ color, size }) => <Ionicons name="home" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="search"
        options={{
          title: t("tabSearch"),
          tabBarIcon: ({ color, size }) => <Ionicons name="search" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="scan"
        options={{
          title: t("menuScan"),
          tabBarIcon: ({ color, size }) => <Ionicons name="camera" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="meal-log"
        options={{
          title: t("tabMeals"),
          tabBarIcon: ({ color, size }) => <Ionicons name="restaurant" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="ask-ai"
        options={{
          title: t("tabAI"),
          tabBarIcon: ({ color, size }) => <Ionicons name="sparkles" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          // Reachable from the Home menu card; hidden from the tab bar to
          // keep five large, elderly-friendly touch targets.
          href: null,
        }}
      />
    </Tabs>
  );
}
