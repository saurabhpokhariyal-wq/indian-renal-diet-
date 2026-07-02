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

export interface FoodOut {
  id: string;
  name: string;
  hindi_name: string;
  category: string;
  safety_tier: SafetyTier;
  primary_risk_factor: string;
  portion_limit_text: string;
  actionable_clinical_tip: string;
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

export interface UserOut {
  id: string;
  email: string;
  full_name: string;
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
  food: FoodOut;
  created_at: string;
}

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

  listFoods: (q?: string, tier?: string) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (tier) params.set("tier", tier);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return request<FoodOut[]>(`/foods${suffix}`);
  },
  getFood: (id: string) => request<FoodDetail>(`/foods/${id}`),

  listMealLogs: (date: string) =>
    request<MealLogOut[]>(`/meal-logs?date=${encodeURIComponent(date)}`, {}, true),
  addMealLog: (food_id: string, date: string, meal_type: string = "meal") =>
    request<MealLogOut>(
      "/meal-logs",
      { method: "POST", body: JSON.stringify({ food_id, date, meal_type }) },
      true,
    ),
  deleteMealLog: (id: string) =>
    request<{ success: boolean }>(`/meal-logs/${id}`, { method: "DELETE" }, true),

  askAi: (question: string) =>
    request<{ answer: string }>("/ai/ask", { method: "POST", body: JSON.stringify({ question }) }, true),
};
