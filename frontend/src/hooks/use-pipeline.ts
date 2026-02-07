"use client";

import { useState, useCallback, useRef } from "react";
import type {
  InputMode,
  PipelineState,
  Critique,
  VerificationResult,
  PipelineMetrics,
  Constraint,
  ConstraintEvaluation,
  GateDecision,
  TrustDecision,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const initialState: PipelineState = {
  isRunning: false,
  currentIteration: 0,
  draft: { status: "idle", content: "" },
  critique: { status: "idle" },
  verify: { status: "idle", results: [], web_verified: true },
  refine: { status: "idle", content: "", changes_made: [] },
  decompose: { status: "idle", constraints: [] },
  gate: { status: "idle" },
  trust: { status: "idle" },
  constraintVerdicts: [],
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
        case "decompose_complete": {
          const constraints = ((data.constraints as Record<string, unknown>[]) || []).map(
            (c): Constraint => ({
              id: c.id as string,
              text: (c.description as string) || (c.text as string) || "",
              type: c.type as string,
              priority: c.priority as string,
            })
          );
          setState((prev) => ({
            ...prev,
            decompose: {
              status: "complete",
              constraints,
              duration_ms: data.duration_ms as number,
            },
          }));
          break;
        }

        case "gate_decision": {
          const decision: GateDecision = {
            decision: (data.gate_decision as string as "skip" | "refine") || (data.decision as "skip" | "refine"),
            confidence: (data.gate_confidence as number) ?? (data.confidence as number) ?? 0,
            sub_questions: (data.sub_questions as GateDecision["sub_questions"]) || [],
            reason: (data.reason as string) || "",
          };
          setState((prev) => ({
            ...prev,
            gate: {
              status: "complete",
              decision,
              duration_ms: data.duration_ms as number,
            },
          }));
          break;
        }

        case "constraint_verdict": {
          const verdictStr = data.verdict as string;
          const evaluation: ConstraintEvaluation = {
            constraint_id: data.constraint_id as string,
            constraint_text: (data.constraint_text as string) || (data.description as string) || "",
            verdict: (verdictStr === "partially_satisfied" ? "partial" : verdictStr) as ConstraintEvaluation["verdict"],
            confidence: (data.confidence as number) ?? 0,
            explanation: (data.feedback as string) || (data.explanation as string) || "",
          };
          setState((prev) => ({
            ...prev,
            constraintVerdicts: [...prev.constraintVerdicts, evaluation],
          }));
          break;
        }

        case "self_verify_claim": {
          // Self-verification is supplementary — verify_claim already has the combined verdict.
          // Skip adding a duplicate entry.
          break;
        }

        case "iteration_start": {
          const iteration = data.iteration as number;
          setState((prev) => ({
            ...prev,
            currentIteration: iteration,
            // Reset critique/verify/refine for new iteration
            critique: { status: "idle" },
            verify: { status: "idle", results: [], web_verified: true },
            refine: { status: "idle", content: "", changes_made: [] },
            constraintVerdicts: [],
          }));
          break;
        }

        case "iteration_complete": {
          // Convergence info -- no special UI action needed
          break;
        }

        case "trust_decision": {
          const decision: TrustDecision = {
            winner: data.winner as "draft" | "refined",
            draft_score: (data.draft_score as number) ?? 0,
            refined_score: (data.refined_score as number) ?? 0,
            reason: (data.reasoning as string) || (data.reason as string) || "",
          };
          setState((prev) => ({
            ...prev,
            trust: {
              status: "complete",
              decision,
              duration_ms: data.duration_ms as number,
            },
          }));
          break;
        }

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
          } else if (step === "decompose") {
            setState((prev) => ({
              ...prev,
              decompose: { ...prev.decompose, status: "running" },
            }));
          } else if (step === "gate") {
            setState((prev) => ({
              ...prev,
              gate: { ...prev.gate, status: "running" },
            }));
          } else if (step === "trust") {
            setState((prev) => ({
              ...prev,
              trust: { ...prev.trust, status: "running" },
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
            const raw = data.content as Record<string, unknown> | undefined;
            const critique: Critique | undefined = raw
              ? {
                  issues: (
                    (raw.constraint_evaluations as Record<string, unknown>[]) || []
                  )
                    .filter((ev) => ev.verdict !== "satisfied")
                    .map((ev) => ({
                      description:
                        (ev.feedback as string) ||
                        `Constraint ${ev.constraint_id}: ${ev.verdict}`,
                      severity: (ev.verdict === "violated" ? "high" : "medium") as "high" | "medium" | "low",
                      quote: ev.evidence_quote as string | undefined,
                    })),
                  strengths: (raw.strengths_to_preserve as string[]) || [],
                  claims_to_verify: (
                    (raw.claims_to_verify as Array<Record<string, unknown> | string>) || []
                  ).map((c) => (typeof c === "string" ? c : (c.claim as string))),
                  confidence: (raw.overall_confidence as number) ?? 0,
                }
              : undefined;
            setState((prev) => ({
              ...prev,
              critique: {
                status: "complete",
                data: critique,
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
            const rawChanges = (data.changes_made as Array<Record<string, unknown> | string>) || [];
            const changes = rawChanges.map((ch) =>
              typeof ch === "string" ? ch : (ch.change as string) || `${ch.type}: ${ch.target_id}`
            );
            setState((prev) => ({
              ...prev,
              refine: {
                status: "complete",
                content: (data.content as string) || prev.refine.content,
                confidence: (data.confidence as number) ?? (data.confidence_after as number),
                changes_made: changes,
                duration_ms: data.duration_ms as number,
              },
            }));
          }
          break;
        }

        case "verify_claim": {
          const result: VerificationResult = {
            claim: data.claim as string,
            verdict: ((data.combined_verdict as string) || (data.verdict as string)) as VerificationResult["verdict"],
            source: (data.web_source as string) || (data.source as string),
            source_title: data.source_title as string | undefined,
            explanation: (data.web_explanation as string) || (data.explanation as string) || "",
            web_verified: (data.web_verified as boolean) ?? true,
          };
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
          const { final_output, ...rest } = data;
          const metrics = rest as unknown as PipelineMetrics;
          setState((prev) => ({
            ...prev,
            isRunning: false,
            metrics,
            finalOutput: final_output as string | undefined,
          }));
          break;
        }
      }
    }
  }, [reset]);

  return { state, run, stop, reset };
}
