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
} as const;

export type TKey = keyof typeof translations;

export function t(lang: Lang, key: TKey): string {
  return translations[key][lang];
}
