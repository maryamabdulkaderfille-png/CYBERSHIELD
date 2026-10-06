import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import * as authService from "@/services/authService";
import * as settingsService from "@/services/settingsService";
import { applyTheme, watchSystemTheme } from "@/lib/theme";
import type { LoginPayload, RegisterPayload, User } from "@/types/auth";

function bootstrapTheme() {
  let currentTheme = "system" as Awaited<ReturnType<typeof settingsService.getSettings>>["theme"];
  watchSystemTheme(() => currentTheme);
  settingsService
    .getSettings()
    .then((settings) => {
      currentTheme = settings.theme;
      applyTheme(settings.theme);
    })
    // No persisted preference to read (not logged in, or the request
    // failed) — fall back to the OS/browser preference like any other
    // guest, rather than forcing dark regardless of their actual setting.
    .catch(() => applyTheme("system"));
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await authService.fetchCurrentUser();
      setUser(currentUser);
    } catch {
      // Not logged in — the normal case for the landing page and Quick
      // Scan. Theme must still be resolved for this visitor (previously it
      // wasn't: bootstrapTheme() was only reachable on the success path
      // above, so `data-theme` was never set at all for a guest and the
      // page silently fell back to the hardcoded base/dark CSS regardless
      // of their actual OS preference).
      setUser(null);
    } finally {
      bootstrapTheme();
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
  }, [refreshUser]);

  const login = useCallback(async (payload: LoginPayload) => {
    const loggedInUser = await authService.loginUser(payload);
    setUser(loggedInUser);
    bootstrapTheme();
    return loggedInUser;
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    const newUser = await authService.registerUser(payload);
    setUser(newUser);
    bootstrapTheme();
    return newUser;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authService.logoutUser();
    } finally {
      setUser(null);
      // Back to guest — same fallback as any other unauthenticated visitor.
      applyTheme("system");
    }
  }, []);

  const value = useMemo(
    () => ({ user, isLoading, isAuthenticated: user !== null, login, register, logout, refreshUser, setUser }),
    [user, isLoading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
