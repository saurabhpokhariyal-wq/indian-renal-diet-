#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Extend the Indian Renal Diet app with:
  (1) Barcode scanning for packaged Indian foods using Open Food Facts (authoritative DB override
      logic same as Vision Scan). Frontend uses expo-camera barcode scanner and calls
      POST /api/scan/barcode. Falls back with friendly not-found message.
  (2) Multi-language expansion: add Tamil (ta), Bengali (bn), Marathi (mr) in addition to English
      and Hindi. Language picker in Settings must expose all 5.

backend:
  - task: "Barcode scan endpoint /api/scan/barcode already implemented — verify still working"
    implemented: true
    working: "NA"
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Endpoint /api/scan/barcode built in earlier iteration; auth required, calls Open Food Facts and merges nutrients into FoodScan response with authoritative override when name matches seed DB. Please re-verify with a real Indian pack barcode e.g. 8901058851557 (Maggi) or 8901491101653."

frontend:
  - task: "Scan screen: two-mode toggle (Food photo / Barcode)"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/scan.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Added mode chips 'scan-mode-vision' and 'scan-mode-barcode'. Barcode mode uses CameraView with barcodeScannerSettings and onBarcodeScanned, calls api.scanBarcode. Result rendered in same ScanResultCard with brand line."

  - task: "Settings: expanded 5-language picker (en, hi, ta, bn, mr)"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/settings.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Iterates SUPPORTED_LANGS from i18n.ts and shows a wrap-flow of language buttons with native-script labels via langLabel(). Persists via language-context which now accepts all supported languages."

metadata:
  created_by: "main_agent"
  version: "1.1"
  test_sequence: 9
  run_ui: true

test_plan:
  current_focus:
    - "Scan screen: two-mode toggle (Food photo / Barcode)"
    - "Settings: expanded 5-language picker (en, hi, ta, bn, mr)"
    - "Barcode scan endpoint /api/scan/barcode already implemented — verify still working"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Please verify:
      Backend:
       - POST /api/scan/barcode with a real barcode (try "8901058851557" or "3017620422003" Nutella)
         after login as demo@renal.app / demo123. Should return safety_tier + food_name + brand.
       - Confirm 404 with "Product not found" for random 12-digit like "000000000000".
       - Rate limit (15/min) still applies.
      Frontend:
       - Log in as demo user, go to Scan tab. Confirm 'scan-mode-vision' and 'scan-mode-barcode'
         chips render and toggle correctly (only one active at a time).
       - Vision mode: shutter still works. Barcode mode on web shows a placeholder message.
       - Settings tab: language section shows 5 buttons (lang-en, lang-hi, lang-ta, lang-bn, lang-mr)
         each with native-script label. Tapping switches language and persists across reload.
       - No regressions: existing Search / Meals / Ask AI / Weekly report / Favorites still work.

# ----------- Iteration 10: nutrient bars on barcode scans + favorite/log actions -----------
backend:
  - task: "Barcode scan endpoint now persists non-matched packs to db.foods for favorites/logging"
    implemented: true
    working: "NA"
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          scan_barcode() now upserts a food doc with id=bc_{barcode}, source='barcode',
          brand and combined display name whenever no seed match is found. Idempotent by barcode.
          Response's matched_food_id is now always set on success. FoodOut extended with
          optional brand and source fields (nullable).

frontend:
  - task: "Barcode scan result: nutrient bars against daily budget + Log this pack + Favorite"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/scan.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Barcode result now shows:
          - PackNutrientPanel with 3 NutrientBar (K, P, Na) rendering per-pack values vs user's
            daily limits (fetched once via api.getMealSummary on mount).
          - testID 'pack-log' (Log this pack) - calls api.addMealLog(matched_food_id, today, 'snack')
          - testID 'pack-favorite' (star toggle) - calls api.toggleFavorite(matched_food_id)
          - testID 'barcode-rescan' (secondary style)
          - testID 'pack-logged-flash' shows a green check pill after successful log
          Favorites tab / Meal-log list automatically pick up the barcode food via existing endpoints.

test_plan:
  current_focus:
    - "Barcode scan endpoint now persists non-matched packs to db.foods for favorites/logging"
    - "Barcode scan result: nutrient bars against daily budget + Log this pack + Favorite"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Iteration 10 adds (a) per-pack nutrient bars vs daily budget and (b) 'Log this pack' +
      Favorite toggle on the barcode scan result. Please verify:
       Backend:
        - POST /api/scan/barcode with 3017620422003 (Nutella) -> matched_food_id must be
          non-null and start with 'bc_' (not a seed food id).
        - After the scan, GET /api/foods/{that_id} should succeed and return the same product
          with source='barcode' and brand populated.
        - POST /api/meal-logs {"food_id": "bc_3017620422003", "date":<today>, "meal_type":"snack"}
          should succeed and appear in GET /api/meal-logs?date=<today>.
        - POST /api/favorites/bc_3017620422003 should toggle correctly (twice = removed).
        - GET /api/foods?favorites_only=true should list it after favoriting.
        - Scanning the same barcode again should NOT create a duplicate food (idempotent).
       Frontend (Playwright web):
        - Login as demo@renal.app / demo123, go to Scan tab, toggle Barcode mode.
        - Web still shows the placeholder (expected). Skip actual scan in Playwright but
          please make sure the mode-toggle chips still work and no runtime error occurs.

# ----------- Iteration 11: Home dashboard replaces Search as post-login landing -----------
frontend:
  - task: "Home dashboard as post-login landing with 6 large menu cards"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/index.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Renamed original /(app)/index.tsx -> /(app)/search.tsx (no logic change, just filename).
          New /(app)/index.tsx implements a Home dashboard with 6 cards routing to search, scan,
          meal-log, /report, ask-ai, settings. TestIDs: home-menu-{search,scan,meals,report,ai,settings}.
          Greeting is "user-greeting". Cards use the elderly-friendly large touch target style
          (min-height 150, 47% flex-basis grid).

  - task: "Tab layout: 5 tabs (Home/Search/Scan/Meals/Ask AI), Settings hidden but routable"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/_layout.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Rewrote _layout.tsx to declare index (Home), search, scan, meal-log, ask-ai as tabs.
          Settings is still a registered Tabs.Screen with href: null so navigating to
          /(app)/settings from the Home menu still works.

  - task: "i18n keys for Home dashboard"
    implemented: true
    working: "NA"
    file: "frontend/src/lib/i18n.ts"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Added: tabHome, menuTitle, menuScan, menuReport, menuSearchSub, menuScanSub,
          menuMealsSub, menuReportSub, menuAISub, menuSettingsSub — placed right after tabSettings.
          Tamil/Bengali/Marathi intentionally use English fallbacks for the new subtitle strings.

test_plan:
  current_focus:
    - "Home dashboard as post-login landing with 6 large menu cards"
    - "Tab layout: 5 tabs (Home/Search/Scan/Meals/Ask AI), Settings hidden but routable"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Iteration 11 changes the post-login landing from Search to a Home dashboard. Please verify
      per the acceptance checklist. NOTE: existing frontend E2E flows that previously landed on
      the Search screen after login must now first tap `home-menu-search` (or the "Search" tab)
      before interacting with `search-input`. No backend changes in this iteration.

      Checklist to run:
        1. Login → lands on Home; testID `user-greeting` visible; six testIDs
           home-menu-{search,scan,meals,report,ai,settings} render.
        2. Tap each of the six cards and confirm correct navigation (search screen shows the
           existing search-input, scan shows scan-mode-vision, meals shows meal-log-list,
           report shows the weekly report header, ask-ai shows the AI chat, settings shows
           testID settings-user-name).
        3. From /report tap Back and confirm we're on Home again (not gone off the stack).
        4. Bottom tab bar shows exactly five tabs: Home, Search, Scan, Meals, Ask AI.
        5. Language change from Settings still works — switching to Hindi should translate
           the greeting header, menu title and card titles/subtitles that have hi variants.
           Switching to Tamil should show English fallbacks for the sub-strings without crash.
        6. Regression: existing search-input, favorites-row, tier-chips, meal-log, report,
           barcode scan pack-log flows still function.

# ----------- Iteration 12: 992 INDB foods + serving_disclaimer field -----------
backend:
  - task: "Load 992 INDB foods alongside 35 curated foods; seed 1027 total"
    implemented: true
    working: true
    file: "backend/server.py, backend/seed_data_indb.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: |
          Added seed_data_indb.py (unchanged from source, 992 dishes, 223 with serving_disclaimer).
          server.py now imports SEED_FOODS_INDB and the lifespan startup upserts both lists.
          Confirmed startup log line: 'Seeded 1027 foods, 10 swaps'.
          Zero id overlap between curated and INDB confirmed via set diff.
          Curated foods (e.g. food-lauki-sabzi) untouched and retain original clinical_tip.
      - working: true
        agent: "main"
        comment: |
          FoodOut extended with optional serving_disclaimer; enrich_food_sync now passes
          food.get('serving_disclaimer'). Verified 'Rasam with lemon' returns the disclaimer and
          'Lauki Sabzi' returns null.

frontend:
  - task: "Serving disclaimer caution box on food detail screen"
    implemented: true
    working: true
    file: "frontend/app/food/[id].tsx, frontend/src/lib/api.ts"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: |
          Added yellow caution box with alert-circle icon + testID 'serving-disclaimer' between
          Portion Limit and Clinical Tip. Uses existing COLORS.yellowBg / yellowBorder / yellowText.
          FoodOut TS type updated with optional serving_disclaimer.
          Playwright screenshot confirms the box renders correctly for 'Rasam with lemon' and does
          NOT render when the field is absent (verified for Lauki Sabzi manually earlier).

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Iteration 12 delivered — 1027 seeded foods and the new serving_disclaimer field are wired
      through backend + frontend. Please verify:
       Backend:
        - GET /api/foods returns total >= 1027 (may be higher due to prior barcode-scanned entries).
        - GET /api/foods/food-rasam-with-lemon returns non-null serving_disclaimer.
        - GET /api/foods/food-lauki-sabzi returns null serving_disclaimer AND its original tip.
        - Search still works: q='rasam' returns Rasam with lemon; q='palak' returns Palak Paneer.
        - Meal-log POST/GET, favorites toggle, weekly report still function with the larger DB.
       Frontend:
        - Login, tap home-menu-search, search 'Rasam with lemon', tap the safety-card.
          Verify testID 'serving-disclaimer' visible.
        - Search 'Lauki Sabzi', tap it. Verify serving-disclaimer NOT rendered, no empty box.
        - No console errors.

