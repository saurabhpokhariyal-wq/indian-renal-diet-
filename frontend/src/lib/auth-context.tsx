import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, setToken, type Stage, type UserOut } from "@/src/lib/api";
import { storage } from "@/src/utils/storage";

interface AuthCtx {
  user: UserOut | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName?: string) => Promise<void>;
  signOut: () => Promise<void>;
  setStage: (stage: Stage) => Promise<void>;
  refresh: () => Promise<void>;
}

const Ctx = createContext<AuthCtx | null>(null);

const TOKEN_KEY = "renal.jwt";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const token = await storage.secureGet<string>(TOKEN_KEY, "");
        if (token) {
          const me = await api.me();
          setUser(me);
        }
      } catch {
        // token expired/invalid — silently reset
        await setToken(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const res = await api.login(email, password);
    await setToken(res.access_token);
    setUser(res.user);
  }, []);

  const signUp = useCallback(async (email: string, password: string, fullName?: string) => {
    const res = await api.register(email, password, fullName);
    await setToken(res.access_token);
    setUser(res.user);
  }, []);

  const signOut = useCallback(async () => {
    await setToken(null);
    setUser(null);
  }, []);

  const setStage = useCallback(async (stage: Stage) => {
    const updated = await api.setStage(stage);
    setUser(updated);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const u = await api.me();
      setUser(u);
    } catch {
      // ignore
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signUp, signOut, setStage, refresh }),
    [user, loading, signIn, signUp, signOut, setStage, refresh],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth must be used inside AuthProvider");
  return c;
}
