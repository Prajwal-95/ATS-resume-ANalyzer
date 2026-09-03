import { createContext, useContext, useState, useEffect } from "react";
import { authApi } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem("ats_token");
    const storedUser = localStorage.getItem("ats_user");
    if (storedToken) {
      setToken(storedToken);
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch {
          localStorage.removeItem("ats_user");
        }
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const data = await authApi.login(email, password);
    localStorage.setItem("ats_token", data.access_token);
    setToken(data.access_token);
    // Fetch user profile
    const me = await authApi.me(data.access_token);
    setUser(me);
    localStorage.setItem("ats_user", JSON.stringify(me));
    return me;
  };

  const register = async (email, username, password) => {
    const userData = await authApi.register(email, username, password);
    // Auto-login after registration
    await login(email, password);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem("ats_token");
    localStorage.removeItem("ats_user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
