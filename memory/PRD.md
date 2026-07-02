# Indian Renal Diet — PRD

## Overview
Patient-facing Expo React Native app for CKD/dialysis patients (and their caregivers) to look up Indian foods, see safety tiers, personalize by stage, log meals, share weekly reports with their nephrologist, and scan foods with AI vision.

## Personas
Elderly patients and family caregivers — visual, high-contrast, large touch targets, bilingual (English + हिन्दी).

## Core Features
1. **Auth (JWT + bcrypt)** — register/login/me/stage endpoints; token stored in expo-secure-store.
2. **Onboarding Quiz** — first-run stage picker (Pre-dialysis CKD / On Dialysis). Dialysis stage tightens YELLOW foods with POTASSIUM/PHOSPHORUS/FLUID risk to RED via `personal_tier`, and auto-generates a swap suggestion when no direct swap exists.
3. **Local Food Search** — instant search over 35 seeded Indian foods with GREEN/YELLOW/RED safety tiers and Hindi names.
4. **Visual Safety Cards** — color-coded card with icon, tier badge, portion limit, and clinical tip.
5. **Smart Swap Card** — for any RED food (base or personalized) shows a green-tier alternative with clinical benefit.
6. **Favorites** — star toggle on food detail; "My Favorites" horizontal row on Home with one-tap "Log" button.
7. **Ask AI** — Claude Sonnet 4.5 via Emergent LLM key answering CKD-diet questions in warm, plain language.
8. **Camera Food Scan** — expo-camera + expo-image-manipulator captures & compresses JPEG; POST to `/api/scan/food` where Claude Sonnet 4.5 **vision** identifies the dish and returns structured safety JSON.
9. **Daily Meal Log** — add foods eaten today; per-day Safe/Caution/Avoid summary; delete entries.
10. **Weekly PDF Report** — 7-day bar chart, top-safe & top-avoid foods; exportable/shareable as PDF via expo-print + expo-sharing for nephrologist visits.
11. **English ↔ हिन्दी** toggle across all screens.

## Tech Stack
- **Backend**: FastAPI, MongoDB (motor), passlib+bcrypt, python-jose (JWT), emergentintegrations (Claude Sonnet 4.5 text + vision)
- **Frontend**: Expo SDK 54, expo-router (typed routes), expo-camera, expo-image-manipulator, expo-print, expo-sharing, expo-secure-store, react-native-safe-area-context, react-native-keyboard-controller, @expo/vector-icons

## Data Model
- **users**: id, email (unique), full_name, stage ("pre_dialysis"|"dialysis"|"unknown"), hashed_password, created_at
- **foods**: id, name, hindi_name, category, safety_tier, primary_risk_factor, portion_limit_text, actionable_clinical_tip
- **swaps**: id, trigger_food_id (RED), recommended_swap_food_id, clinical_benefit_explanation
- **favorites**: id, user_id, food_id, created_at (unique index on user_id+food_id)
- **meal_logs**: id, user_id, food_id, date (YYYY-MM-DD), meal_type, created_at

## API (all `/api` prefixed)
- POST `/auth/register`, POST `/auth/login`, GET `/auth/me`, POST `/auth/stage`
- GET `/foods?q=&tier=&favorites_only=`, GET `/foods/{id}` (includes personal_tier, is_favorite, and swap if effective tier=RED)
- POST `/favorites/{food_id}` (toggle)
- GET `/meal-logs?date=`, POST `/meal-logs`, DELETE `/meal-logs/{id}`
- GET `/reports/weekly?end_date=`
- POST `/ai/ask`, POST `/scan/food`

## Test Credentials
See `/app/memory/test_credentials.md`.

## Testing Status
- Iteration 1: 21/21 backend pytest ✅ · full Playwright E2E ✅
- Iteration 2 (4 new features): 23/23 backend pytest ✅ · Playwright E2E ✅
- Iteration 3 (security & correctness hardening): 27/27 backend pytest ✅
  - CORS origins from env, regex.escape on `q`, generic 502 errors on AI/scan,
    Pydantic Literal `meal_type` + calendar-date validator, DuplicateKeyError
    handled on register, slowapi rate limits (auth 5/min IP, ai 10/min user,
    scan 5/min user), lifespan context manager, batched `$in` food lookups,
    single favorites-set fetch per request.
