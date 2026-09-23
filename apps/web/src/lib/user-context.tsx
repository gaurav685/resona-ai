"use client";

import { createContext, useContext, useEffect, useState } from "react";

const STORAGE_KEY = "resona:selected-user-id";

interface UserContextValue {
  userId: string | null;
  setUserId: (id: string | null) => void;
}

const UserContext = createContext<UserContextValue>({ userId: null, setUserId: () => {} });

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserIdState] = useState<string | null>(null);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional one-time hydration from localStorage on mount
      if (stored) setUserIdState(stored);
    } catch {
      // localStorage unavailable — fall back to no persisted selection
    }
  }, []);

  const setUserId = (id: string | null) => {
    setUserIdState(id);
    try {
      if (id) window.localStorage.setItem(STORAGE_KEY, id);
      else window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  };

  return <UserContext.Provider value={{ userId, setUserId }}>{children}</UserContext.Provider>;
}

export function useUser() {
  return useContext(UserContext);
}
