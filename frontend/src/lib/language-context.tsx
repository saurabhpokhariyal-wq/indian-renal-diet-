import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { t as translate, type Lang, type TKey } from "@/src/lib/i18n";
import { storage } from "@/src/utils/storage";

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: TKey) => string;
}

const Ctx = createContext<LangCtx | null>(null);
const LANG_KEY = "renal.lang";

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    (async () => {
      const saved = await storage.getItem<string>(LANG_KEY, "");
      if (saved === "hi" || saved === "en") setLangState(saved);
    })();
  }, []);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    void storage.setItem(LANG_KEY, l);
  }, []);

  const value = useMemo<LangCtx>(
    () => ({ lang, setLang, t: (k: TKey) => translate(lang, k) }),
    [lang, setLang],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useLang() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useLang must be used inside LanguageProvider");
  return c;
}
