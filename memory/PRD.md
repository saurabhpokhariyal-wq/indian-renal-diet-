# Indian Renal Diet — PRD

## Overview
Patient-facing Expo React Native app for CKD/dialysis patients (and their caregivers) to look up Indian foods, see safety tiers, and get kidney-friendly smart swaps.

## Personas
Elderly patients and family caregivers — must be visual, high-contrast, large touch targets, bilingual (English + हिन्दी).

## Core Features
1. **Auth (JWT + bcrypt)** — register/login/me endpoints; token stored in expo-secure-store.
2. **Local Food Search** — instant search over 35 seeded Indian foods with GREEN/YELLOW/RED safety tiers and Hindi names.
3. **Visual Safety Cards** — color-coded card with icon, tier badge, portion limit, and clinical tip.
4. **Smart Swap Card** — for any RED food (e.g. Palak Paneer, Besan Chilla, Rajma, Aloo Sabzi, Methi Saag, Full Banana, Orange, Coconut Water, Samosa, Achar) shows a green-tier alternative with clinical benefit.
5. **Ask AI** — Claude Sonnet 4.5 via Emergent LLM key answering CKD-diet questions in warm, plain language.
6. **Daily Meal Log** — add foods eaten today; shows daily summary (Safe / Caution / Avoid counts) with per-entry delete.
7. **Language Toggle** — English / हिन्दी across all UI copy, tab labels, badges.

## Tech Stack
- Backend: FastAPI, MongoDB (motor), passlib+bcrypt, python-jose (JWT), emergentintegrations (Claude Sonnet 4.5)
- Frontend: Expo SDK 54, expo-router, react-native-safe-area-context, react-native-keyboard-controller, expo-secure-store, @expo/vector-icons

## Data Model
- **users**: id, email (unique), full_name, hashed_password, created_at
- **foods**: id, name, hindi_name, category, safety_tier, primary_risk_factor, portion_limit_text, actionable_clinical_tip
- **swaps**: id, trigger_food_id (RED), recommended_swap_food_id (GREEN/YELLOW), clinical_benefit_explanation
- **meal_logs**: id, user_id, food_id, date (YYYY-MM-DD), meal_type, created_at

## API (all `/api` prefixed)
- POST `/auth/register`, POST `/auth/login`, GET `/auth/me`
- GET `/foods?q=&tier=`, GET `/foods/{id}` (includes swap if RED)
- GET `/meal-logs?date=`, POST `/meal-logs`, DELETE `/meal-logs/{id}`
- POST `/ai/ask`

## Test Credentials
See `/app/memory/test_credentials.md`.

## Testing Status
21/21 backend pytest ✅ · Full Playwright E2E ✅ (auth, search, RED→Swap flow, meal log CRUD, AI, Hindi toggle, sign-out).
