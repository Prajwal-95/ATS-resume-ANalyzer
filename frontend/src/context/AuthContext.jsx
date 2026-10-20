import { createContext, useContext, useState, useEffect } from "react";
import { authApi } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function validateSession() {
      const storedToken = localStorage.getItem("ats_token");
      const storedUser = localStorage.getItem("ats_user");

      if (!storedToken) {
        if (!cancelled) setLoading(false);
        return;
      }

      // Validate the stored JWT against the server — do NOT trust
      // localStorage alone, as the token may be expired or revoked.
      try {
        const me = await authApi.me(storedToken);
        if (cancelled) return;
        setToken(storedToken);
        setUser(me);
        // Refresh stored user data in case profile changed
        localStorage.setItem("ats_user", JSON.stringify(me));
      } catch {
        // Token is invalid, expired, or server unreachable — clear session
        if (!cancelled) {
          localStorage.removeItem("ats_token");
          localStorage.removeItem("ats_user");
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    validateSession();
    return () => { cancelled = true; };
  }, []);

  const login = async (email, password) => {
    const data = await authApi.login(email, password);
    localStorage.setItem("ats_token", data.access_token);
    setToken(data.access_token);
    // Fetch user profile to confirm token validity and get user data
    const me = await authApi.me(data.access_token);
    setUser(me);
    localStorage.setItem("ats_user", JSON.stringify(me));
    return me;
  };

  const register = async (email, username, password) => {
    const userData = await authApi.register(email, username, password);
    // Registration creates an unverified account — do NOT auto-login.
    // The user must verify their email before they can log in.
    return userData;
  };

  const verifyEmail = async (verificationToken) => {
    return authApi.verifyEmail(verificationToken);
  };

  const resendVerification = async (email) => {
    return authApi.resendVerification(email);
  };

  const forgotPassword = async (email) => {
    return authApi.forgotPassword(email);
  };

  const resetPassword = async (resetToken, newPassword) => {
    return authApi.resetPassword(resetToken, newPassword);
  };

  const logout = () => {
    localStorage.removeItem("ats_token");
    localStorage.removeItem("ats_user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        verifyEmail,
        resendVerification,
        forgotPassword,
        resetPassword,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}