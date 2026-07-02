import { Ionicons } from "@expo/vector-icons";
import { Link, router } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "@/src/lib/auth-context";
import { useLang } from "@/src/lib/language-context";
import { COLORS, FONT, SIZE } from "@/src/theme";

export default function Register() {
  const { signUp } = useAuth();
  const { t } = useLang();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    if (!email || !password) {
      setError("Please fill in email and password");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    try {
      await signUp(email.trim(), password, fullName.trim() || undefined);
      router.replace("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>
        <View style={styles.container}>
          <View style={styles.brandRow}>
            <View style={styles.logo}><Ionicons name="leaf" size={28} color={COLORS.textInverse} /></View>
            <Text style={styles.brandName}>Indian Renal Diet</Text>
          </View>

          <Text testID="register-title" style={styles.title}>{t("registerTitle")}</Text>
          <Text style={styles.subtitle}>{t("registerSubtitle")}</Text>

          <View style={styles.field}>
            <Text style={styles.label}>{t("fullName")}</Text>
            <TextInput
              testID="register-name-input"
              style={styles.input}
              value={fullName}
              onChangeText={setFullName}
              placeholder="Priya Sharma"
              placeholderTextColor="#A8A29E"
              autoCapitalize="words"
            />
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>{t("email")}</Text>
            <TextInput
              testID="register-email-input"
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="you@example.com"
              placeholderTextColor="#A8A29E"
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>{t("password")}</Text>
            <TextInput
              testID="register-password-input"
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="min 6 characters"
              placeholderTextColor="#A8A29E"
              secureTextEntry
            />
          </View>

          {error ? <Text testID="register-error" style={styles.error}>{error}</Text> : null}

          <TouchableOpacity
            testID="register-submit-button"
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={onSubmit}
            disabled={loading}
          >
            <Text style={styles.buttonText}>{loading ? "..." : t("signUp")}</Text>
          </TouchableOpacity>

          <Link href="/(auth)/login" asChild>
            <TouchableOpacity testID="link-to-login" style={styles.linkRow}>
              <Text style={styles.linkText}>{t("hasAccount")}</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.bgDefault },
  container: { flex: 1, padding: SIZE.l, gap: SIZE.m, justifyContent: "center" },
  brandRow: { flexDirection: "row", alignItems: "center", gap: 12, marginBottom: SIZE.l },
  logo: { width: 48, height: 48, borderRadius: 24, backgroundColor: COLORS.brand, alignItems: "center", justifyContent: "center" },
  brandName: { fontSize: FONT.h3, fontWeight: "800", color: COLORS.brand },
  title: { fontSize: FONT.h1, fontWeight: "800", color: COLORS.textPrimary },
  subtitle: { fontSize: FONT.body, color: COLORS.textSecondary, marginBottom: SIZE.s },
  field: { gap: 6 },
  label: { fontSize: FONT.body, color: COLORS.textPrimary, fontWeight: "600" },
  input: {
    height: SIZE.touchPrimary,
    borderRadius: SIZE.radiusMd,
    borderWidth: 2,
    borderColor: COLORS.border,
    backgroundColor: COLORS.bgSurface,
    paddingHorizontal: SIZE.m,
    fontSize: FONT.bodyL,
    color: COLORS.textPrimary,
  },
  button: {
    height: SIZE.touchPrimary,
    borderRadius: SIZE.radiusPill,
    backgroundColor: COLORS.brand,
    alignItems: "center",
    justifyContent: "center",
    marginTop: SIZE.s,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: COLORS.textInverse, fontSize: FONT.bodyL, fontWeight: "700" },
  linkRow: { alignItems: "center", padding: SIZE.m },
  linkText: { color: COLORS.brand, fontSize: FONT.body, fontWeight: "600" },
  error: { color: COLORS.redStrong, fontSize: FONT.body, fontWeight: "600" },
});
