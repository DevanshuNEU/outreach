import { useState, useEffect } from "react";
import api from "@/lib/api";

interface User {
  id: string;
  username: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/api/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const res = await api.post("/api/auth/login", { username, password });
    localStorage.setItem("token", res.data.access_token);
    const me = await api.get("/api/auth/me");
    setUser(me.data);
  };

  const register = async (username: string, password: string) => {
    const res = await api.post("/api/auth/register", { username, password });
    localStorage.setItem("token", res.data.access_token);
    const me = await api.get("/api/auth/me");
    setUser(me.data);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return { user, loading, login, register, logout };
}