# ----------- Iteration 13: Seed-time reconciliation + audit script -----------
backend:
  - task: "Reconciliation pipeline: bucket rescale + reclassify + curated overrides + dedupe + sanity ceiling"
    implemented: true
    working: "NA"
    file: "backend/reconciliation.py, backend/server.py, backend/scripts/audit_seed.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          New /app/backend/reconciliation.py exposes reconcile_seed() called from the lifespan
          startup. It applies (in order):
            Step 1 bucket classification (spice/condiment/soup/sweet/beverage, priority-ordered,
                   evaluated against ORIGINAL values only)
            Step 2 nutrient rescale per bucket (spice÷30 @5g, condiment÷10 @15g, soup÷5 @30g,
                   sweet÷4.3 @35g, beverage×1.5 @225ml)
            Step 3 reclassify safety_tier via _classify_from_nutrients (except tier_override)
            Step 4 curated clinical overrides applied to 7 entries with override_reason strings
            Step 5 auto_rescaled: True stamped on rescaled entries
            Step 6 dedupe by lowercase name (curated first-wins); 9 duplicates dropped, logged
            Step 7 sanity ceiling K>800/P>400/Na>1000 for solid foods <=150g → written to
                   /app/backend/needs_manual_review.csv (42 rows this run) instead of silently
                   left in place.
          FoodOut extended with optional tier_override, override_reason, auto_rescaled.
          Startup log confirms: input=1027 reclassified=421 rescaled=451 dupes=9 sanity_flags=42
          overrides=7. Total DB rows after dedupe: 1018 (+ prior barcode-scanned rows).
          The 4 patient-unsafe SEVERE_TIER_MISMATCH cases are now correctly RED:
            food-soya-chunks-sweet-and-sour, food-raw-mango-chutney (now GREEN after 15g rescale — Na=72),
            food-mayonnaise (RED SODIUM), food-cold-tomato-soup (RED SODIUM).

  - task: "Standalone audit script /app/backend/scripts/audit_seed.py"
    implemented: true
    working: "NA"
    file: "backend/scripts/audit_seed.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Runs the same pipeline against raw seed files without touching MongoDB. Reports counts
          + samples for reclassified, rescaled_by_bucket, duplicates_dropped, sanity_violations,
          and portion_limit_text vs disclaimer conflicts. Zero conflicts remaining. Supports
          --json and --fail-on-flags flags for CI wiring.

frontend:
  - task: "FoodOut type updated with new optional fields"
    implemented: true
    working: "NA"
    file: "frontend/src/lib/api.ts"
    stuck_count: 0
    priority: "low"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: Added tier_override, override_reason, auto_rescaled to FoodOut. Not surfaced in UI yet; kept as data-only additions.

test_plan:
  current_focus:
    - "Reconciliation pipeline: bucket rescale + reclassify + curated overrides + dedupe + sanity ceiling"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      Iteration 13 delivers seed-time data reconciliation matching the CSV audit exactly.
      Backend regression + acceptance-criteria testing needed. Frontend changes are TYPE-only
      (FoodOut interface); please just check that existing screens still render (search,
      detail, meals, favorites, scan).

      Acceptance criteria to verify:
       1. GET /api/foods/food-soya-chunks-sweet-and-sour → safety_tier == "RED", risk == "SODIUM"
       2. GET /api/foods/food-cold-tomato-soup → safety_tier == "RED", risk == "SODIUM"
       3. GET /api/foods/food-mayonnaise → safety_tier == "RED", risk == "SODIUM"
       4. GET /api/foods/food-raw-mango-chutney → auto_rescaled == True, portion_g == 15,
          portion_limit_text contains "15 g" (rescaled → no longer patient-unsafe at real portion)
       5. GET /api/foods/food-chat-masala → auto_rescaled == True, portion_g == 5, safety_tier == "RED"
       6. GET /api/foods/food-cheese-soup → auto_rescaled == True, portion_g == 30, serving_disclaimer
          mentions "concentrated base" or "manual re-sourcing"
       7. GET /api/foods/food-toor-dal → tier_override == True, safety_tier == "YELLOW" preserved
       8. GET /api/foods/food-orange → tier_override == True, safety_tier == "RED" preserved
       9. GET /api/foods/food-brown-rice → tier_override == True, override_reason non-empty
      10. GET /api/foods count total >= 1018 (may be higher due to prior barcode scans, but not lower)
      11. Duplicate ids food-cabbage-rolls-2, food-white-sauce-2, food-white-sauce-3,
          food-caramel-custard-2, food-shepherd-s-pie-2, food-stuffed-bittergourd-2,
          food-chicken-sandwich-2, food-cheese-and-tomato-sandwich-2, food-fruit-punch-2
          should NOT be present in GET /api/foods (dedupe dropped them).
      12. python /app/backend/scripts/audit_seed.py --fail-on-flags → exit 1 currently (42 sanity
          flags remain, which is expected — the review CSV exists at
          /app/backend/needs_manual_review.csv). Please verify the CSV was written and has
          exactly 42 rows plus a header.
      13. Regression: barcode scan, meal log, favorites, weekly report all still work.

# ---------------- Iteration 17 (Proteins & Grains Guides) ----------------

backend_iter17:
  - task: "GET /api/proteins/guide returns curated protein guide (GREEN/YELLOW/RED)"
    implemented: true
    working: "NA"
    file: "backend/server.py, backend/protein_guide.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          New endpoint mirroring /api/snacks/guide. Should return JSON with keys GREEN,
          YELLOW, RED each having title, subtitle, and a "proteins" array of entries
          (name, hindi, serving, potassium_mg, note, linked_food_id).
  - task: "GET /api/grains/guide returns curated grains guide (GREEN/YELLOW/RED)"
    implemented: true
    working: "NA"
    file: "backend/server.py, backend/grain_guide.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          New endpoint. Should return JSON with keys GREEN, YELLOW, RED each having
          title, subtitle, and a "grains" array of entries.

frontend_iter17:
  - task: "Proteins Guide screen (/proteins) renders GREEN/YELLOW/RED sections"
    implemented: true
    working: "NA"
    file: "frontend/app/proteins.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: New screen matching snacks.tsx pattern. Uses api.getProteinGuide.
  - task: "Grains Guide screen (/grains) renders GREEN/YELLOW/RED sections"
    implemented: true
    working: "NA"
    file: "frontend/app/grains.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: New screen. Uses api.getGrainGuide.
  - task: "Home dashboard shows Proteins Guide and Grains Guide cards that route correctly"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/index.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: Two new menu cards inserted after Snacks — icons egg/pizza, href /proteins and /grains.

test_plan_iter17:
  current_focus:
    - "New proteins/grains backend endpoints"
    - "New proteins/grains guide screens"
    - "Home dashboard routes to /proteins and /grains"
    - "Regression: fruits, beverages, vegetables, snacks guides still work"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

# ---------------- Iteration 18 (FoodGuideLayout refactor) ----------------

frontend_iter18:
  - task: "Refactor 6 guide screens to use shared FoodGuideLayout component"
    implemented: true
    working: "NA"
    file: "frontend/src/components/FoodGuideLayout.tsx, frontend/app/{fruits,beverages,vegetables,snacks,proteins,grains}.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Created FoodGuideLayout (src/components) and rewrote all six guide screens as tiny
          10-line wrappers. TestID prefixes normalized to singular:
            fruits    -> fruit-section-*, fruit-row-*
            beverages -> beverage-section-*, beverage-row-*   (was bev-row-*)
            vegetables-> vegetable-section-*, vegetable-row-* (was veg-*)
            snacks    -> snack-section-*, snack-row-*
            proteins  -> protein-section-*, protein-row-*
            grains    -> grain-section-*, grain-row-*
          Back-button testIDs remain plural (fruits-back, beverages-back, etc).
          Beverages uses showFluidChip + introTheme="aiBlue"; all others use brand green intro.
          NO behavioural changes intended - pure refactor. All 6 screens should render identically.
test_plan_iter18:
  current_focus:
    - "All six guide screens still render (fruits, beverages, vegetables, snacks, proteins, grains)"
    - "Beverages shows fluid_ml chip; the other five do not"
    - "TestID prefixes work with new singular scheme (fruit-, beverage-, vegetable-, snack-, protein-, grain-)"
    - "Tapping any linked row still navigates to /food/{id}"
    - "Home dashboard cards still route correctly"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

# ---------------- Iteration 19 (Nutrient unit: mg / mEq) ----------------

backend_iter19:
  - task: "User model gets nutrient_unit (mg default, mEq optional). PATCH /api/auth/profile accepts it. GET /api/auth/me returns it. AI grounded/context blocks include both mg + mEq for K and Na."
    implemented: true
    working: "NA"
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Added `nutrient_unit: Literal["mg","mEq"] = "mg"` to UserOut/ProfileUpdate.
          _user_to_out returns it (falls back to "mg" for legacy users).
          _build_ai_context now emits `K 158 mg (4.0 mEq)` style dual-unit strings
          in daily limits + today's intake + grounded food data.

