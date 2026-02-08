"use client";

import { useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "tt_api_key";

export function useApiKey() {
  const [apiKey, setApiKeyState] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);

  // Hydrate from sessionStorage on mount (SSR-safe)
  useEffect(() => {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) setApiKeyState(stored);
    setHydrated(true);
  }, []);

  const setApiKey = useCallback((key: string) => {
    sessionStorage.setItem(STORAGE_KEY, key);
    setApiKeyState(key);
  }, []);

  const clearApiKey = useCallback(() => {
    sessionStorage.removeItem(STORAGE_KEY);
    setApiKeyState(null);
  }, []);

  return { apiKey, setApiKey, clearApiKey, hasKey: !!apiKey, hydrated };
}
