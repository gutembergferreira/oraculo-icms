import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { API_BASE_URL } from "../config";

export type AuthUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_superuser: boolean;
};

export type AuthContextValue = {
  user: AuthUser | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
  authenticate: (accessToken: string, refreshToken: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const ACCESS_KEY = "oraculo.access";
const REFRESH_KEY = "oraculo.refresh";

const readStorage = (key: string): string | null => {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(key);
};

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    const error = detail?.detail ?? response.statusText;
    throw new Error(typeof error === "string" ? error : "Falha na requisição");
  }
  return response.json() as Promise<T>;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(() => readStorage(ACCESS_KEY));
  const [refreshToken, setRefreshToken] = useState<string | null>(() => readStorage(REFRESH_KEY));
  const [loading, setLoading] = useState<boolean>(true);

  const persistTokens = useCallback((access: string, refresh: string) => {
    setAccessToken(access);
    setRefreshToken(refresh);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(ACCESS_KEY, access);
      window.localStorage.setItem(REFRESH_KEY, refresh);
    }
  }, []);

  const clearTokens = useCallback(() => {
    setAccessToken(null);
    setRefreshToken(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(ACCESS_KEY);
      window.localStorage.removeItem(REFRESH_KEY);
    }
  }, []);

  const fetchProfile = useCallback(async () => {
    if (!accessToken) {
      setUser(null);
      return;
    }
    try {
      const profile = await request<AuthUser>(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
      setUser(profile);
    } catch (error) {
      console.error("Erro ao carregar perfil", error);
      setUser(null);
      clearTokens();
    }
  }, [accessToken, clearTokens]);

  useEffect(() => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    fetchProfile().finally(() => setLoading(false));
  }, [accessToken, fetchProfile]);

  const authenticate = useCallback(
    async (access: string, refresh: string) => {
      persistTokens(access, refresh);
      await fetchProfile();
    },
    [fetchProfile, persistTokens]
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await request<{ access_token: string; refresh_token: string }>(
        `${API_BASE_URL}/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password }),
        }
      );
      await authenticate(tokens.access_token, tokens.refresh_token);
    },
    [authenticate]
  );

  const refreshProfile = useCallback(async () => {
    await fetchProfile();
  }, [fetchProfile]);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, [clearTokens]);

  const value = useMemo(
    () => ({ user, accessToken, loading, login, logout, refreshProfile, authenticate }),
    [user, accessToken, loading, login, logout, refreshProfile, authenticate]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser utilizado dentro de AuthProvider");
  }
  return context;
};
