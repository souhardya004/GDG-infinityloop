import React, { createContext, useContext, useEffect, useState } from "react";
import { api, getStoredToken, setStoredToken } from "../lib/api";
import { ProvidersConfig, User } from "../types/api";

type AuthContextType = {
  user: User | null;
  token: string | null;
  loading: boolean;
  providers: ProvidersConfig | null;
  isAuthenticated: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<void>;
  signup: (payload: { email: string; password: string; username?: string; full_name?: string }) => Promise<void>;
  oauthLogin: (
    provider: "github" | "google",
    payload: { code?: string; id_token?: string; redirect_uri?: string },
  ) => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState<ProvidersConfig | null>(null);

  // Load providers config
  useEffect(() => {
    api.auth
      .providers()
      .then((cfg) => setProviders(cfg))
      .catch(() => undefined);
  }, []);

  // Check initial login state
  useEffect(() => {
    const stored = getStoredToken();
    if (!stored) {
      setLoading(false);
      return;
    }

    api.auth
      .me()
      .then((res) => {
        setUser(res.user);
        setToken(stored);
      })
      .catch(() => {
        // If token is invalid or expired
        setStoredToken(null);
        setToken(null);
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const refreshUser = async () => {
    try {
      const res = await api.auth.me();
      setUser(res.user);
    } catch {
      setUser(null);
    }
  };

  const login = async (usernameOrEmail: string, password: string) => {
    const res = await api.auth.login({ username_or_email: usernameOrEmail, password });
    setStoredToken(res.token);
    setToken(res.token);
    setUser(res.user);
  };

  const signup = async (payload: { email: string; password: string; username?: string; full_name?: string }) => {
    const res = await api.auth.signup(payload);
    setStoredToken(res.token);
    setToken(res.token);
    setUser(res.user);
  };

  const oauthLogin = async (
    provider: "github" | "google",
    payload: { code?: string; id_token?: string; redirect_uri?: string },
  ) => {
    let res;
    if (provider === "github") {
      res = await api.auth.github({ code: payload.code || "", redirect_uri: payload.redirect_uri });
    } else {
      res = await api.auth.google(payload);
    }
    setStoredToken(res.token);
    setToken(res.token);
    setUser(res.user);
  };

  const demoLogin = async () => {
    const res = await api.auth.demo();
    setStoredToken(res.token);
    setToken(res.token);
    setUser(res.user);
  };

  const logout = async () => {
    try {
      await api.auth.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      setStoredToken(null);
      setToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        providers,
        isAuthenticated: Boolean(user && token),
        login,
        signup,
        oauthLogin,
        demoLogin,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
