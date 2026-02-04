"use client";

import { useState, useCallback, useRef } from "react";
import type {
  InputMode,
  PipelineState,
  Critique,
  VerificationResult,
  PipelineMetrics,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const initialState: PipelineState = {
  isRunning: false,
  draft: { status: "idle", content: "" },
  critique: { status: "idle" },
  verify: { status: "idle", results: [], web_verified: true },
  refine: { status: "idle", content: "", changes_made: [] },
};

export function usePipeline() {
  const [state, setState] = useState<PipelineState>(initialState);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  const stop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setState((prev) => ({ ...prev, isRunning: false }));
  }, []);

  const run = useCallback(async (input: string, mode: InputMode) => {
    reset();
    setState((prev) => ({ ...prev, isRunning: true }));

    abortRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE}/api/think`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input, mode }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";
        let currentData = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7);
          } else if (line.startsWith("data: ")) {
            currentData = line.slice(6);
            if (currentEvent && currentData) {
              try {
                const data = JSON.parse(currentData);
                handleEvent(currentEvent, data);
              } catch {
                // Skip malformed JSON
              }
              currentEvent = "";
              currentData = "";
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return;
      setState((prev) => ({
        ...prev,
        isRunning: false,
        error: err instanceof Error ? err.message : "Pipeline failed",
      }));
    }

    function handleEvent(event: string, data: Record<string, unknown>) {
      switch (event) {
        case "step_start": {
          const step = data.step as string;
          if (step === "draft") {
            setState((prev) => ({
              ...prev,
              draft: { ...prev.draft, status: "running" },
            }));
          } else if (step === "critique") {
            setState((prev) => ({
              ...prev,
              critique: { ...prev.critique, status: "running" },
            }));
          } else if (step === "verify") {
            setState((prev) => ({
              ...prev,
              verify: { ...prev.verify, status: "running" },
            }));
          } else if (step === "refine") {
            setState((prev) => ({
              ...prev,
              refine: { ...prev.refine, status: "running" },
            }));
          }
          break;
        }

        case "step_stream": {
          const step = data.step as string;
          const token = data.token as string;
          if (step === "draft") {
            setState((prev) => ({
              ...prev,
              draft: { ...prev.draft, content: prev.draft.content + token },
            }));
          } else if (step === "refine") {
            setState((prev) => ({
              ...prev,
              refine: { ...prev.refine, content: prev.refine.content + token },
            }));
          }
          break;
        }

        case "step_complete": {
          const step = data.step as string;
          if (step === "draft") {
            setState((prev) => ({
              ...prev,
              draft: {
                status: "complete",
                content: (data.content as string) || prev.draft.content,
                duration_ms: data.duration_ms as number,
              },
            }));
          } else if (step === "critique") {
            setState((prev) => ({
              ...prev,
              critique: {
                status: "complete",
                data: data.content as Critique,
                duration_ms: data.duration_ms as number,
              },
            }));
          } else if (step === "verify") {
            setState((prev) => ({
              ...prev,
              verify: {
                ...prev.verify,
                status: "complete",
                duration_ms: data.duration_ms as number,
                web_verified: (data.web_verified as boolean) ?? true,
              },
            }));
          } else if (step === "refine") {
            setState((prev) => ({
              ...prev,
              refine: {
                status: "complete",
                content: (data.content as string) || prev.refine.content,
                confidence: data.confidence as number,
                changes_made: (data.changes_made as string[]) || [],
                duration_ms: data.duration_ms as number,
              },
            }));
          }
          break;
        }

        case "verify_claim": {
          const result = data as unknown as VerificationResult;
          setState((prev) => ({
            ...prev,
            verify: {
              ...prev.verify,
              results: [...prev.verify.results, result],
            },
          }));
          break;
        }

        case "pipeline_complete": {
          const metrics = data as unknown as PipelineMetrics;
          setState((prev) => ({
            ...prev,
            isRunning: false,
            metrics,
          }));
          break;
        }
      }
    }
  }, [reset]);

  return { state, run, stop, reset };
}