- Iteration 4 (frontend robustness & consent): 7/7 features verified ✅
  - First-run medical disclaimer with per-user persistence
    (`renal.disclaimer.<userId>`) + settings re-read entry.
  - Search & Meal Log: distinct error state + Retry button.
  - Search tier filter chips (GREEN/YELLOW/RED, multi-select, toggleable).
  - Ask AI messages persisted per user (`renal.chat.<userId>`) with clear button.
  - `LogBox.ignoreAllLogs` removed; own shadow-style warning fixed via
    `Platform.select`. Only the upstream `pointerEvents` warning from
    react-navigation/react-native-web remains (not user code).
  - Meal Log previous/next-day arrows with `next-day` disabled on today.
- Iteration 5 (nutrient data & daily budget tracker): 15/15 backend + 7/7 frontend ✅
  - All 35 foods now carry IFCT-2017 sourced `portion_g / potassium_mg /
    phosphorus_mg / sodium_mg / protein_g / fluid_ml`.
  - Content fixes: Orange tip factual (moderately high, not dangerous);
    Idli tip attributes sodium to added salt / sambar (not fermentation);
    smart-swap `clinical_benefit_explanation` strings COMPUTED from actual
    IFCT deltas at seed time — no more hard-coded percentages.
  - New endpoint `GET /api/meal-logs/summary?date=` returns `totals + limits`
    (defaults K 2000mg, P 1000mg, Na 2000mg).
  - Weekly report includes `avg_daily` + `limits`; PDF export includes
    "Average daily nutrients" table.
  - Meal Log screen replaces tier-count pills with 3 `NutrientBar` progress
    bars (green→yellow→red at 60%/90% thresholds). Tier badges remain on items.
  - Food detail shows a per-portion nutrient table (fluid cell hidden for
    solids). Weekly report screen adds an avg-nutrient card.
- Iteration 6 (health profile extension + AI patient context): 16/16 backend + full frontend ✅
  - `UserOut` extended with `diabetic:bool` and `doctor_limits:{K?,P?,Na?,fluid?}|null`.
  - New `PATCH /api/auth/profile` (partial) with `model_fields_set` semantics:
    absent = no-op, `null` = explicit clear, empty-object = clear.
  - Stage-based default limits: dialysis {K:2000,P:1000,Na:2000},
    pre-dialysis / unknown {K:2400,P:1200,Na:2300}. Doctor-set values win
    per-field, with unspecified fields falling back to defaults. Used by both
    `/meal-logs/summary` and `/reports/weekly`.
  - `personal_tier_for()` now also SOFTENS: pre_dialysis + YELLOW +
    POTASSIUM → GREEN, with a KDOQI-2020 individualized-guidance note
    surfaced via new `personalized_note` field. Sodium & phosphorus items
    are NEVER softened.
  - Ask AI accepts `lang` and builds a "PATIENT CONTEXT" system-prompt block
    (stage, diabetic flag, doctor/default limits, today's nutrient totals);
    when `lang=hi` the model is instructed to reply in Hindi Devanagari.
  - Frontend: 3-step onboarding (stage → diabetic → optional doctor limits
    with skip), Settings health-profile card (stage pills, diabetic switch,
    editable K/P/Na limits + Save + Using-defaults reset), Food detail
    surfaces `personalized-note` and a stage-neutral "Softened/Tightened
    for your stage" chip, Ask AI passes the current UI language.
- Iteration 7 (spot-fix confirmation): 6/6 backend + 3/3 frontend ✅
  - `{"doctor_limits":null}` now correctly clears via `model_fields_set`.
  - Food detail chip is stage-neutral and dynamic.
  - Stale limit assertions in `test_nutrient_budget.py` updated to new
    2400/1200/2300 defaults for unknown-stage users.
