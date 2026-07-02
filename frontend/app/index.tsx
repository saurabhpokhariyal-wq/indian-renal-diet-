import { Redirect } from "expo-router";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { useAuth } from "@/src/lib/auth-context";
import { COLORS } from "@/src/theme";

export default function Index() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.brand} />
      </View>
    );
  }
  if (!user) return <Redirect href="/(auth)/login" />;
  if (user.stage === "unknown") return <Redirect href="/onboarding" />;
  return <Redirect href="/(app)" />;
}

const styles = StyleSheet.create({
  center: { flex: 1, backgroundColor: COLORS.bgDefault, alignItems: "center", justifyContent: "center" },
});
