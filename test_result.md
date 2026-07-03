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
