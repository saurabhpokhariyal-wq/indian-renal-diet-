import { Redirect } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { useAuth } from "@/src/lib/auth-context";
import { disclaimerKey } from "@/src/lib/storage-keys";
import { storage } from "@/src/utils/storage";
import { COLORS } from "@/src/theme";

export default function Index() {
  const { user, loading } = useAuth();
  const [disclaimerAccepted, setDisclaimerAccepted] = useState<boolean | null>(null);

  useEffect(() => {
    if (!user) {
      setDisclaimerAccepted(null);
      return;
    }
    let cancelled = false;
    (async () => {
      const val = await storage.getItem<string>(disclaimerKey(user.id), "");
      if (!cancelled) setDisclaimerAccepted(val === "accepted");
    })();
    return () => {
      cancelled = true;
    };
  }, [user]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.brand} />
      </View>
    );
  }
  if (!user) return <Redirect href="/(auth)/login" />;
  if (disclaimerAccepted === null) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.brand} />
      </View>
    );
  }
  if (!disclaimerAccepted) return <Redirect href="/disclaimer" />;
  if (user.stage === "unknown") return <Redirect href="/onboarding" />;
  return <Redirect href="/(app)" />;
}

const styles = StyleSheet.create({
  center: { flex: 1, backgroundColor: COLORS.bgDefault, alignItems: "center", justifyContent: "center" },
});