frontend_iter19:
  - task: "Global mg/mEq toggle available in Settings; persists via profile PATCH."
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/settings.tsx, frontend/src/lib/units.ts"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "FoodGuideLayout displays K in user's chosen unit."
    implemented: true
    working: "NA"
    file: "frontend/src/components/FoodGuideLayout.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "Food detail (K, Na cells) respects unit; Phosphorus stays mg."
    implemented: true
    working: "NA"
    file: "frontend/app/food/[id].tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "Meal-log NutrientBars for K and Na respect unit; Phosphorus stays mg. Progress percentages remain correct."
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/meal-log.tsx, frontend/src/components/NutrientBar.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "Scan (barcode) pack panel NutrientBars respect unit for K and Na."
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/scan.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "Weekly report on-screen NutrientBars respect unit; PDF table always shows both mg and mEq for K and Na."
    implemented: true
    working: "NA"
    file: "frontend/app/report.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "Doctor-limit inputs in Settings adapt to selected unit; values convert canonically to mg before save; decimals allowed in mEq mode."
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/settings.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true

test_plan_iter19:
  current_focus:
    - "User can toggle mg <-> mEq in Settings; preference persists to backend"
    - "K and Na numbers everywhere flip units correctly"
    - "Doctor-limits round-trip: enter 51 mEq → saved as ~2000 mg → re-read as 51.2 mEq"
    - "Phosphorus stays mg everywhere"
    - "AI answers include both units in patient context"
    - "Weekly PDF report shows both mg and mEq for K/Na"
    - "No regression on: food search, food detail load, meal log CRUD, favorites, scan"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

# ---------------- Iteration 20 (Guide enrichment: mEq + sodium badge + new entries) ----------------

backend_iter20:
  - task: "guide_utils.py enriches every guide entry with potassium_meq (mg/39.1, 1dp) and high_sodium (sodium_mg >= 400)"
    implemented: true
    working: "NA"
    file: "backend/guide_utils.py, backend/{fruit,vegetable,snack,beverage,protein,grain}_guide.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Every get_*_guide() now runs through enrich_guide(). potassium_mg remains
          source of truth. potassium_meq is derived at load time and never hand-
          entered. sodium_mg defaults to null for entries where a real number
          isn't sourced yet — no formulaic backfill.
  - task: "Ten new researched entries added across 5 guide files"
    implemented: true
    working: "NA"
    file: "backend/{vegetable,fruit,protein,beverage,snack}_guide.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          vegetable: Bitter Gourd (280mg, Na=None), Raw Banana (400mg, Na=None) — YELLOW
          fruit: Muskmelon (400mg, Na=24) — YELLOW
          protein: Egg Yolk alone (19mg, Na=8) — RED (phosphorus concern)
          beverage: Almond Milk (67mg, Na=60) — GREEN; Jaljeera (150mg, Na=600), Aam Panna (150mg, Na=800) — YELLOW; Thandai (425mg, Na=109) — RED
          snack: Dhokla (240mg, Na=310) — YELLOW; Pani Puri (250mg, Na=450), Banana Chips (140mg, Na=None) — YELLOW
  - task: "guide_needs_sourcing.csv generated at startup — 7 flagged dishes + all sodium-missing entries"
    implemented: true
    working: "NA"
    file: "backend/server.py lifespan + backend/guide_utils.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true

frontend_iter20:
  - task: "Guide rows show BOTH mg and mEq for potassium regardless of user's toggle. Order flips based on toggle preference."
    implemented: true
    working: "NA"
    file: "frontend/src/components/FoodGuideLayout.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Format is "K 150 mg / 3.8 mEq" (mg mode) or "K 3.8 mEq / 150 mg" (mEq mode).
          Both figures always visible per user request; toggle only affects order.
  - task: "High Sodium warning badge renders on any entry with high_sodium=true, independent of tier"
    implemented: true
    working: "NA"
    file: "frontend/src/components/FoodGuideLayout.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Small red pill badge with warning icon: "High Sodium — 600 mg per serving".
          Visible on Jaljeera and Aam Panna (YELLOW tier), correctly appears on any
          entry with sodium_mg >= 400. Uses testID pattern `${rowTestId}-high-sodium`.

test_plan_iter20:
  current_focus:
    - "All /api/{fruits,vegetables,snacks,beverages,proteins,grains}/guide responses include potassium_meq (rounded 1dp) and high_sodium (bool) on every entry."
    - "potassium_meq = round(potassium_mg / 39.1, 1) — spot-check a few (Egg White boiled: 110→2.8, Water: 0→0.0, Coconut Water: 500→12.8)."
    - "sodium_mg == null on entries where we didn't source a value; new entries with values have them (Jaljeera 600, Aam Panna 800, Dhokla 310, Pani Puri 450, Thandai 109, Almond Milk 60, Muskmelon 24, Egg Yolk 8)."
    - "high_sodium == true when sodium_mg >= 400 (Jaljeera, Aam Panna, Pani Puri) — false otherwise even for Thandai (109) and Dhokla (310)."
    - "guide_needs_sourcing.csv exists at /app/backend/guide_needs_sourcing.csv with the 7 flagged dishes (Vada Pav, Misal Pav, Sattu Sharbat, Sol Kadhi, Momos, Bhel Puri, Sev Puri) plus rows for every entry missing sodium_mg."
    - "Frontend: /beverages Jaljeera row shows 'K 150 mg / 3.8 mEq' AND a red 'High Sodium — 600 mg per serving' badge."
    - "Frontend: /snacks Pani Puri row shows 'K 250 mg / 6.4 mEq' AND a red 'High Sodium — 450 mg per serving' badge."
    - "Frontend: /proteins Egg Yolk (alone) entry appears in RED tier with 'K 19 mg / 0.5 mEq' (NO sodium badge — sodium is 8mg)."
    - "Frontend: With user toggled to mEq (Settings → mEq), guide rows flip to 'K 3.8 mEq / 150 mg' style (mEq first)."
    - "Regression: all 6 guide screens still render, tap navigation still works, home dashboard still routes correctly."
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

# ---------------- Iteration 21 (IFCT 2017 corrections + new entries) ----------------

backend_iter21:
  - task: "Egg Yolk (alone) updated to IFCT M006 values"
    implemented: true
    working: "NA"
    file: "backend/protein_guide.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          K 18mg (was 19), P 100mg (new), Na 8mg, source="IFCT 2017, code M006".
          Note updated to cite IFCT phosphorus figure (100mg per yolk).
  - task: "Whole Egg (boiled) enriched with P + Na fields (K unchanged)"
    implemented: true
    working: "NA"
    file: "backend/protein_guide.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
  - task: "Muskmelon corrected to IFCT E046 value (K 400→294)"
    implemented: true
    working: "NA"
    file: "backend/fruit_guide.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "New IFCT-sourced entries added: Radish + Water Chestnut (veg YELLOW); Fresh Fig (fruit GREEN); Ber (fruit YELLOW); Bael + Phalsa (fruit RED); Khoa (protein RED)"
    implemented: true
    working: "NA"
    file: "backend/vegetable_guide.py, backend/fruit_guide.py, backend/protein_guide.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "Guide file docstrings updated with sourcing convention + legume-methodology caveat"
    implemented: true
    working: "NA"
    file: "backend/protein_guide.py, backend/vegetable_guide.py, backend/fruit_guide.py"
    stuck_count: 0
    priority: "low"
    needs_retesting: true

frontend_iter21:
  - task: "GuideEntry type extended with optional source, phosphorus_mg fields"
    implemented: true
    working: "NA"
    file: "frontend/src/components/FoodGuideLayout.tsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
  - task: "Guide rows render a subtle 'Source: IFCT 2017, code XXX' caption when source field is present"
    implemented: true
    working: "NA"
    file: "frontend/src/components/FoodGuideLayout.tsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true

test_plan_iter21:
  current_focus:
    - "GET /api/proteins/guide RED has Egg Yolk with K=18, phosphorus_mg=100, sodium_mg=8, source contains 'M006'."
    - "GET /api/proteins/guide RED has Khoa with K=161, phosphorus_mg=143, sodium_mg=14, source contains 'L004'."
    - "GET /api/proteins/guide YELLOW has Whole Egg (boiled) with K=63, phosphorus_mg=105, sodium_mg=61, source contains 'M004'."
    - "GET /api/fruits/guide YELLOW has Muskmelon with K=294 (not 400), source contains 'E046'."
    - "GET /api/fruits/guide GREEN has Fig, fresh with K=116, source contains 'E020'."
    - "GET /api/fruits/guide YELLOW has Ber with K=237, source contains 'E068'."
    - "GET /api/fruits/guide RED has Bael with K=409, source contains 'E008'; and Phalsa with K=362, source contains 'E052'."
    - "GET /api/vegetables/guide YELLOW has Radish with K=287, source contains 'F012'; and Water Chestnut with K=382, source contains 'F016'."
    - "potassium_meq derived correctly on all new entries: Egg Yolk 0.5, Khoa 4.1, Muskmelon 7.5, Fig 3.0, Ber 6.1, Bael 10.5, Phalsa 9.3, Radish 7.3, Water Chestnut 9.8."
    - "high_sodium is False for all new entries (all sodium_mg < 400)."
    - "Frontend: /proteins Egg Yolk row shows subtle 'Source: IFCT 2017, code M006 (scaled to ~17 g)' caption below the note. TestID pattern ${rowTestId}-source."
    - "Frontend: /fruits Muskmelon row shows K 294 mg / 7.5 mEq and source caption."
    - "Regression: iter 20 high-sodium badges (Jaljeera, Aam Panna, Pani Puri) still render. Existing entries without source field do NOT render a Source: caption."
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

# ---------------- Iteration 22 (AI grounding fix + NL meal log + guide retrieval + multilingual stopwords) ----------------

