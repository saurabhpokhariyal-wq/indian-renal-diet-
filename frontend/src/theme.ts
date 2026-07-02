export const COLORS = {
  bgDefault: "#FAFAF9",
  bgSurface: "#FFFFFF",
  bgAlt: "#F5F5F4",
  textPrimary: "#1C1917",
  textSecondary: "#57534E",
  textInverse: "#FFFFFF",
  brand: "#2F5233",
  brandDark: "#1E3B22",
  brandLight: "#EAF3EC",
  border: "#D6D3D1",
  aiBlue: "#0284C7",
  aiBlueDark: "#026FA6",

  greenText: "#064E3B",
  greenBg: "#D1FAE5",
  greenBorder: "#34D399",
  greenStrong: "#059669",

  yellowText: "#78350F",
  yellowBg: "#FEF3C7",
  yellowBorder: "#F59E0B",
  yellowStrong: "#D97706",

  redText: "#7F1D1D",
  redBg: "#FEE2E2",
  redBorder: "#F87171",
  redStrong: "#DC2626",

  swapBg: "#F0FDF4",
  swapBorder: "#22C55E",
};

export const SIZE = {
  radiusSm: 8,
  radiusMd: 12,
  radiusLg: 16,
  radiusXl: 24,
  radiusPill: 28,

  s: 8,
  m: 16,
  l: 24,
  xl: 32,
  xxl: 48,

  touchMin: 44,
  touchPrimary: 56,
};

export const FONT = {
  h1: 32,
  h2: 26,
  h3: 22,
  bodyL: 18,
  body: 16,
  label: 14,
};

export type SafetyTier = "GREEN" | "YELLOW" | "RED";

export const TIER_META: Record<SafetyTier, {
  label: string;
  labelHi: string;
  bg: string;
  border: string;
  text: string;
  strong: string;
  icon: "checkmark-circle" | "warning" | "alert-circle";
}> = {
  GREEN: {
    label: "Safe / Recommended",
    labelHi: "सुरक्षित",
    bg: COLORS.greenBg,
    border: COLORS.greenBorder,
    text: COLORS.greenText,
    strong: COLORS.greenStrong,
    icon: "checkmark-circle",
  },
  YELLOW: {
    label: "Caution / Limit Portions",
    labelHi: "सावधानी",
    bg: COLORS.yellowBg,
    border: COLORS.yellowBorder,
    text: COLORS.yellowText,
    strong: COLORS.yellowStrong,
    icon: "warning",
  },
  RED: {
    label: "Avoid / Danger",
    labelHi: "टालें",
    bg: COLORS.redBg,
    border: COLORS.redBorder,
    text: COLORS.redText,
    strong: COLORS.redStrong,
    icon: "alert-circle",
  },
};
