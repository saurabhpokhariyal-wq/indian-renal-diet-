import { storage } from "@/src/utils/storage";

const BASE = process.env.EXPO_PUBLIC_BACKEND_URL;
const TOKEN_KEY = "renal.jwt";

async function getToken(): Promise<string | null> {
  return await storage.secureGet<string>(TOKEN_KEY, "");
}

export async function setToken(token: string | null) {
  if (token) await storage.secureSet(TOKEN_KEY, token);
  else await storage.secureRemove(TOKEN_KEY);
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  auth: boolean = false,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (auth) {
    const token = await getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE}/api${path}`, { ...init, headers });
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const detail =
      (data && typeof data === "object" && "detail" in data && (data as { detail: string }).detail) ||
      `Request failed (${res.status})`;
    throw new Error(String(detail));
  }
  return data as T;
}

// ---------------- Types ----------------
export type SafetyTier = "GREEN" | "YELLOW" | "RED";
export type ScanTier = SafetyTier | "UNVERIFIED";
export type Stage = "pre_dialysis" | "dialysis" | "unknown";

export interface FoodOut {
  id: string;
  name: string;
  hindi_name: string;
  category: string;
  safety_tier: SafetyTier;
  primary_risk_factor: string;
  portion_limit_text: string;
  actionable_clinical_tip: string;
  portion_g: number;
  potassium_mg: number;
  phosphorus_mg: number;
  sodium_mg: number;
  protein_g: number;
  fluid_ml: number;
  personal_tier?: SafetyTier | null;
  personalized_note?: string | null;
  serving_disclaimer?: string | null;
  is_favorite?: boolean;
  brand?: string | null;
  source?: string | null;
  tier_override?: boolean | null;
  override_reason?: string | null;
  auto_rescaled?: boolean | null;
  data_quality_flag?: string | null;
}

export interface SwapOut {
  id: string;
  trigger_food_id: string;
  recommended_swap_food_id: string;
  recommended_food: FoodOut;
  clinical_benefit_explanation: string;
}

export interface FoodDetail {
  food: FoodOut;
  swap: SwapOut | null;
}

export interface DoctorLimits {
  potassium_mg?: number | null;
  phosphorus_mg?: number | null;
  sodium_mg?: number | null;
  fluid_ml?: number | null;
}

export interface UserOut {
  id: string;
  email: string;
  full_name: string;
  stage: Stage;
  diabetic: boolean;
  doctor_limits: DoctorLimits | null;
  nutrient_unit: "mg" | "mEq";
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserOut;
}

export interface MealLogOut {
  id: string;
  food_id: string;
  date: string;
  meal_type: string;
  quantity_multiplier?: number;
  food: FoodOut;
  created_at: string;
}

export interface MealItemCandidate {
  food_id: string;
  name: string;
  hindi_name: string;
  category: string;
  safety_tier: SafetyTier;
  portion_limit_text: string;
}

export interface ParsedMealItem {
  item_text: string;
  quantity_multiplier: number;
  outcome: "match_single" | "match_multiple" | "no_match";
  candidates: MealItemCandidate[];
}

export interface AiLogMealResponse {
  parsed_items: ParsedMealItem[];
  notice?: string | null;
}

export interface WeeklyReportDay {
  date: string;
  green: number;
  yellow: number;
  red: number;
}

export interface NutrientTotals {
  potassium_mg: number;
  phosphorus_mg: number;
  sodium_mg: number;
  protein_g: number;
  fluid_ml: number;
}

export interface NutrientLimits {
  potassium_mg: number;
  phosphorus_mg: number;
  sodium_mg: number;
  fluid_ml: number;
}

export interface MealLogSummary {
  date: string;
  total_meals: number;
  totals: NutrientTotals;
  limits: NutrientLimits;
}

export interface WeeklyReport {
  start_date: string;
  end_date: string;
  total_meals: number;
  green: number;
  yellow: number;
  red: number;
  days: WeeklyReportDay[];
  top_safe_foods: string[];
  top_avoid_foods: string[];
  avg_daily: NutrientTotals;
  limits: NutrientLimits;
}

export interface FoodScan {
  food_name: string;
  hindi_name: string | null;
  safety_tier: ScanTier;
  primary_risk_factor: string;
  portion_limit_text: string;
  clinical_tip: string;
  matched_food_id: string | null;
  barcode?: string | null;
  brand?: string | null;
  portion_g?: number | null;
  potassium_mg?: number | null;
  phosphorus_mg?: number | null;
  sodium_mg?: number | null;
  protein_g?: number | null;
  raw: string | null;
}

export interface FruitEntry {
  name: string;
  hindi: string;
  serving: string;
  potassium_mg: number;
  note: string;
  linked_food_id: string | null;
}

export interface FruitGuideSection {
  title: string;
  subtitle: string;
  fruits: FruitEntry[];
}

export interface FruitGuide {
  GREEN: FruitGuideSection;
  YELLOW: FruitGuideSection;
  RED: FruitGuideSection;
}

export interface BeverageEntry {
  name: string;
  hindi: string;
  serving: string;
  potassium_mg: number;
  fluid_ml: number;
  note: string;
  linked_food_id: string | null;
}

export interface BeverageGuideSection {
  title: string;
  subtitle: string;
  beverages: BeverageEntry[];
}

export interface BeverageGuide {
  GREEN: BeverageGuideSection;
  YELLOW: BeverageGuideSection;
  RED: BeverageGuideSection;
}

export type Lang = "en" | "hi" | "ta" | "bn" | "mr";

// ---------------- API ----------------
export const api = {
  register: (email: string, password: string, full_name?: string) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<UserOut>("/auth/me", {}, true),
  setStage: (stage: Stage) =>
    request<UserOut>("/auth/stage", { method: "POST", body: JSON.stringify({ stage }) }, true),
  updateProfile: (patch: { diabetic?: boolean; doctor_limits?: DoctorLimits | null; nutrient_unit?: "mg" | "mEq" }) =>
    request<UserOut>("/auth/profile", { method: "PATCH", body: JSON.stringify(patch) }, true),

  listFoods: (q?: string, tier?: string, favoritesOnly = false) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (tier) params.set("tier", tier);
    if (favoritesOnly) params.set("favorites_only", "true");
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return request<FoodOut[]>(`/foods${suffix}`, {}, true);
  },
  getFood: (id: string) => request<FoodDetail>(`/foods/${id}`, {}, true),

  toggleFavorite: (foodId: string) =>
    request<{ food_id: string; is_favorite: boolean }>(`/favorites/${foodId}`, { method: "POST" }, true),

  listMealLogs: (date: string) =>
    request<MealLogOut[]>(`/meal-logs?date=${encodeURIComponent(date)}`, {}, true),
  getMealSummary: (date: string) =>
    request<MealLogSummary>(`/meal-logs/summary?date=${encodeURIComponent(date)}`, {}, true),
  addMealLog: (food_id: string, date: string, meal_type: string = "meal", quantity_multiplier: number = 1.0) =>
    request<MealLogOut>(
      "/meal-logs",
      { method: "POST", body: JSON.stringify({ food_id, date, meal_type, quantity_multiplier }) },
      true,
    ),
  deleteMealLog: (id: string) =>
    request<{ success: boolean }>(`/meal-logs/${id}`, { method: "DELETE" }, true),

  parseMealText: (text: string, date: string, meal_type: string = "meal", lang: Lang = "en") =>
    request<AiLogMealResponse>(
      "/ai/log-meal",
      { method: "POST", body: JSON.stringify({ text, date, meal_type, lang }) },
      true,
    ),

  weeklyReport: (endDate?: string) => {
    const s = endDate ? `?end_date=${endDate}` : "";
    return request<WeeklyReport>(`/reports/weekly${s}`, {}, true);
  },

  scanFood: (image_base64: string) =>
    request<FoodScan>("/scan/food", { method: "POST", body: JSON.stringify({ image_base64 }) }, true),

  scanBarcode: (barcode: string) =>
    request<FoodScan>("/scan/barcode", { method: "POST", body: JSON.stringify({ barcode }) }, true),

  getFruitGuide: () => request<FruitGuide>("/fruits/guide", {}, true),

  getBeverageGuide: () => request<BeverageGuide>("/beverages/guide", {}, true),
  getVegetableGuide: () => request<Record<string, { title: string; subtitle: string; vegetables: FruitEntry[] }>>("/vegetables/guide", {}, true),
  getSnackGuide: () => request<Record<string, { title: string; subtitle: string; snacks: FruitEntry[] }>>("/snacks/guide", {}, true),
  getProteinGuide: () => request<Record<string, { title: string; subtitle: string; proteins: FruitEntry[] }>>("/proteins/guide", {}, true),
  getGrainGuide: () => request<Record<string, { title: string; subtitle: string; grains: FruitEntry[] }>>("/grains/guide", {}, true),
  getOilGuide: () => request<Record<string, { title: string; subtitle: string; oils: FruitEntry[] }>>("/oils/guide", {}, true),

  askAi: (question: string, lang: Lang = "en") =>
    request<{ answer: string }>("/ai/ask", { method: "POST", body: JSON.stringify({ question, lang }) }, true),
};
