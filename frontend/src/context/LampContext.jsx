import { createContext, useContext, useState, useEffect, useCallback } from "react";

const LAMP_STORAGE_KEY = "lamp_auth_on";

const LampContext = createContext(null);

export function LampProvider({ children }) {
  const [lampOn, setLampOn] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  // Restore persisted lamp state on mount (sessionStorage survives reloads).
  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(LAMP_STORAGE_KEY);
      if (stored === "true") {
        setLampOn(true);
      }
    } catch {
      // sessionStorage may be unavailable (private mode restrictions, SSR, etc.)
    }
    setHydrated(true);
  }, []);

  // Persist every change so refresh/navigation preserves the intended state.
  useEffect(() => {
    if (!hydrated) return;
    try {
      sessionStorage.setItem(LAMP_STORAGE_KEY, String(lampOn));
    } catch {
      // Ignore persistence failures; state still works in-memory.
    }
  }, [lampOn, hydrated]);

  const toggleLamp = useCallback(() => {
    setLampOn((prev) => !prev);
  }, []);

  const value = { lampOn, setLampOn, toggleLamp, hydrated };

  return <LampContext.Provider value={value}>{children}</LampContext.Provider>;
}

export function useLamp() {
  const context = useContext(LampContext);
  if (!context) {
    throw new Error("useLamp must be used within a LampProvider");
  }
  return context;
}