backend_iter22:
  - task: "P0 BUG FIX: /ai/ask no longer silently ungrounds itself when no food matches"
    implemented: true
    working: "NA"
    file: "backend/server.py (AI_SYSTEM_PROMPT_BASE + _build_grounded_food_block)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          System prompt rewritten with an explicit GROUNDING RULE: only classify a
          food as SAFE/CAUTION/AVOID if it appears in the grounded block.
          _build_grounded_food_block now returns an explicit '(no matching food
          found ... do NOT invent a tier)' marker when both DB and guides miss,
          so the model sees a signal rather than an empty append. This is the
          reported live bug — MUST be verified end-to-end by the testing_agent
          before it can be considered fixed.
  - task: "Extend /ai/ask retrieval to 5+ guide files (option-b: sibling function, no data duplication)"
    implemented: true
    working: "NA"
    file: "backend/server.py (_find_relevant_guide_entries + updated _build_grounded_food_block)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "Multilingual stopwords + Tamil/Bengali script preserved in tokenizer"
    implemented: true
    working: "NA"
    file: "backend/server.py (_AI_STOPWORDS + _tokenize_question)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "New endpoint POST /api/ai/log-meal — retrieval-then-confirm meal parsing"
    implemented: true
    working: "NA"
    file: "backend/server.py (/ai/log-meal, ParsedMealItem, AiLogMealResponse)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          LLM only extracts {item_text, quantity_multiplier} pairs — never invents
          food IDs or nutrient numbers. Each extracted item runs through the
          existing _find_relevant_foods retrieval. Returns match_single |
          match_multiple | no_match per item. Endpoint NEVER writes to
          meal_logs — the frontend must render a confirmation screen and call
          POST /meal-logs per confirmed item.
  - task: "quantity_multiplier added to MealLogCreate/MealLogOut and applied at every summation site"
    implemented: true
    working: "NA"
    file: "backend/server.py (MealLogCreate, MealLogOut, create_meal_log, list_meal_logs, meal_log_summary, weekly_report, _build_ai_context)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Field: float default 1.0, validators gt=0 le=10. Multiplied into K/P/Na/protein/fluid
          totals in: meal_log_summary, weekly report avg, _build_ai_context daily intake.
          MealLogOut carries the value back so the frontend can display it.
          Legacy logs without the field default to 1.0 via .get(...,1.0).

frontend_iter22:
  - task: "New /log-meal-nl screen — describe meal in text, parse, confirm, commit"
    implemented: true
    working: "NA"
    file: "frontend/app/log-meal-nl.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "'Log by text' button added to meal-log screen header"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/meal-log.tsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true

test_plan_iter22:
  current_focus:
    - "PRIMARY (bug): POST /api/ai/ask with a made-up dish name like 'zorplok curry' should NOT return a confident SAFE/CAUTION/AVOID tier. Response should contain a variant of 'I don't have verified data for that food' (or the localized equivalent). The system prompt's grounding rule and the grounded-block no-match marker together must prevent the model from guessing."
    - "PRIMARY (bug regression): POST /api/ai/ask with a real food from db.foods (e.g. 'is potato safe for me?' with a demo user) should still return a grounded, tier-cited answer as before."
    - "Guide-only visibility: POST /api/ai/ask with 'is khoa safe?' or 'what about water chestnut?' should now return a grounded answer citing the guide entry — these foods have no linked_food_id in db.foods so they were previously invisible to /ai/ask."
    - "Tamil-language question: POST /api/ai/ask with lang='ta' and a question containing a known food name in Tamil script should retrieve the food. Verify at minimum that the tokenizer preserves Tamil unicode and that stopwords are stripped (see _tokenize_question)."
    - "POST /api/ai/log-meal with body {text:'2 rotis, 1 katori dal, small bowl of curd', date:'2026-08-16', meal_type:'lunch', lang:'en'} returns parsed_items array with 3 elements. Each has quantity_multiplier (roti=2 or 2.0, others =1.0), outcome ∈ {match_single,match_multiple,no_match}, and 0+ candidates (never nutrient totals)."
    - "The endpoint MUST NOT write to db.meal_logs. Verify by counting meal_logs before and after the call for the demo user — count should be identical."
    - "POST /api/meal-logs accepts quantity_multiplier: 2.0. GET /api/meal-logs echoes it. GET /api/meal-logs/summary shows K totals ~2x the food's stored K when qty=2."
    - "POST /api/meal-logs rejects quantity_multiplier: 0 (must be >0) and quantity_multiplier: 15 (must be <=10) with 422."
    - "GET /api/reports/weekly avg_daily nutrient totals scale with quantity_multiplier for aggregated logs."
    - "Regression: /api/foods/guide-*, /api/foods list, /api/auth still function normally."
    - "FRONTEND: /log-meal-nl screen accepts text, calls parseMealText, renders parsed items with candidate rows or 'not in database' pills, allows +/- quantity, then commits via addMealLog per confirmed item and navigates back to /meal-log."
    - "FRONTEND: /meal-log screen shows a 'Log by text' primary button that opens /log-meal-nl."
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

# ---------------- Iteration 23 (Sajina rescale + category mislabel bugfix + audit check) ----------------

