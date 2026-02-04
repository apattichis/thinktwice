"use client";

import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Examples {
  questions: string[];
  claims: string[];
  urls: string[];
}

export function useExamples() {
  const [examples, setExamples] = useState<Examples | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/examples`)
      .then((res) => res.json())
      .then(setExamples)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return { examples, loading };
}
