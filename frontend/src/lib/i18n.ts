export type Lang = "en" | "hi" | "ta" | "bn" | "mr";

// Each entry must have `en`. Other languages are optional and fall back to
// English via t() — this lets us ship the plumbing for new languages and add
// polished translations incrementally without breaking the type check.
type Entry = { en: string; hi?: string; ta?: string; bn?: string; mr?: string };

export const translations: Record<string, Entry> = {
  appName: {
    en: "Indian Renal Diet",
    hi: "इंडियन रीनल डाइट",
    ta: "இந்திய சிறுநீரக உணவு",
    bn: "ইন্ডিয়ান রেনাল ডায়েট",
    mr: "इंडियन रेनल डाएट",
  },
  tagline: {
    en: "Smart food swaps for kidney health",
    hi: "किडनी के लिए स्मार्ट फूड स्वैप",
    ta: "சிறுநீரக ஆரோக்கியத்துக்கான ஸ்மார்ட் உணவு மாற்றங்கள்",
    bn: "কিডনি স্বাস্থ্যের জন্য স্মার্ট খাবার বদল",
    mr: "किडनीच्या आरोग्यासाठी स्मार्ट फूड स्वॅप",
  },

  tabSearch: { en: "Search", hi: "खोज", ta: "தேடல்", bn: "খুঁজুন", mr: "शोधा" },
  tabMeals: { en: "Meals", hi: "भोजन", ta: "உணவுகள்", bn: "খাবার", mr: "जेवण" },
  tabAI: { en: "Ask AI", hi: "AI से पूछें", ta: "AI-ஐக் கேளுங்கள்", bn: "AI-কে জিজ্ঞাসা", mr: "AI ला विचारा" },
  tabSettings: { en: "Settings", hi: "सेटिंग्स", ta: "அமைப்புகள்", bn: "সেটিংস", mr: "सेटिंग्ज" },

  tabHome: { en: "Home", hi: "होम", ta: "முகப்பு", bn: "হোম", mr: "होम" },

  menuTitle: { en: "What would you like to do?", hi: "आप क्या करना चाहेंगे?" },
  menuScan: { en: "Scan", hi: "स्कैन", ta: "ஸ்கேன்", bn: "স্ক্যান", mr: "स्कॅन" },
  menuReport: { en: "Weekly Report", hi: "साप्ताहिक रिपोर्ट" },
  menuSearchSub: { en: "Check if a food is kidney-safe", hi: "जाँचें कि भोजन किडनी के लिए सुरक्षित है या नहीं" },
  menuScanSub: { en: "Scan a dish or barcode with your camera", hi: "कैमरे से डिश या बारकोड स्कैन करें" },
  menuMealsSub: { en: "Log today's meals and track nutrients", hi: "आज का भोजन दर्ज करें और पोषण देखें" },
  menuReportSub: { en: "7-day summary to share with your doctor", hi: "डॉक्टर से साझा करने के लिए 7-दिन का सारांश" },
  menuAISub: { en: "Ask diet questions in simple language", hi: "सरल भाषा में डाइट से जुड़े सवाल पूछें" },
  menuSettingsSub: { en: "Language, health profile and limits", hi: "भाषा, हेल्थ प्रोफ़ाइल और सीमाएँ" },

  loginTitle: {
    en: "Welcome back",
    hi: "फिर से स्वागत है",
    ta: "மீண்டும் வரவேற்கிறோம்",
    bn: "আবার স্বাগতম",
    mr: "पुन्हा स्वागत आहे",
  },
  loginSubtitle: {
    en: "Sign in to your kidney-safe diet coach",
    hi: "अपने किडनी-सुरक्षित डाइट कोच में साइन इन करें",
    ta: "உங்கள் சிறுநீரக பாதுகாப்பான உணவு பயிற்சியாளரில் உள்நுழையவும்",
    bn: "আপনার কিডনি-সুরক্ষিত ডায়েট কোচে সাইন ইন করুন",
    mr: "तुमच्या किडनी-सुरक्षित डाएट कोचमध्ये साइन इन करा",
  },
  registerTitle: { en: "Create account", hi: "खाता बनाएँ" },
  registerSubtitle: { en: "Start your kidney-safe eating journey", hi: "किडनी-सुरक्षित खान-पान की शुरुआत करें" },
  email: { en: "Email", hi: "ईमेल" },
  password: { en: "Password", hi: "पासवर्ड" },
  fullName: { en: "Full name (optional)", hi: "पूरा नाम (वैकल्पिक)" },
  signIn: { en: "Sign In", hi: "साइन इन", ta: "உள்நுழை", bn: "সাইন ইন", mr: "साइन इन" },
  signUp: { en: "Sign Up", hi: "साइन अप", ta: "பதிவு", bn: "সাইন আপ", mr: "साइन अप" },
  noAccount: { en: "New here? Create an account", hi: "नए हैं? खाता बनाएँ" },
  hasAccount: { en: "Already have an account? Sign in", hi: "पहले से खाता है? साइन इन करें" },

  searchPlaceholder: { en: "Search for a food, e.g. Palak Paneer", hi: "भोजन खोजें, जैसे पालक पनीर" },
  greeting: {
    en: "Namaste",
    hi: "नमस्ते",
    ta: "வணக்கம்",
    bn: "নমস্কার",
    mr: "नमस्ते",
  },
  quickTips: { en: "Popular searches", hi: "लोकप्रिय खोजें" },
  noResults: { en: "No foods matched your search", hi: "कोई भोजन नहीं मिला" },

  portion: { en: "Portion Limit", hi: "मात्रा सीमा" },
  clinicalTip: { en: "Clinical Tip", hi: "क्लिनिकल टिप" },
  swapHeader: { en: "Recommended Safe Swap", hi: "सुरक्षित विकल्प" },
  whyBetter: { en: "Why this is better", hi: "यह क्यों बेहतर है" },
  addToLog: { en: "Add to today's meal log", hi: "आज के भोजन लॉग में जोड़ें" },
  added: { en: "Added ✓", hi: "जोड़ा ✓" },
  back: { en: "Back", hi: "वापस" },
  riskFactor: { en: "Primary Risk", hi: "मुख्य जोखिम" },

  mealLog: { en: "Today's Meals", hi: "आज का भोजन" },
  emptyMeals: { en: "No meals logged yet. Search a food and add it here.", hi: "अभी तक कोई भोजन दर्ज नहीं। कोई भोजन खोजकर यहाँ जोड़ें।" },
  summarySafe: { en: "Safe", hi: "सुरक्षित", ta: "பாதுகாப்பான", bn: "নিরাপদ", mr: "सुरक्षित" },
  summaryCaution: { en: "Caution", hi: "सावधानी", ta: "எச்சரிக்கை", bn: "সতর্কতা", mr: "सावधान" },
  summaryAvoid: { en: "Avoid", hi: "टालें", ta: "தவிர்க்கவும்", bn: "এড়িয়ে চলুন", mr: "टाळा" },
  remove: { en: "Remove", hi: "हटाएँ" },

  askAiTitle: { en: "Ask your Renal Diet AI", hi: "अपने रीनल डाइट AI से पूछें" },
  askAiSubtitle: { en: "Powered by Claude Sonnet 4.5", hi: "Claude Sonnet 4.5 द्वारा" },
  askAiPlaceholder: { en: "Type your question, e.g. 'Is bhindi safe for CKD?'", hi: "प्रश्न लिखें, जैसे 'क्या भिंडी CKD में सुरक्षित है?'" },
  askAiSend: { en: "Ask", hi: "पूछें" },
  askAiWelcome: {
    en: "Hi! I can answer any question about Indian food and your kidney diet. Ask me about a dish, ingredient, or portion.",
    hi: "नमस्ते! मैं भारतीय भोजन और आपकी किडनी डाइट के बारे में किसी भी प्रश्न का उत्तर दे सकता हूँ।",
  },

  settingsTitle: { en: "Settings", hi: "सेटिंग्स" },
  language: { en: "Language", hi: "भाषा" },
  english: { en: "English", hi: "अंग्रेज़ी" },
  hindi: { en: "हिन्दी", hi: "हिन्दी" },
  signOut: { en: "Sign Out", hi: "साइन आउट" },
  disclaimer: {
    en: "This app provides general dietary guidance for CKD/dialysis patients. Always consult your nephrologist for personal targets.",
    hi: "यह ऐप CKD/डायलिसिस रोगियों के लिए सामान्य आहार मार्गदर्शन देता है। व्यक्तिगत लक्ष्य के लिए हमेशा अपने नेफ्रोलॉजिस्ट से सलाह लें।",
  },
  reviewDisclaimer: { en: "Review medical disclaimer", hi: "चिकित्सा अस्वीकरण देखें" },

  // Full-screen disclaimer
  disclaimerScreenTitle: { en: "Before you begin", hi: "शुरू करने से पहले" },
  disclaimerScreenLead: {
    en: "This app is an educational tool. It is not medical advice, diagnosis or treatment.",
    hi: "यह ऐप एक शैक्षणिक साधन है। यह चिकित्सा सलाह, निदान या उपचार नहीं है।",
  },
  disclaimerP1: {
    en: "Food safety colors (Green/Yellow/Red) are general guidance for CKD and dialysis patients — not a substitute for your care team's advice.",
    hi: "भोजन सुरक्षा रंग (हरा/पीला/लाल) CKD और डायलिसिस रोगियों के लिए सामान्य मार्गदर्शन हैं — यह आपकी चिकित्सा टीम की सलाह का विकल्प नहीं है।",
  },
  disclaimerP2: {
    en: "Always follow the personal potassium, phosphorus, sodium and fluid targets your nephrologist has set for you.",
    hi: "अपने नेफ्रोलॉजिस्ट द्वारा तय किए गए व्यक्तिगत पोटैशियम, फ़ॉस्फ़ोरस, सोडियम और तरल लक्ष्यों का हमेशा पालन करें।",
  },
  disclaimerP3: {
    en: "The AI food scanner and Ask-AI answers may be inaccurate. Do not act on them without confirming with your care team.",
    hi: "AI भोजन स्कैनर और Ask-AI उत्तर गलत भी हो सकते हैं। इन्हें अपनी चिकित्सा टीम से पुष्टि किए बिना न मानें।",
  },
  disclaimerAccept: { en: "I understand", hi: "मैं समझ गया / गयी" },
  disclaimerClose: { en: "Close", hi: "बंद करें" },

  // Error state
  somethingWrong: { en: "Something went wrong", hi: "कुछ गलत हो गया" },
  couldNotLoad: { en: "We couldn't load this. Please check your connection and try again.", hi: "हम यह लोड नहीं कर सके। कृपया कनेक्शन जाँचें और पुनः प्रयास करें।" },
  retry: { en: "Retry", hi: "पुनः प्रयास" },

  // Filters
  filterAll: { en: "All", hi: "सभी" },

  // Meal-log date nav
  today: { en: "Today", hi: "आज" },
  prevDay: { en: "Previous day", hi: "पिछला दिन" },
  nextDay: { en: "Next day", hi: "अगला दिन" },

  // Ask AI
  clearChat: { en: "Clear chat", hi: "बातचीत साफ़ करें" },

  // Nutrients
  nutrientPotassium: { en: "Potassium", hi: "पोटैशियम" },
  nutrientPhosphorus: { en: "Phosphorus", hi: "फ़ॉस्फ़ोरस" },
  nutrientSodium: { en: "Sodium", hi: "सोडियम" },
  nutrientProtein: { en: "Protein", hi: "प्रोटीन" },
  nutrientFluid: { en: "Fluid", hi: "तरल" },
  perPortion: { en: "Per portion", hi: "प्रति सर्विंग" },
  todaysBudget: { en: "Today's budget", hi: "आज का बजट" },
  ofLimit: { en: "of", hi: "/" },
  avgDaily: { en: "Average daily nutrients", hi: "प्रतिदिन औसत पोषक तत्व" },
  avgVsLimit: { en: "Avg / daily limit", hi: "औसत / दैनिक सीमा" },

  // Onboarding
  onboardingWelcome: { en: "Welcome!", hi: "स्वागत है!" },
  onboardingIntro: {
    en: "Tell us your stage so we can personalize food safety guidance for you.",
    hi: "अपनी अवस्था बताएँ ताकि हम आपके लिए भोजन सुरक्षा मार्गदर्शन को व्यक्तिगत बना सकें।",
  },
  stagePreDialysis: { en: "Pre-dialysis CKD", hi: "प्री-डायलिसिस CKD" },
  stagePreDialysisDesc: {
    en: "You have chronic kidney disease but are not yet on dialysis.",
    hi: "आपको दीर्घकालिक किडनी रोग है पर अभी डायलिसिस पर नहीं हैं।",
  },
  stageDialysis: { en: "On Dialysis", hi: "डायलिसिस पर" },
  stageDialysisDesc: {
    en: "You are on hemodialysis or peritoneal dialysis. We'll tighten Yellow foods to Red.",
    hi: "आप हीमोडायलिसिस या पेरिटोनियल डायलिसिस पर हैं। हम पीले खाद्य को लाल कर देंगे।",
  },
  stageContinue: { en: "Continue", hi: "जारी रखें" },
  stageSkip: { en: "Skip for now", hi: "अभी छोड़ें" },
  stageBack: { en: "Back", hi: "पीछे" },
  stageStep: { en: "Step", hi: "चरण" },

  // Diabetic step
  diabeticQuestion: { en: "Are you diabetic?", hi: "क्या आपको मधुमेह है?" },
  diabeticSub: {
    en: "We'll flag high-sugar foods and adjust AI advice accordingly.",
    hi: "हम अधिक शक्कर वाले भोजन को चिन्हित करेंगे और AI सलाह उसी के अनुसार देंगे।",
  },
  yes: { en: "Yes", hi: "हाँ" },
  no: { en: "No", hi: "नहीं" },
  diabetic: { en: "Diabetic", hi: "मधुमेह" },

  // Doctor limits
  doctorLimitsTitle: { en: "Your doctor's targets", hi: "आपके डॉक्टर के लक्ष्य" },
  doctorLimitsSub: {
    en: "Enter any daily limits your nephrologist set for you. Leave blank to use stage-based defaults.",
    hi: "यदि आपके नेफ्रोलॉजिस्ट ने कोई दैनिक सीमा तय की है तो दर्ज करें। स्टेज-आधारित डिफ़ॉल्ट के लिए खाली छोड़ें।",
  },
  doctorLimitsSave: { en: "Save targets", hi: "लक्ष्य सहेजें" },
  personalisedForYou: { en: "Personalized for you", hi: "आपके लिए वैयक्तिकृत" },

  // Health profile section on settings
  healthProfile: { en: "Health profile", hi: "स्वास्थ्य प्रोफ़ाइल" },
  stage: { en: "CKD stage", hi: "CKD स्तर" },
  editStage: { en: "Change stage", hi: "स्तर बदलें" },
  editLimits: { en: "Doctor targets", hi: "डॉक्टर के लक्ष्य" },
  usingDefaults: { en: "Using stage defaults", hi: "स्टेज-आधारित डिफ़ॉल्ट" },

  // Favorites
  favoritesTitle: { en: "My Favorites", hi: "पसंदीदा" },
  favoritesEmpty: { en: "No favorites yet. Tap the ★ on any food to save it here.", hi: "अभी कोई पसंदीदा नहीं। किसी भोजन पर ★ दबाकर सहेजें।" },
  favorite: { en: "Favorite", hi: "पसंदीदा" },
  unfavorite: { en: "Unfavorite", hi: "पसंदीदा हटाएँ" },
  quickLog: { en: "Log", hi: "लॉग" },

  // Weekly report
  weeklyReport: { en: "Weekly Report", hi: "साप्ताहिक रिपोर्ट" },
  reportForNephro: { en: "For your nephrologist", hi: "अपने नेफ्रोलॉजिस्ट के लिए" },
  share: { en: "Share PDF", hi: "PDF साझा करें" },
  weekOf: { en: "Week of", hi: "सप्ताह" },
  totalMeals: { en: "Total meals", hi: "कुल भोजन" },
  topSafe: { en: "Top safe foods", hi: "शीर्ष सुरक्षित भोजन" },
  topAvoid: { en: "Foods to reduce", hi: "कम करने योग्य भोजन" },
  reportEmpty: { en: "Log some meals this week to generate a report.", hi: "रिपोर्ट के लिए इस सप्ताह कुछ भोजन दर्ज करें।" },

  // Scan
  scanTitle: { en: "Scan a food", hi: "भोजन स्कैन करें" },
  scanIntro: { en: "Take a photo of any dish. AI will identify it and check kidney safety.", hi: "किसी भी व्यंजन की तस्वीर लें। AI इसे पहचानेगा और किडनी सुरक्षा जाँचेगा।" },
  scanTakePhoto: { en: "Take Photo", hi: "तस्वीर लें" },
  scanRetake: { en: "Retake", hi: "फिर से लें" },
  scanAnalyze: { en: "Analyze", hi: "विश्लेषण" },
  scanAnalyzing: { en: "Analyzing dish...", hi: "व्यंजन का विश्लेषण..." },
  scanPermissionTitle: { en: "Camera permission needed", hi: "कैमरा अनुमति आवश्यक" },
  scanPermissionBody: { en: "We need camera access to identify foods with AI.", hi: "AI से भोजन पहचानने के लिए कैमरा अनुमति आवश्यक है।" },
  grantPermission: { en: "Grant Permission", hi: "अनुमति दें" },
  openSettings: { en: "Open Settings", hi: "सेटिंग्स खोलें" },
  seeMore: { en: "See full details", hi: "पूरी जानकारी देखें" },

  // Scan modes / Barcode
  scanModeVision: {
    en: "Food photo",
    hi: "भोजन फ़ोटो",
    ta: "உணவு புகைப்படம்",
    bn: "খাবারের ছবি",
    mr: "जेवणाचा फोटो",
  },
  scanModeBarcode: {
    en: "Barcode",
    hi: "बारकोड",
    ta: "பார்கோடு",
    bn: "বারকোড",
    mr: "बारकोड",
  },
  barcodeIntro: {
    en: "Point the camera at a packaged food's barcode. We'll check kidney safety from Open Food Facts.",
    hi: "पैकेज्ड फूड के बारकोड पर कैमरा रखें। हम Open Food Facts से किडनी सुरक्षा जाँचेंगे।",
    ta: "பொதி செய்யப்பட்ட உணவின் பார்கோடில் கேமராவை நோக்கவும். சிறுநீரக பாதுகாப்பை Open Food Facts வழியாக சரிபார்ப்போம்.",
    bn: "প্যাকেটজাত খাবারের বারকোডে ক্যামেরা তাক করুন। আমরা Open Food Facts থেকে কিডনি নিরাপত্তা যাচাই করব।",
    mr: "पॅकेज्ड फूडच्या बारकोडवर कॅमेरा ठेवा. Open Food Facts वरून किडनी सुरक्षा तपासू.",
  },
  barcodeAlignHint: {
    en: "Align the barcode inside the frame",
    hi: "बारकोड को फ्रेम में रखें",
    ta: "பார்கோடை சட்டத்திற்குள் வையுங்கள்",
    bn: "বারকোডটি ফ্রেমের ভেতরে রাখুন",
    mr: "बारकोड चौकटीत ठेवा",
  },
  barcodeLookingUp: {
    en: "Looking up barcode…",
    hi: "बारकोड खोज रहे हैं…",
    ta: "பார்கோடு தேடப்படுகிறது…",
    bn: "বারকোড খোঁজা হচ্ছে…",
    mr: "बारकोड शोधत आहोत…",
  },
  barcodeNotFound: {
    en: "Product not found. Try scanning again or use the photo mode.",
    hi: "उत्पाद नहीं मिला। दुबारा स्कैन करें या फ़ोटो मोड का उपयोग करें।",
    ta: "தயாரிப்பு கிடைக்கவில்லை. மீண்டும் ஸ்கேன் செய்யவும் அல்லது புகைப்பட முறையைப் பயன்படுத்தவும்.",
    bn: "পণ্য পাওয়া যায়নি। আবার স্ক্যান করুন বা ফটো মোড ব্যবহার করুন।",
    mr: "उत्पाद सापडले नाही. पुन्हा स्कॅन करा किंवा फोटो मोड वापरा.",
  },
  barcodeRescan: {
    en: "Scan another",
    hi: "फिर से स्कैन",
    ta: "மீண்டும் ஸ்கேன்",
    bn: "আবার স্ক্যান",
    mr: "पुन्हा स्कॅन",
  },
  brand: {
    en: "Brand",
    hi: "ब्रांड",
    ta: "பிராண்ட்",
    bn: "ব্র্যান্ড",
    mr: "ब्रँड",
  },
  pendingResourcing: {
    en: "🕒 Pending re-sourcing",
    hi: "🕒 डेटा पुनः स्रोत की प्रतीक्षा",
    ta: "🕒 மீள்-மூல தேடலுக்கு காத்திருக்கிறது",
    bn: "🕒 পুনরায়-সোর্সিং অপেক্ষমাণ",
    mr: "🕒 पुन्हा-सोर्सिंग प्रलंबित",
  },
  menuFruits: {
    en: "Fruit Guide",
    hi: "फल गाइड",
    ta: "பழ வழிகாட்டி",
    bn: "ফল গাইড",
    mr: "फळांचे मार्गदर्शन",
  },
  menuFruitsSub: {
    en: "Which fruits are kidney-safe",
    hi: "कौन से फल किडनी के लिए सुरक्षित हैं",
    ta: "எந்த பழங்கள் சிறுநீரகத்திற்கு பாதுகாப்பானவை",
    bn: "কোন ফলগুলি কিডনির জন্য নিরাপদ",
    mr: "कोणती फळे किडनीसाठी सुरक्षित आहेत",
  },
  menuBeverages: {
    en: "Beverage Guide",
    hi: "पेय पदार्थ गाइड",
    ta: "பானங்கள் வழிகாட்டி",
    bn: "পানীয় গাইড",
    mr: "पेय मार्गदर्शन",
  },
  menuBeveragesSub: {
    en: "Chai, coconut water, juices — safe vs avoid",
    hi: "चाय, नारियल पानी, जूस — सुरक्षित बनाम परहेज",
    ta: "தேநீர், இளநீர், சாறுகள் — பாதுகாப்பானவை vs தவிர்க்கவேண்டியவை",
    bn: "চা, নারকেল জল, রস — নিরাপদ বনাম এড়ানো",
    mr: "चहा, नारळपाणी, ज्यूस — सुरक्षित vs टाळावे",
  },
  beverageGuideTitle: {
    en: "Beverage Guide",
    hi: "पेय पदार्थ गाइड",
    ta: "பானங்கள் வழிகாட்டி",
    bn: "পানীয় গাইড",
    mr: "पेय मार्गदर्शन",
  },
  beverageGuideSubtitle: {
    en: "Drink smart — potassium + fluid count together",
    hi: "समझदारी से पिएं — पोटैशियम और तरल दोनों साथ गिने जाते हैं",
  },
  beverageGuideIntro: {
    en: "For beverages, both potassium AND fluid volume matter. Every glass counts toward your daily fluid limit, even water. Milk-based drinks (chai, lassi, malt drinks) also add phosphorus. Check your dietitian's budget for both.",
    hi: "पेय पदार्थों में पोटैशियम और तरल मात्रा दोनों महत्वपूर्ण हैं। पानी सहित हर गिलास आपकी दैनिक तरल सीमा में गिना जाता है। दूध वाले पेय (चाय, लस्सी, माल्ट) फास्फोरस भी बढ़ाते हैं।",
  },
  menuVegetables: { en: "Vegetables Guide", hi: "सब्जी गाइड" },
  menuVegetablesSub: { en: "Which veggies are kidney-safe", hi: "कौन सी सब्जियां किडनी के लिए सुरक्षित हैं" },
  vegetableGuideTitle: { en: "Vegetables Guide", hi: "सब्जी गाइड" },
  vegetableGuideSubtitle: { en: "Daily sabzis to safest choices", hi: "रोज़ की सब्ज़ी से लेकर सबसे सुरक्षित विकल्प" },
  vegetableGuideIntro: { en: "Potassium content varies widely by vegetable. Leafy greens and root vegetables (potato, sweet potato, yam) concentrate potassium heavily; gourds (lauki, tinda, turai) are the safest daily choices. Boiling and draining (leaching) can cut potato potassium by ~50%.", hi: "पोटैशियम की मात्रा सब्जी के अनुसार बहुत बदलती है। पत्तेदार सब्जियां और जड़-सब्जियां (आलू, शकरकंदी, सूरन) पोटैशियम में उच्च होती हैं; लौकी, टिंडा, तुरई सबसे सुरक्षित दैनिक विकल्प हैं।" },
  menuSnacks: { en: "Snacks Guide", hi: "स्नैक्स गाइड" },
  menuSnacksSub: { en: "Namkeen, chips, biscuits — safe vs avoid", hi: "नमकीन, चिप्स, बिस्किट — सुरक्षित बनाम परहेज" },
  menuProteins: { en: "Proteins Guide", hi: "प्रोटीन गाइड" },
  menuProteinsSub: { en: "Dals, eggs, chicken, paneer — how much is safe", hi: "दाल, अंडा, चिकन, पनीर — कितना सुरक्षित" },
  menuGrains: { en: "Grains & Rotis Guide", hi: "अनाज और रोटी गाइड" },
  menuGrainsSub: { en: "Rice, atta, millets — pick kidney-safe carbs", hi: "चावल, आटा, बाजरा — किडनी-सुरक्षित अनाज चुनें" },
  snackGuideTitle: { en: "Snacks Guide", hi: "स्नैक्स गाइड" },
  snackGuideSubtitle: { en: "The hidden sodium & phosphorus danger", hi: "छुपा हुआ सोडियम और फास्फोरस खतरा" },
  snackGuideIntro: { en: "Snacks are the sneakiest source of sodium and phosphorus in an Indian diet. A single small pack of namkeen can contain 1000+ mg sodium — nearly half a day's budget. Roasted makhana and homemade khakhra are the safest daily options.", hi: "स्नैक्स भारतीय भोजन में सोडियम और फास्फोरस का सबसे बड़ा छुपा हुआ स्रोत हैं। नमकीन के एक छोटे पैकेट में ही 1000+ मिग्रा सोडियम हो सकता है। भुना मखाना और घर का खाखरा सबसे सुरक्षित विकल्प हैं।" },
  proteinGuideTitle: { en: "Proteins Guide", hi: "प्रोटीन गाइड" },
  proteinGuideSubtitle: { en: "Getting enough protein without overloading K & phosphorus", hi: "पोटैशियम और फास्फोरस बढ़ाए बिना पर्याप्त प्रोटीन" },
  proteinGuideIntro: { en: "Protein is essential — especially on dialysis — but Indian favourites like rajma, palak paneer and full glasses of milk push kidneys hard. Egg whites, small pieces of grilled chicken/fish, and small dal portions (with the first boil water drained) are the safest daily choices.", hi: "प्रोटीन ज़रूरी है — खासकर डायलिसिस पर — लेकिन राजमा, पालक पनीर और पूरा गिलास दूध किडनी पर भारी होते हैं। अंडे का सफेद भाग, ग्रिल्ड चिकन/मछली का छोटा टुकड़ा, और छोटी दाल की मात्रा (पहला उबला पानी निकालकर) सबसे सुरक्षित हैं।" },
  grainGuideTitle: { en: "Grains & Rotis Guide", hi: "अनाज और रोटी गाइड" },
  grainGuideSubtitle: { en: "Why refined grains are often kinder to kidneys", hi: "क्यों रिफाइंड अनाज किडनी के लिए बेहतर हो सकते हैं" },
  grainGuideIntro: { en: "Whole grains are healthy for most people, but for CKD they carry extra phosphorus. White rice, suji, maida roti and vermicelli are usually safer daily staples than multigrain roti, ragi or muesli. Rotate whole-wheat atta with white rice and skip 'multigrain' loaves.", hi: "साबुत अनाज ज़्यादातर लोगों के लिए अच्छे हैं, लेकिन CKD में इनमें अधिक फास्फोरस होता है। सफेद चावल, सूजी, मैदा रोटी और सेवइयां रोज़ के लिए मल्टीग्रेन रोटी, रागी या मूसली से सुरक्षित हैं। आटा रोटी को सफेद चावल के साथ बदलते रहें।" },
  fruitGuideTitle: {
    en: "Fruit Guide",
    hi: "फल गाइड",
    ta: "பழ வழிகாட்டி",
    bn: "ফল গাইড",
    mr: "फळांचे मार्गदर्शन",
  },
  fruitGuideSubtitle: {
    en: "What to eat, watch, and avoid",
    hi: "क्या खाएं, संभल कर खाएं, और परहेज करें",
  },
  fruitGuideIntro: {
    en: "Potassium is the main concern with fruit. Serving sizes matter — a large fruit or a whole cup pushes even a safe fruit into caution. Always check with your dietitian and stay within your daily potassium budget.",
    hi: "फलों में मुख्य चिंता पोटैशियम की होती है। मात्रा महत्वपूर्ण है — बड़ा फल या पूरा कप सुरक्षित फल को भी सावधानी में डाल सकता है। हमेशा अपने डाइटिशियन से जांच लें और अपने दैनिक पोटैशियम बजट में रहें।",
  },
  logThisPack: {
    en: "Log this pack",
    hi: "इस पैक को लॉग करें",
    ta: "இந்தப் பொதியை பதிவு செய்யவும்",
    bn: "এই প্যাকটি লগ করুন",
    mr: "हे पॅक लॉग करा",
  },
  packLogged: {
    en: "Added to today's log ✓",
    hi: "आज के लॉग में जोड़ा ✓",
    ta: "இன்றைய பதிவில் சேர்க்கப்பட்டது ✓",
    bn: "আজকের লগে যোগ হয়েছে ✓",
    mr: "आजच्या लॉगमध्ये जोडले ✓",
  },
  perPackNutrients: {
    en: "Per pack vs your daily budget",
    hi: "प्रति पैक बनाम आपका दैनिक बजट",
    ta: "ஒரு பொதிக்கு உங்கள் தினசரி பட்ஜெட்டுக்கு எதிராக",
    bn: "প্রতি প্যাক বনাম আপনার দৈনিক বাজেট",
    mr: "प्रति पॅक विरुद्ध तुमचा दैनिक बजेट",
  },
} as const;

export type TKey = keyof typeof translations;

const LANG_LABELS: Record<Lang, string> = {
  en: "English",
  hi: "हिन्दी",
  ta: "தமிழ்",
  bn: "বাংলা",
  mr: "मराठी",
};

export const SUPPORTED_LANGS: Lang[] = ["en", "hi", "ta", "bn", "mr"];

export function langLabel(l: Lang): string {
  return LANG_LABELS[l];
}

export function t(lang: Lang, key: TKey): string {
  const entry = translations[key];
  return (entry[lang] as string | undefined) ?? entry.en;
}