backend_iter23:
  - task: "food-sajina rescaled from 150g stored to 40g reference portion"
    implemented: true
    working: "NA"
    file: "backend/seed_data_indb.py (patched via scripts/patch_iter23.py)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          K 874→233, P 375→100, Na 18→5, protein 16.2→4.3, portion_g 150→40.
          safety_tier auto-recomputed by reclassify_tier() — do NOT hand-check,
          the formula picked YELLOW from the new numbers (dropped from RED as
          the user predicted).
  - task: "Category mislabel fix: 24 formerly-beverage-tagged solid dishes recategorized; 2 legitimate liquids (chicken-stock, egg-nog) explicitly kept as beverage"
    implemented: true
    working: "NA"
    file: "backend/seed_data_indb.py, backend/category_review.csv"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Every decision logged in backend/category_review.csv (audit trail). Reconciliation
          pipeline now regenerates portion_limit_text + serving_disclaimer + fluid_ml from
          the corrected category — we do NOT hand-edit those derived fields.
  - task: "Pipeline: always regenerate portion_limit_text on rescale; regenerate serving_disclaimer when stored value matches a known auto-generated template"
    implemented: true
    working: "NA"
    file: "backend/reconciliation.py (rescale_food + _STALE_DISCLAIMER_MARKERS)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Fixes the "stale bucket disclaimer preserved across category changes" gap.
          Hand-authored curated disclaimers (e.g. sajina's, tier_override entries)
          don't match any auto-template marker and are preserved unchanged.
  - task: "Pipeline: solids-cannot-be-fluids normalizer strips fluid_ml on any non-beverage entry"
    implemented: true
    working: "NA"
    file: "backend/reconciliation.py (Step 2b sanity pass in reconcile_seed)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Catches the exact bug the user hit: a sandwich tagged beverage carried
          fluid_ml=150, and after category correction it still didn't hit any
          rescale bucket. Now: if category != beverage and fluid_ml > 0, strip
          fluid_ml and (if disclaimer also looks auto-generated) reset it to
          'Values shown per stored portion.'
  - task: "audit_seed.py gains a permanent category-plausibility check across beverage/snack/condiment name patterns"
    implemented: true
    working: "NA"
    file: "backend/scripts/audit_seed.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Anchored regex + negative lookahead so "milkshake with ice cream"
          doesn't false-positive. Current state: zero category-plausibility
          flags. --fail-on-flags now also gates on this new check.

test_plan_iter23:
  current_focus:
    - "GET /api/foods/food-sajina — safety_tier ∈ {YELLOW,GREEN} (formula-computed from new numbers, NOT RED); portion_g=40; potassium_mg=233; phosphorus_mg=100; sodium_mg=5; protein_g=4.3."
    - "GET /api/foods/food-classic-club-sandwich — category=snack; fluid_ml=0; serving_disclaimer does NOT contain 'count as FLUID intake'."
    - "GET /api/foods/food-buttermilk-biscuit — category=snack; portion_g=35 (sweet bucket rescale); disclaimer references single-piece not 150 g portion."
    - "GET /api/foods/food-kadhai-paneer — category=dairy; portion_g=35 (routes through sweet bucket via SWEET_PATTERNS on 'paneer' or by K/P threshold in dairy)."
    - "GET /api/foods/food-vanilla-ice-cream-with-egg — category=dairy; fluid_ml=0 (stripped by solids-cannot-be-fluids pass)."
    - "GET /api/foods/food-macaroni-salad, food-orange-souffle, food-milk-cookies — all category NOT 'beverage', fluid_ml=0, no 'count as FLUID' text."
    - "GET /api/foods/food-chicken-stock — category=beverage still (explicit human decision kept); fluid_ml>0."
    - "GET /api/foods/food-egg-nog — category=beverage still (explicit human decision kept); fluid_ml>0."
    - "Additional audit catches applied: food-choconut-ice-cream, food-mango-ice-cream, food-strawberry-ice-cream etc. all category=dairy; food-masala-urad-dal-vada category=snack (was condiment)."
    - "backend/category_review.csv exists, has 36 rows, header 'food_id,kind,before,after,reason'."
    - "python3 scripts/audit_seed.py shows Category-plausibility flags = 0."
    - "REGRESSION: /api/foods list still returns >= 1018 entries. /api/foods/food-toor-dal, food-apple, food-potato still 200 with intact fields. /api/auth/me still works. /api/ai/ask still works. /api/meal-logs CRUD still works."
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

# ---------------- Iteration 24 (scan grounding fix + fluid budget surfaced) ----------------

backend_iter24:
  - task: "P0 BUG FIX: /scan/food no longer returns a colored tier for unmatched dishes"
    implemented: true
    working: "NA"
    file: "backend/server.py (scan_food + _classify_from_nutrients + FoodScanResponse)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Same class of bug as iter-22 for /ai/ask. Fix:
          (a) _extract_json parse failure OR empty result → UNVERIFIED + neutral
              portion/tip strings, no colored tier.
          (b) Vision LLM's self-reported tier is NEVER trusted — it's only used
              indirectly via the food_name for a DB lookup. If no match, tier=
              UNVERIFIED. If match, tier comes from the DB card (personal_tier_for).
          (c) FoodScanResponse.safety_tier accepts UNVERIFIED literal (via any
              string; frontend maps colored badges only for GREEN/YELLOW/RED).
  - task: "P0 BUG FIX: /scan/barcode no longer classifies packs with zero nutrient data"
    implemented: true
    working: "NA"
    file: "backend/server.py (scan_barcode + _classify_from_nutrients)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          _classify_from_nutrients now returns ("UNVERIFIED","NONE") when K/P/Na
          are all zero (Open Food Facts had no nutrients). scan_barcode adds an
          is_unverified guard: the synthetic bc_* food doc upsert is SKIPPED for
          UNVERIFIED packs so a patient can't favorite/log a phantom entry. If
          a DB seed name-match exists, that wins as before.
  - task: "Fluid budget surfaced end-to-end"
    implemented: true
    working: "NA"
    file: "backend/server.py (NutrientLimits.fluid_ml + limits_for_user)"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          NutrientLimits gained fluid_ml field (default 2000). limits_for_user
          now reads doctor override → stage default (1000ml dialysis / 2000ml
          otherwise). Doctor_limits already had fluid_ml — profile PATCH already
          persists it. MealLogSummary.limits and WeeklyReportResponse.limits both
          now carry fluid_ml.

frontend_iter24:
  - task: "SafetyBadge + TIER_META gain UNVERIFIED grey/neutral state (never colored)"
    implemented: true
    working: "NA"
    file: "frontend/src/theme.ts, frontend/src/components/SafetyBadge.tsx, frontend/src/lib/api.ts"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          ScanTier = SafetyTier | 'UNVERIFIED'. TIER_META.UNVERIFIED uses bgAlt/
          border/textSecondary + help-circle icon. Deliberately NOT reusing YELLOW.
          FoodScan.safety_tier typed as ScanTier so the scan screen must handle
          all four cases.
  - task: "Scan screen renders UNVERIFIED without risk/see-more/log affordances"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/scan.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "Meal-log + weekly report + weekly-PDF report all show fluid progress bar/row"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/meal-log.tsx, frontend/app/report.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
  - task: "Settings screen accepts a doctor-set fluid_ml override"
    implemented: true
    working: "NA"
    file: "frontend/app/(app)/settings.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true

test_plan_iter24:
  current_focus:
    - "PRIMARY BUG (scan/food): POST /api/scan/food with an image of a dish clearly NOT in db.foods should return safety_tier='UNVERIFIED', primary_risk_factor='NONE', portion_limit_text containing 'Not in our verified database yet', matched_food_id=None. Do NOT return GREEN/YELLOW/RED. Note: testing image can be a colored square or a photo of a made-up 'zorplok curry'; the LLM will invent a food_name but the DB lookup will fail → UNVERIFIED."
    - "PRIMARY BUG (scan/food regression): POST /api/scan/food with a photo/description that the LLM parses as a real DB food (e.g. 'apple' or 'chapati') should still return a colored tier from the DB card, matched_food_id set."
    - "PRIMARY BUG (scan/food parse fail): if the vision LLM returns unparseable text (no JSON), scan_food must ALSO return UNVERIFIED. Testable by mocking _extract_json to return None or by sending a request the model refuses to parse (harder to force in prod, so pytest-mock the helper if practical)."
    - "PRIMARY BUG (scan/barcode zero-nutrients): fetch a real barcode that Open Food Facts has NO nutrient data for (or mock the httpx response), verify safety_tier='UNVERIFIED', matched_food_id=None, and no bc_<barcode> food doc was inserted into db.foods."
    - "PRIMARY BUG (scan/barcode regression): a barcode with proper OFF nutrient data still returns GREEN/YELLOW/RED per _classify_from_nutrients."
    - "FLUID BUDGET (backend): GET /api/meal-logs/summary returns limits.fluid_ml (>0). GET /api/reports/weekly returns limits.fluid_ml. For a dialysis user, fluid_ml should default to 1000; for pre_dialysis/unknown, 2000."
    - "FLUID BUDGET (doctor override): PATCH /api/auth/profile body={doctor_limits:{fluid_ml:1500}}. GET /api/meal-logs/summary now returns limits.fluid_ml=1500 (doctor override wins over stage default). Cleanup: unset by patching with null.",
    - "FLUID BUDGET (frontend, 390x844): log in demo@renal.app/demo123. /meal-log screen shows a Fluid bar in the Today's Budget section (testID budget-fluid). Value/limit reflect current defaults. /report screen shows an avg-fluid bar (testID avg-fluid). Settings screen shows an input testID='settings-limit-fluid'; entering 1500 and tapping Save Limits persists."
    - "REGRESSION: /api/foods, /api/foods/food-apple, /api/auth/me, /api/meal-logs list/create, /api/ai/ask all still function."
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"


# ================================================================
# Iter 25 — server.py refactor + IFCT data expansion (dals, dairy, oils)
# ================================================================
backend_iter25:
  - task: "Refactor 1800-line server.py into modular package"
    implemented: true
    working: "NA"
    file: "backend/{config,db,security,schemas,personalization,food_enrichment,ai_service,scan_service,lifespan}.py, backend/routes/*.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          Broke server.py (1827 lines) into 9 focused modules + 8 route files:
            config.py       - env vars, JWT constants
            db.py           - Motor client + db handle
            security.py     - hash_pw, JWT, deps, rate-limiter
            schemas.py      - all Pydantic models + type aliases
            personalization.py - stage/tier logic, limits_for_user
            food_enrichment.py - enrich_food_sync/async
            ai_service.py   - AI system prompts, stopwords, tokenizer, retrieval, grounded block
            scan_service.py - _extract_json, _classify_from_nutrients, _SCAN_SYSTEM
            lifespan.py     - startup seeding, index creation, CSV dumps
            routes/{auth,foods,favorites,meal_logs,reports,guides,scan,ai}.py
          server.py is now ~60 lines: builds FastAPI app, wires api router, CORS, exception handler.
          Preserved re-exports: server.app, server.db, server._extract_json (used by iter24 tests).
          Discovered slowapi + `from __future__ import annotations` + pydantic body params breaks
          FastAPI's body-field introspection (returns 422). Removed the future-import from routes/*.py.
  - task: "New fats & oils guide (10 IFCT-sourced entries) + /api/oils/guide endpoint"
    implemented: true
    working: "NA"
    file: "backend/oil_guide.py, backend/routes/guides.py, backend/lifespan.py, backend/ai_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          6 GREEN oils (mustard, groundnut, sunflower, rice bran, desi ghee, unsalted butter),
          3 YELLOW (coconut, olive, sesame), 4 RED (salted butter, vanaspati, margarine, restaurant
          deep-fry). Every entry has IFCT 2017 code citation. AI-ask retrieval now walks oils too.
          lifespan.collect_needs_sourcing also flags any missing-sodium rows for QA CSV.
  - task: "Expand proteins guide: 4 new dal entries + 3 new dairy entries"
    implemented: true
    working: "NA"
    file: "backend/protein_guide.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          YELLOW dals added: Chana Dal (105 mg K), Urad Dal (130), Whole Green Moong (130),
          Kala Chana (150) — all with IFCT 2017 dry-weight code + explicit ~2.4x cooked-leaching
          factor comment (per the protein_guide preamble).
          YELLOW dairy: Plain Curd/Dahi (½ katori), Buttermilk (unsalted).
          RED dairy: Salted Lassi, Sweetened Condensed Milk.

frontend_iter25:
  - task: "Fats & Oils Guide screen + Home menu tile"
    implemented: true
    working: "NA"
    file: "frontend/app/oils.tsx, frontend/app/(app)/index.tsx, frontend/src/lib/api.ts, frontend/src/lib/i18n.ts"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: |
          New /oils route wired to <FoodGuideLayout entriesKey='oils' fetchGuide=api.getOilGuide>.
          Home menu grid gained an 11th tile: 'Fats & Oils Guide' with flask icon + yellow accent.
          i18n keys: menuOils, menuOilsSub, oilGuideTitle, oilGuideSubtitle, oilGuideIntro across
          en/hi/ta/bn/mr.

test_plan_iter25:
  current_focus:
    - "REFACTOR SMOKE: server import ok, app.routes has all 28 endpoints, /api/auth/login returns 200 with valid demo creds."
    - "REFACTOR REGRESSION: iter24 test_iter24_scan_grounding_and_fluid_budget.py runs 15/15 (verified in isolation)."
    - "NEW /api/oils/guide returns tiers GREEN/YELLOW/RED with enriched entries (potassium_meq, high_sodium)."
    - "NEW proteins guide includes Chana Dal, Urad Dal, Kala Chana, Whole Green Moong, Plain Curd, Buttermilk, Salted Lassi, Sweetened Condensed Milk."
    - "FRONTEND: Home menu shows 'Fats & Oils Guide' tile that navigates to /oils screen; screen renders 3 tiers with IFCT citations."
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication_iter25:
  - agent: "main"
    message: |
      Refactored server.py into 9 modules + 8 route files. Behavior preserved.
      Regression check: /api/auth/login, /api/foods, /api/proteins/guide, /api/oils/guide,
      /api/meal-logs/summary, /api/reports/weekly all return expected shapes.
      Iter24 pytests (15) all pass in isolation.
      New content: 10 oils, 4 dals, 4 dairy items — every entry cites IFCT 2017 code.


# ================================================================
# Iter 26 — Navigation consolidation
# ================================================================
backend_iter26:
  - task: "GET /api/foods gains ?category= filter with folk-mapping"
    implemented: true
    working: true
    file: "backend/routes/foods.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: |
          New CATEGORY_MAP dict expands frontend-facing chip keys to underlying
          db.foods.category values — "protein" → [protein, dal, dairy],
          "vegetable" → [vegetable, sabzi], others 1:1. Verified: ?category=fruit
          returns only fruit rows (200), ?category=protein returns 200 rows
          across protein/dal/dairy, ?category=vegetable returns 260 across
          vegetable/sabzi.

frontend_iter26:
  - task: "Home reduced to one hero action + budget bars + small More section"
    implemented: true
    working: true
    file: "frontend/app/(app)/index.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
  - task: "CheckFoodModeSwitcher shared component (Type/Photo/Voice)"
    implemented: true
    working: true
    file: "frontend/src/components/CheckFoodModeSwitcher.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
  - task: "Search screen: mode switcher + 6 category chips + tier chips"
    implemented: true
    working: true
    file: "frontend/app/(app)/search.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
  - task: "Scan + log-meal-nl screens carry the mode switcher too"
    implemented: true
    working: true
    file: "frontend/app/(app)/scan.tsx, frontend/app/log-meal-nl.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
  - task: "Delete 7 guide screens (fruits/vegetables/grains/snacks/proteins/beverages/oils)"
    implemented: true
    working: true
    file: "frontend/app/{fruits,vegetables,grains,snacks,proteins,beverages,oils}.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false

test_plan_iter26:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication_iter26:
  - agent: "main"
    message: |
      Nav consolidation complete. Home has ONE dominant "Check a food" hero,
      today's K/P/Na/Fluid budget bars, and a small More section (Report,
      Settings). Search/Scan/Voice are three modes of the same flow reached
      via a persistent top-of-screen switcher. Six standalone guide screens
      (+ the just-added Oils) deleted; their content is reachable via new
      category chips inside Search (Fruits, Vegetables, Grains, Snacks,
      Proteins, Beverages) mapped to backend CATEGORY_MAP.
      Tab bar untouched (5 items). Net screen count reduced by 7.


