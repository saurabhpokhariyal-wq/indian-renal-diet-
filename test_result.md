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
