import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";

interface User {
  id: string;
  username: string;
}

interface Profile {
  background: string | null;
  full_name: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = useCallback(async () => {
    try {
      const res = await api.get("/api/profile");
      setProfile(res.data);
    } catch {
      setProfile({ background: null, full_name: "" });
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/api/auth/me")
      .then(async (res) => {
        setUser(res.data);
        await fetchProfile();
      })
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false));
  }, [fetchProfile]);

  const login = async (username: string, password: string) => {
    const res = await api.post("/api/auth/login", { username, password });
    localStorage.setItem("token", res.data.access_token);
    const me = await api.get("/api/auth/me");
    setUser(me.data);
    await fetchProfile();
  };

  const register = async (username: string, password: string) => {
    const res = await api.post("/api/auth/register", { username, password });
    localStorage.setItem("token", res.data.access_token);
    const me = await api.get("/api/auth/me");
    setUser(me.data);
    await fetchProfile();
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("onboarding_complete");
    setUser(null);
    setProfile(null);
  };

  return { user, profile, loading, login, register, logout, refreshProfile: fetchProfile };
}
