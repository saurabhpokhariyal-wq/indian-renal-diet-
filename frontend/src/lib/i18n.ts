export type Lang = "en" | "hi";

export const translations = {
  appName: { en: "Indian Renal Diet", hi: "इंडियन रीनल डाइट" },
  tagline: { en: "Smart food swaps for kidney health", hi: "किडनी के लिए स्मार्ट फूड स्वैप" },

  tabSearch: { en: "Search", hi: "खोज" },
  tabMeals: { en: "Meals", hi: "भोजन" },
  tabAI: { en: "Ask AI", hi: "AI से पूछें" },
  tabSettings: { en: "Settings", hi: "सेटिंग्स" },

  loginTitle: { en: "Welcome back", hi: "फिर से स्वागत है" },
  loginSubtitle: { en: "Sign in to your kidney-safe diet coach", hi: "अपने किडनी-सुरक्षित डाइट कोच में साइन इन करें" },
  registerTitle: { en: "Create account", hi: "खाता बनाएँ" },
  registerSubtitle: { en: "Start your kidney-safe eating journey", hi: "किडनी-सुरक्षित खान-पान की शुरुआत करें" },
  email: { en: "Email", hi: "ईमेल" },
  password: { en: "Password", hi: "पासवर्ड" },
  fullName: { en: "Full name (optional)", hi: "पूरा नाम (वैकल्पिक)" },
  signIn: { en: "Sign In", hi: "साइन इन" },
  signUp: { en: "Sign Up", hi: "साइन अप" },
  noAccount: { en: "New here? Create an account", hi: "नए हैं? खाता बनाएँ" },
  hasAccount: { en: "Already have an account? Sign in", hi: "पहले से खाता है? साइन इन करें" },

  searchPlaceholder: { en: "Search for a food, e.g. Palak Paneer", hi: "भोजन खोजें, जैसे पालक पनीर" },
  greeting: { en: "Namaste", hi: "नमस्ते" },
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
  summarySafe: { en: "Safe", hi: "सुरक्षित" },
  summaryCaution: { en: "Caution", hi: "सावधानी" },
  summaryAvoid: { en: "Avoid", hi: "टालें" },
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
} as const;

export type TKey = keyof typeof translations;

export function t(lang: Lang, key: TKey): string {
  return translations[key][lang];
}
