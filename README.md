# Indian Renal Diet

A patient-facing mobile app that helps people living with **CKD** and on **dialysis** (and their family caregivers) navigate everyday Indian food safely.

- Search **35 seeded Indian foods** with GREEN / YELLOW / RED safety tiers, real IFCT-2017 nutrient values, and one-tap **kidney-friendly swaps** for risky dishes.
- Personalised by CKD stage (dialysis tightens YELLOW→RED; pre-dialysis softens YELLOW potassium foods with a KDOQI-style note), diabetic flag, and doctor-set daily K / P / Na limits.
- **Daily budget tracker** with potassium / phosphorus / sodium progress bars against your daily limits.
- **Weekly PDF report** you can share with your nephrologist between visits.
- **Ask AI** coach (Claude Sonnet 4.5) grounded in the app's own food database so it never contradicts the food cards, with English + Hindi answers.
- **Camera Food Scan** — take a photo of a dish; the vision model identifies it and, when it matches a seeded food, the app **overrides the AI verdict with the authoritative DB values** so scan and search always agree.
- Fully **bilingual** UI (English + हिन्दी) with high-contrast, large-text design for elderly patients.

## Stack

- **Frontend** — Expo SDK 54 + expo-router (typed routes), React Native for iOS / Android / Web, `expo-camera`, `expo-image-manipulator`, `expo-print`, `expo-sharing`, `expo-secure-store`, `react-native-keyboard-controller`, `react-native-safe-area-context`, `@expo/vector-icons`.
- **Backend** — FastAPI on Uvicorn, MongoDB via `motor`, `passlib[bcrypt]` + `python-jose` for JWT auth, `slowapi` for rate limiting, `emergentintegrations` for Claude Sonnet 4.5 text + vision via the Emergent LLM key.

## Repository layout

```
/app
├── backend/
│   ├── server.py           # FastAPI app (all /api/* endpoints)
│   ├── seed_data.py        # 35 foods + 10 smart swaps with IFCT-2017 nutrients
│   ├── requirements.txt
│   └── .env                # MONGO_URL, DB_NAME, JWT_SECRET, EMERGENT_LLM_KEY, CORS_ORIGINS
├── frontend/
│   ├── app/                # expo-router file-based routes
│   │   ├── _layout.tsx
│   │   ├── index.tsx       # redirect: login → disclaimer → onboarding → tabs
│   │   ├── (auth)/         # login, register
│   │   ├── (app)/          # tab layout + Search / Scan / Meals / Ask AI / Settings
│   │   ├── food/[id].tsx   # food detail + smart swap + nutrient table
│   │   ├── disclaimer.tsx  # first-run medical consent
│   │   ├── onboarding.tsx  # 3-step: stage → diabetic → doctor limits
│   │   └── report.tsx      # weekly PDF report
│   ├── src/
│   │   ├── components/     # SafetyCard, SmartSwapCard, NutrientBar, SafetyBadge
│   │   ├── lib/            # api client, auth-context, language-context, i18n
│   │   ├── hooks/          # use-icon-fonts
│   │   └── utils/storage/  # AsyncStorage / SecureStore wrapper
│   ├── app.json
│   └── .env                # EXPO_PACKAGER_*, EXPO_PUBLIC_BACKEND_URL
└── memory/
    ├── PRD.md
    └── test_credentials.md
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20+ with `yarn`
- A running MongoDB instance (local `mongod` or a hosted URI)
- Emergent LLM key for Claude Sonnet 4.5 text + vision

### 1. Backend

```bash
cd /app/backend
pip install -r requirements.txt

# Configure environment (see "Environment variables" below)
cp .env.example .env   # then edit values

# Start the API (bind to 0.0.0.0:8001 so the Expo app can reach it)
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Foods and smart swaps are **idempotently seeded** on every startup (upsert on `id`) so restarting the server is safe.

### 2. Frontend (Expo)

```bash
cd /app/frontend
yarn install

# Configure EXPO_PUBLIC_BACKEND_URL in .env, then:
yarn expo start
```

You can open the app on:
- **iOS / Android** — scan the QR code in Expo Go
- **Web** — open the URL Metro prints
- **A production build** — via the Emergent "Publish" button (top-right) to generate iOS / Android builds

## Environment variables

### `/app/backend/.env`

| Variable            | Required | Example                                                          | Purpose |
|---------------------|:--------:|------------------------------------------------------------------|---------|
| `MONGO_URL`         |    ✓     | `mongodb://localhost:27017`                                      | MongoDB connection string. |
| `DB_NAME`           |    ✓     | `renal_diet_db`                                                  | Database name — collections auto-created on startup. |
| `JWT_SECRET`        |    ✓     | a long random hex string                                         | HMAC secret for signing JWTs. Must be stable across restarts. |
| `EMERGENT_LLM_KEY`  |    ✓     | `sk-emergent-…`                                                  | Emergent Universal LLM key used for Claude Sonnet 4.5 (text + vision). |
| `CORS_ORIGINS`      |    ✓     | `https://your-app.example.com,http://localhost:3000`             | Comma-separated allow-list. `*` is deliberately not accepted alongside credentials. |

### `/app/frontend/.env` (managed values — do not edit unless you know what you're doing)

| Variable                    | Purpose |
|-----------------------------|---------|
| `EXPO_PACKAGER_PROXY_URL`   | Set by the platform — how Expo Go connects to Metro over the preview tunnel. |
| `EXPO_PACKAGER_HOSTNAME`    | Set by the platform. |
| `EXPO_PUBLIC_BACKEND_URL`   | Public origin of the FastAPI backend (all requests append `/api/...`). |

## Key API endpoints (all prefixed with `/api`)

- **Auth** — `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/stage`, `PATCH /auth/profile`
- **Foods** — `GET /foods?q=&tier=&favorites_only=`, `GET /foods/{id}`
- **Favorites** — `POST /favorites/{food_id}` (toggle)
- **Meal log** — `GET/POST /meal-logs`, `DELETE /meal-logs/{id}`, `GET /meal-logs/summary?date=`
- **Reports** — `GET /reports/weekly`
- **AI** — `POST /ai/ask` (grounded in the food DB, honours `lang: "en"|"hi"`), `POST /scan/food` (vision; overrides tier/tip with DB values on match)

Rate-limited via `slowapi`: register/login 5/min per IP, `/ai/ask` 10/min per user, `/scan/food` 5/min per user.

## Testing

```bash
# Backend
cd /app/backend
pytest -q

# Frontend lint
cd /app/frontend
yarn lint
```

## Medical Disclaimer

**This app is an educational tool. It is not medical advice, diagnosis, or treatment.**

Food safety colors (GREEN / YELLOW / RED) are general guidance for CKD and dialysis patients — not a substitute for your care team's advice. Always follow the personal potassium, phosphorus, sodium and fluid targets your **nephrologist** has set for you. The AI food scanner and Ask-AI answers may be inaccurate; do not act on them without confirming with your care team.

If you experience swelling, breathlessness, muscle weakness, irregular heartbeat, or any acute symptom, contact your doctor or emergency services immediately.