# Iter 27 — Salt substitutes + Protein target + P:Pro ratio + Vitamin/myth guide

backend_iter27:
  - task: "Salt substitutes in food DB (Lo-Salt, NoSalt, Tata Salt Lite, pink salt, kala namak, herb seasoning)"
    implemented: true
    working: true
    file: "/app/backend/seed_data.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Added 6 salt-substitute entries to SEED_FOODS. KCl-based Lo-Salt/NoSalt/Tata Salt Lite are RED with POTASSIUM primary risk (660/530/350 mg K per gram). Rock/pink and black salt classified per SODIUM. One GREEN entry for actual salt-free lemon-herb seasoning. Verified via /api/foods?q=salt search."
  - task: "Protein target — NutrientLimits.protein_g + DoctorLimits.protein_g + stage defaults"
    implemented: true
    working: true
    file: "/app/backend/schemas.py, /app/backend/personalization.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Added protein_g to both NutrientLimits (default 60g) and DoctorLimits. Stage defaults: dialysis=75g, pre-dialysis=50g, unknown=60g. suggest_protein_g(weight_kg, stage) helper added for onboarding (1.2 g/kg on dialysis per KDOQI, 0.8 g/kg otherwise). limits_for_user() respects doctor override. Verified via curl PATCH /auth/profile + GET /meal-logs/summary — protein_g now appears in the limits payload."
  - task: "Vitamin, supplement and dietary-myth reference block in AI ask context"
    implemented: true
    working: true
    file: "/app/backend/vitamin_myth_guide.py, /app/backend/ai_service.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Created vitamin_myth_guide.py with stage-filtered VITAMIN_GUIDANCE (B-complex on dialysis, vitamin C, D, A/E/K, iron, calcium, herbs, protein powders) plus 10 DIETARY_MYTHS (coconut water, banana, ORS, milk, brown rice, salt substitutes, pink salt, apple cider). Injected via get_vitamin_myth_context(stage) into _build_ai_context. System prompt updated with a new rule teaching the model to quote from this block. Verified live: 'Can I take whey protein?' returns egg-white/chicken alternatives; 'Is Lo-Salt safe?' returns strict AVOID with grounded 660mg K figure."

frontend_iter27:
  - task: "Protein bar on Home budget card"
    implemented: true
    working: true
    file: "/app/frontend/app/(app)/index.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Added a new NutrientBar for protein between Phosphorus and Sodium — testID home-budget-protein, uses `g` unit with 1 decimal. Reads summary.totals.protein_g and summary.limits.protein_g. Verified visually on Home."
  - task: "Weight input + protein-target field on onboarding (auto-suggest from body weight)"
    implemented: true
    working: true
    file: "/app/frontend/app/onboarding.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Added optional weight (kg) input + protein-target (g) input on the limits step. When user types weight, protein is auto-populated using KDOQI factor (1.2 g/kg dialysis, 0.8 g/kg otherwise). Once user manually edits the protein field, we stop overwriting (proteinTouched flag). Both fields propagate into doctor_limits on save. Skip button still respected — sends null doctor_limits."
  - task: "Protein target row + weight suggestion in Settings > Doctor limits"
    implemented: true
    working: true
    file: "/app/frontend/app/(app)/settings.tsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Added a testID=settings-limit-protein input under fluid_ml. Included in saveLimits() and clearLimits() flows. Pre-fills from user.doctor_limits.protein_g on mount."
  - task: "Phosphorus-to-protein ratio as secondary stat on food detail"
    implemented: true
    working: true
    file: "/app/frontend/app/food/[id].tsx"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Added a green/yellow/red banded ratio chip under the tier badge showing 'X.X mg P per g protein' + short interpretation. Bands: <15 excellent (green), 15-25 acceptable (yellow), >25 high (red). Hidden when protein_g < 1.0 to avoid meaningless ratios on fruits/vegetables. Verified: Paneer 7.2 → excellent, Cow Milk 28.2 → high."

test_plan_iter27:
  current_focus:
    - "Salt substitutes search + tier classification"
    - "Doctor limits PATCH with protein_g + summary/reports response shape"
    - "Onboarding weight auto-suggests protein and can be overridden"
    - "AI /ai/ask about vitamins, salt substitutes and myths quotes grounded data"
    - "P:Pro ratio chip on food detail (paneer/milk/rajma)"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication_iter27:
  - agent: "main"
    message: |
      Four new features shipped in one pass (per user's YES to all):
      1. Salt substitutes (6 new foods) — searchable via unified /search;
         all KCl-based ones RED-POTASSIUM, real salt-free lemon-herb GREEN.
      2. Protein target — added to schemas (DoctorLimits + NutrientLimits),
         personalization defaults (75g dialysis / 50g pre-dialysis / 60g
         unknown), onboarding (with body-weight auto-suggest 1.2 or 0.8
         g/kg per KDOQI 2020), Settings, and Home budget card (new bar).
      3. Phos:Protein ratio — secondary green/yellow/red banded chip on
         food detail under the tier badge. Hidden for protein_g<1.
      4. Vitamin/dietary-myth guide — new backend module fed into Ask AI
         grounded context so /ai/ask can answer supplement + myth
         questions without a separate Learn tab (per nav-consolidation
         rule: no new top-level screens).
      Backed by curl smoke tests + visual screenshots. No standalone
      screens added. Frontend lint clean. Ready for testing_agent.


# Iter 28 — Salt substitute chemistry correction + Scan/text mode merge

backend_iter28:
  - task: "Salt substitute K/Na chemistry correction (elemental K = KCl × 0.525, elemental Na = NaCl × 0.394) + source fields on all 6"
    implemented: true
    working: true
    file: "/app/backend/seed_data.py, /app/backend/guide_utils.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Fixed potassium_mg on food-lo-salt-substitute (660→350) and food-tata-saltlite (350→184) — previous values were raw KCl compound mass, now elemental K per KCl × 0.525. Sodium recomputed via NaCl × 0.394 on same two entries (Lo-Salt 30→131, Tata 150→256). Verified pink salt (Na=390 vs NaCl × 0.394 × 980 ≈ 386) and kala namak (Na=380 vs 960 × 0.394 ≈ 378) already used the right conversion — added math comments for future auditability. Added `source` field to all 6 entries citing manufacturer / USDA / IFCT with the specific conversion. Added Tata Salt Lite %KCl split to _FLAGGED_UNSOURCED so guide_needs_sourcing.csv flags it as needing manufacturer spec verification. Tier reclassified per classify_from_nutrients (Tata Salt Lite now YELLOW at K=184; Lo-Salt/NoSalt still RED; pink salt & kala namak YELLOW at Na=380-390 since <400 threshold)."
        - working: true
          agent: "testing"
          comment: "Verified via 11 new pytest checks (test_iter28_salt_chemistry_and_scan_merge.py) — all 6 entries match spec'd K/Na/tier/risk_factor. All 6 have non-empty source. 5/5 KCl/NaCl-based entries cite the conversion factor in the source string. guide_needs_sourcing.csv includes the Tata Salt Lite flag row. Iter-27 tests updated to match new correct values."
frontend_iter28:
  - task: "Merge natural-language meal logging (log-meal-nl) into scan.tsx as a third mode (text)"
    implemented: true
    working: true
    file: "/app/frontend/app/(app)/scan.tsx, /app/frontend/src/components/MealTextInput.tsx, /app/frontend/src/components/CheckFoodModeSwitcher.tsx, /app/frontend/app/(app)/meal-log.tsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Extracted /log-meal-nl.tsx logic into a reusable MealTextInput component. scan.tsx now has 3 modes (vision/barcode/text) with a third `scan-mode-text` chip and text-mode body rendering the extracted component. Supports `?mode=text&date=&meal_type=` URL params. CheckFoodModeSwitcher's voice route updated to `/(app)/scan?mode=text`. meal-log.tsx's `open-log-by-text` button now routes to `/(app)/scan?mode=text`. Deleted standalone /app/frontend/app/log-meal-nl.tsx. On web, the camera-permission early-return is now skipped so mode chips remain visible when the browser has no camera."
        - working: true
          agent: "testing"
          comment: "Verified via targeted frontend re-test — all 3 mode chip testIDs present on default /(app)/scan; switching to text mode shows Describe UI; switching to barcode shows barcode overlay; /log-meal-nl now hits Unmatched Route; meal-log button routes correctly."

test_plan_iter28:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication_iter28:
  - agent: "main"
    message: |
      Two review fixes from iter-27:
      1. Salt substitute chemistry — potassium_mg was storing raw KCl compound
         mass on Lo-Salt (660) and Tata Salt Lite (350). Corrected to elemental
         K = KCl × 0.525 (350 and 184 respectively). NaCl → elemental Na
         correction applied where needed. All 6 entries now have a source
         field citing the manufacturer/USDA/IFCT reference and, where
         applicable, the exact conversion arithmetic (K = KCl × 0.525, Na =
         NaCl × 0.394). Tata Salt Lite's % KCl split flagged in
         guide_needs_sourcing.csv pending manufacturer spec.
      2. Nav consolidation completion — log-meal-nl was still a standalone
         route. Extracted its screen logic to MealTextInput.tsx, embedded
         inside scan.tsx as a third mode (vision/barcode/text). Deleted the
         standalone route, updated the two links that pointed at it (Home
         hero via CheckFoodModeSwitcher, meal-log's "Log by text" button).
         All three input methods now live in ONE screen.
      Both fixes confirmed by testing_agent (26/26 backend + 4/4 frontend).


# Iter 29 — Salt substitute manufacturer-verify + Barcode/Vision salt warning

backend_iter29:
  - task: "Lo-Salt manufacturer-verified (Klinge Foods 66% KCl / 33% NaCl) + Tata Salt Lite flagged as unverified composition"
    implemented: true
    working: true
    file: "/app/backend/seed_data.py, /app/backend/guide_utils.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Lo-Salt verified from Klinge Foods spec (klinge-foods.com/losalt.html) + Open Food Facts entry 5011544070034 → 66.0% KCl min / 33.3% NaCl max. K=346 (was 350; recomputed 660 × 0.525). Source string now cites both refs explicitly. Tata Salt Lite %KCl split NOT publicly declared by Tata Consumer Products (their marketing states '15% less sodium than table salt' but doesn't state KCl fraction and FSSAI declaration isn't in any web source). Flagged with data_quality_flag='concentrated_base_pending_resourcing' — food detail UI shows 'Pending re-sourcing' badge. Source field starts 'COMPOSITION NOT YET SOURCED'. Tip openly acknowledges unverified. guide_needs_sourcing.csv row remains."
        - working: true
          agent: "testing"
          comment: "3/3 backend checks pass — Lo-Salt K/Na/tier/source correct; Tata Salt Lite data_quality_flag set + source starts 'COMPOSITION NOT YET SOURCED'; guide_needs_sourcing.csv has the Tata row."

  - task: "Salt-substitute warning bar in Scan (barcode + vision) — fires on TEXT PATTERN, not DB match"
    implemented: true
    working: true
    file: "/app/backend/routes/scan.py, /app/backend/schemas.py, /app/frontend/app/(app)/scan.tsx, /app/frontend/src/lib/i18n.ts, /app/frontend/src/lib/api.ts"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Added FoodScanResponse.salt_substitute_warning bool field. Backend helper _looks_like_salt_substitute() runs the compiled _SALT_SUBSTITUTE_PATTERN regex against product_name + brand + ingredients_text + OFF categories (barcode) and against LLM food_name + raw response (vision). Regex covers: potassium chloride, KCl, low(-)sodium(-salt), reduced(-)sodium, lite salt, salt substitute, salt alternative, sendha, rock salt, himalayan (pink) salt, pink salt, lo(-)salt, no(-)salt, kala namak, black salt, tata salt lite. Applied in BOTH return branches of scan_food (parse failure + DB match/no-match) and in scan_barcode. Independent of DB match — the UNVERIFIED case is exactly when this warning matters most (patient scanning an unfamiliar 'healthy' salt). Frontend SaltSubstituteWarning component renders a solid red bar above ScanResultCard in both scan modes."
        - working: true
          agent: "testing"
          comment: "All 20 tests pass — live OFF barcode 5011544070034 returns salt_substitute_warning=True; Nutella (3017620422003) returns False; regex matches all 15 red-flag keywords and rejects 4 negatives. Frontend renders warning above card in both scan branches; testID + red background verified; 5-lang translations present."

test_plan_iter29:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication_iter29:
  - agent: "main"
    message: |
      Two review fixes from iter-28:
      1. Manufacturer verify — Lo-Salt confirmed 66% KCl / 33% NaCl from
         Klinge Foods manufacturer spec + Open Food Facts entry. Numbers
         updated (K 350→346) and source properly cited. Tata Salt Lite's
         %KCl split isn't publicly declared anywhere we could find, so
         flagged with data_quality_flag='concentrated_base_pending_resourcing'
         (existing badge). Source string starts with 'COMPOSITION NOT YET
         SOURCED'. guide_needs_sourcing.csv row kept from iter-28.
      2. Barcode/vision Salt-Substitute Warning — trigger is TEXT PATTERN,
         not DB match. Regex matches product name, brand, OFF ingredient
         text, categories (barcode) or LLM food_name (vision). Fires in
         both matched and UNVERIFIED cases — an unknown 'healthy' salt is
         precisely the danger case. New SaltSubstituteWarning component
         renders a red bar ABOVE the safety card. 5-language translations
         with unhedged 'never' wording. Verified live via real Lo-Salt
         (Open Food Facts) barcode 5011544070034 → warning True; Nutella
         3017620422003 → False.
      Both fixes confirmed by testing_agent (20/20 backend + frontend).


# Iter 30 — Regex tighten + Tata tier_override + reconciliation backstop

backend_iter30:
  - task: "Salt-substitute regex — require 'salt' after low/reduced-sodium; exclude 'no salt added' via negative lookahead"
    implemented: true
    working: true
    file: "/app/backend/routes/scan.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Removed bare 'low-sodium' / 'reduced-sodium' matches — now require 'salt' after. Added lookahead (?![\\s-]+added) on 'no salt' so 'No Salt Added Canned Tomatoes' and 'No-salt-added chickpeas' don't fire. All 15 original positives still match; 4 new negatives don't. Verified via _looks_like_salt_substitute unit calls."
        - working: true
          agent: "testing"
          comment: "16/16 iter-30 tests pass (see test_iter30_salt_regex_and_reconciliation.py). All negatives return False; all 15 positives + bare 'no salt' return True."

  - task: "Tata Salt Lite tier_override=RED for tier/text consistency"
    implemented: true
    working: true
    file: "/app/backend/reconciliation.py, /app/backend/seed_data.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Added food-tata-saltlite to CURATED_TIER_OVERRIDES with reason 'Composition unverified; portion_limit says Avoid — hold RED until physical pack sourced.' Seed's safety_tier now declares RED too. curated_overrides goes 7→8. The entry remains the ONE intentional case where both tier_override AND data_quality_flag apply — the flag drives the 'Pending re-sourcing' user badge while tier_override holds the tier at RED. test_no_overlap assertion updated 0→1 to codify this exception."
        - working: true
          agent: "testing"
          comment: "Endpoint returns safety_tier=RED, tier_override=True, data_quality_flag preserved, portion_limit contains 'Avoid'."

  - task: "CONCENTRATED_BASE_IDS additions + Step 7b sanity-violation backstop + stats counter recomputation"
    implemented: true
    working: true
    file: "/app/backend/reconciliation.py, /app/backend/tests/test_iter13d_pending_resourcing.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Added food-curried-cauliflower-soup and food-classic-seasoned-black-beans to CONCENTRATED_BASE_IDS (both were failing sanity_check post-reconciliation but weren't flagged). Added Step 7b backstop: any entry still failing sanity_check() after reconciliation that doesn't have tier_override AND doesn't already carry data_quality_flag gets 'concentrated_base_pending_resourcing' set automatically. Also added tail line that recomputes stats['data_quality_flagged'] from the final deduped list so it matches Mongo when a seed entry declares data_quality_flag directly (e.g. Tata Salt Lite). Bumped 4 assertions in test_iter13d — flagged_count 39→42, tier_override 7→8, no_overlap 0→1 (Tata's intentional exception), audit_seed data_quality_flagged 39→42."
        - working: true
          agent: "testing"
          comment: "Final verification 5/5 checkpoints pass. Reconciliation log: sanity_violations=41, curated_overrides=8, data_quality_flagged=42. audit_seed --json: data_quality_flagged=42, sanity_violations_count=41, curated_overrides=8. iter-13d 4/4 assertions PASS at new values."

test_plan_iter30:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication_iter30:
  - agent: "main"
    message: |
      Reviewer flagged three issues from iter-29:
      1. Regex too broad — false-positive clinical claim on 'Low Sodium
         Bread' / 'Reduced Sodium Namkeen' / 'No Salt Added Canned
         Tomatoes'. Tightened pattern to require 'salt' after
         low/reduced-sodium and added lookahead excluding
         '(no|no-)salt(?![\\s-]+added)'.
      2. Tata Salt Lite tier/text mismatch — formula lands YELLOW at
         K=184 but portion_limit says 'Avoid'. Added tier_override=RED
         via CURATED_TIER_OVERRIDES. The entry is now the sole
         intentional exception with BOTH tier_override AND
         data_quality_flag (each drives independent user-visible
         behavior: RED tier + 'Pending re-sourcing' badge respectively).
      3. Missing CONCENTRATED_BASE_IDS entries + no backstop — added
         two missing IDs and a Step 7b auto-flag for any post-reconcile
         sanity-ceiling breach not already flagged/tier_overridden.
         Also aligned the stats counter with the Mongo count so audit
         reports match.
      Four iter-13d assertions bumped (three the reviewer flagged, plus
      the audit_seed counterpart). Testing agent confirmed 5/5 final
      checkpoints + all iter-13d + all iter-30 pass. Sajina assertion
      failures reported are pre-existing and outside iter-30 scope.


# Iter 31 — Bug fix: mango search only showed Mango Malpua

backend_iter31:
  - task: "Add 28 missing fruit entries + fix mango-malpua category + link fruit_guide entries"
    implemented: true
    working: true
    file: "/app/backend/seed_data.py, /app/backend/seed_data_indb.py, /app/backend/fruit_guide.py, /app/backend/reconciliation.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "User reported searching 'mango' only surfaced Mango Malpua. Root cause: only 6 fruit entries in seed (apple/papaya/pear/banana×2/orange) — mango and 27 other common Indian fruits existed only in fruit_guide.py with linked_food_id=None. Added 28 fruit entries to seed_data.py with K values from fruit_guide (IFCT 2017 + USDA composite). Fixed food-mango-malpua category mislabel (fruit → snack). Batch-linked all 28 fruit_guide entries via linked_food_id. Added food-mango-small and food-mango-whole to CURATED_TIER_OVERRIDES so their tiers (YELLOW/RED) match the fruit_guide block placement, following the same aspirational-tier pattern as food-orange. Bumped test_iter13d tier_override count 8 → 10."
        - working: true
          agent: "testing"
          comment: "21/21 tests pass in test_iter31_mango_fruits_search.py — mango search returns both new entries, malpua now snack, grapes/watermelon/guava/kiwi/chikoo searchable, category=fruit filter returns 33+, fruit_guide linked_food_ids populated. iter-13d invariants preserved (flagged=42, tier_override=10, overlap=1). No regressions to salt-substitute machinery."

test_plan_iter31:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication_iter31:
  - agent: "main"
    message: |
      User reported: "ON SEARCHING FOR MANGO THE APP IS ONLY SHOWINTG
      MANGO MALPIA".
      Root cause: seed_data.py only had 6 fruit entries. The other 27+
      common fruits existed only in fruit_guide.py (a curated reference
      screen) with linked_food_id=None, so they never made it into the
      searchable food catalog. Mango-derived items like mango-malpua
      were searchable and one of them was miscategorised as fruit,
      making the gap especially obvious for mango.
      Fixed by:
        1. Adding 28 fruit entries to seed_data.py (mango small/whole,
           pineapple, watermelon, grapes, lychee, fig fresh, straw-
           berries, blueberries, cranberries, guava, peach, plum,
           cherry, pomegranate, kiwi, muskmelon, ber, chikoo, custard
           apple, dates, raisins, dried apricots, prunes, amla, bael,
           phalsa).
        2. Fixing food-mango-malpua category fruit → snack.
        3. Batch-updating fruit_guide.py to populate linked_food_id
           for all 28 previously-unlinked entries.
        4. Adding mango-small (YELLOW) and mango-whole (RED) to
           CURATED_TIER_OVERRIDES so the food-detail tier matches the
           fruit_guide block placement — same aspirational-tier
           pattern used for food-orange.
        5. Bumping test_iter13d tier_override assertion 8 → 10.
      Verified via testing_agent — 21/21 tests pass, no regressions.


# Iter 32 — Guide-gap audit backfill (121 entries) + Search relevance sort

backend_iter32:
  - task: "Vegetable/Grain/Protein/Snack/Beverage gap audit + backfill via seed_guide_staples.py"
    implemented: true
    working: true
    file: "/app/backend/seed_guide_staples.py (NEW), /app/backend/lifespan.py, /app/backend/scripts/audit_seed.py, /app/backend/vegetable_guide.py, grain_guide.py, protein_guide.py, snack_guide.py, beverage_guide.py, /app/backend/tests/test_iter13d_pending_resourcing.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Same-shape bug as iter-31's mango bug lived in all 5 remaining category guides (121 unlinked entries across vegetable/grain/protein/snack/beverage). Audited each guide, matched 12 against existing DB entries and populated their linked_food_id, then generated 109 new seed entries in seed_guide_staples.py. K from guide (IFCT + USDA), P/Na/protein via category-typical defaults + hand-tuned overrides for high-signal items (milk, cheese, tomato juice, condensed milk, etc.). Loaded via SEED_FOODS + SEED_GUIDE_STAPLES in both lifespan.py and audit_seed.py. New reconciliation totals: input 1060→1181, sanity_violations 41→42, data_quality_flagged 42→43, duplicates_dropped 9→11 (two staple entries slugged to pre-existing IDs food-samosa and food-sweet-lassi; deduplication kept the canonical seed_data versions). Bumped 3 iter-13d assertions accordingly."
        - working: true
          agent: "testing"
          comment: "79/79 iter-32 tests pass; iter-13d bumped assertions pass at new values; multi-word 'sports drink' surfaces Sports / Energy Drinks correctly."

  - task: "Search relevance sort — exact-name matches surface above alphabetical substring matches; multi-word queries match individual words"
    implemented: true
    working: true
    file: "/app/backend/routes/foods.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "When q is provided, results are pulled from Mongo then sorted in Python by priority: (0) exact name match, (1) name starts-with q, (2) hindi_name starts-with q, (3) substring in name, (4) alphabetical fallback. Fixes the UX bug that iter-31 uncovered: 'mango' surfaced 'Dry mango chutney' above 'Mango (small portion)' purely by alphabetical order. Also added a multi-word $and clause so 'sports drink' matches 'Sports / Energy Drinks' where the words don't appear consecutively."
        - working: true
          agent: "testing"
          comment: "All exact-match queries (mango, milk, water, green tea, cauliflower) surface the exact-name entry first. Multi-word 'sports drink' → 'Sports / Energy Drinks' first result."

test_plan_iter32:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication_iter32:
  - agent: "main"
    message: |
      Two follow-up asks from iter-31:
      1. Guide gap audit — audit_strict.py identified 121 unlinked
         entries across vegetable_guide, grain_guide, protein_guide,
         snack_guide and beverage_guide. Auto-linked 12 to existing DB
         entries and generated 109 new food entries in seed_guide_
         staples.py (loaded via SEED_FOODS + SEED_GUIDE_STAPLES in
         lifespan.py). Two guide entries deduplicated against existing
         seed_data (food-samosa, food-sweet-lassi) — the canonical
         seed_data entries won and the guides link to those.
      2. Search relevance sort — exact-name matches now surface first
         (priority 0), followed by starts-with (name / hindi_name),
         substring, and alphabetical fallback. Multi-word queries add
         an implicit AND so 'sports drink' matches 'Sports / Energy
         Drinks' where the phrase isn't consecutive.
      Testing agent confirmed 79/79 + 5/5 final checkpoints. iter-13d
      assertions bumped: duplicates_dropped 9→11, data_quality_flagged
      42→43. Sajina pre-existing failures remain out of scope.


# Iter 33 — Sajina reconcile + P/Na refinement (30) + Hindi search

backend_iter33:
  - task: "Sajina test-assertion reconcile with iter-23 rescale"
    implemented: true
    working: true
    file: "/app/backend/tests/test_iter13d_pending_resourcing.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "test_portion_unchanged bumped 150→40 with comment explaining iter-23's 150g raw-leaf → 40g cooked-katori rescale. test_tier_red now asserts safety_tier=YELLOW AND personal_tier ∈ {RED, YELLOW} (the personalization layer bumps to RED for dialysis, so the clinical safety net remains). Current state is intentional: portion=40, K=233, formula-YELLOW, personalization-RED-for-dialysis, actionable_clinical_tip warns Best avoided in advanced CKD."
        - working: true
          agent: "testing"
          comment: "4/4 TestB5Sajina tests pass."

  - task: "P/Na guide sourcing — top-30 entries refined from category defaults to IFCT 2017/USDA per-serving values"
    implemented: true
    working: true
    file: "/app/backend/seed_guide_staples.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Refined phosphorus/sodium/protein on 30 highest-signal entries: ridge/ash gourd, cauliflower, green beans, capsicum, carrot, brinjal, green peas, okra, pumpkin, mushroom, karela, radish, sweet potato, yam, colocasia, spinach, suji, maida-roti, oats, bajra roti, jowar roti, ragi, masoor/chana/urad/whole moong, water, herbal tea, green tea. K unchanged (already guide-sourced). Values scaled from IFCT per-100g figures to each entry's stated portion_g."
        - working: true
          agent: "testing"
          comment: "5 spot-checks pass exact values (cauliflower P=44/Na=8/prot=1.9, oats 99/1/4.2, carrot 20/40/0.6, ridge-gourd 35/8/0.6, masoor 115/3/5.4). No tier changes."

  - task: "Hindi/Devanagari search — unified name+hindi_name scoring + strip parenthetical qualifiers"
    implemented: true
    working: true
    file: "/app/backend/routes/foods.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Extended iter-32's score() function to also score by hindi_name (exact and starts-with), and to strip parenthetical qualifiers before compare — so 'आम' matches the base 'आम' inside 'आम (छोटा भाग)' as exact (score 0), not starts-with (score 2). English regressions preserved. Devanagari 'आम' now ranks Mango (small portion) → Mango (whole) → Aam Panna in that order."
        - working: true
          agent: "testing"
          comment: "'आम' returns Mango (small portion) at idx 0; 'दूध' returns milk; all 5 English regressions clean; multi-word 'sports drink' unaffected."

test_plan_iter33:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication_iter33:
  - agent: "main"
    message: |
      Three follow-ups from iter-32 completed:
      1. Sajina — current 40g/YELLOW/personal-RED state is intentional
         (iter-23 rescale); updated the two stale iter-13d assertions
         to match, with comments explaining provenance.
      2. P/Na guide sourcing (top-30) — 30 highest-signal entries
         refined from category-typical defaults to real IFCT 2017 /
         USDA per-serving values. No tier drift.
      3. Hindi search — extended search score() to also match on
         hindi_name and to strip parenthetical qualifiers, so
         Devanagari 'आम' surfaces Mango (small portion) at exact-match
         score 0. All English regressions preserved.
      Voice dictation remains deferred per prior guidance.
      Testing agent: 20/20 pass. Reconciliation counts unchanged
      (data_quality_flagged=43, sanity_violations=42, curated_overrides=
      10, duplicates_dropped=11).
