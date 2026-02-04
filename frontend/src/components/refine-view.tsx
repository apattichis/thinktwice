"use client";

import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { ArrowUp, CheckCircle } from "lucide-react";
import { StepCard } from "./step-card";
import type { RefineState, CritiqueState } from "@/types";

interface RefineViewProps {
  state: RefineState;
  critiqueState: CritiqueState;
}

export function RefineView({ state, critiqueState }: RefineViewProps) {
  const confidenceBefore = critiqueState.data?.confidence ?? 0;
  const confidenceAfter = state.confidence ?? confidenceBefore;
  const delta = confidenceAfter - confidenceBefore;

  return (
    <StepCard
      title="Refine"
      status={state.status}
      color="var(--color-refine)"
      duration={state.duration_ms}
    >
      <div className="space-y-6">
        {/* Refined content */}
        {state.content && (
          <div className="prose max-w-none">
            <ReactMarkdown>{state.content}</ReactMarkdown>
          </div>
        )}

        {/* Changes made */}
        {state.changes_made.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-border-subtle">
            <div className="flex items-center gap-2 text-sm font-medium text-text-secondary">
              <CheckCircle className="w-4 h-4" />
              Changes Made
            </div>
            <div className="space-y-1.5">
              {state.changes_made.map((change, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-start gap-2 text-sm text-text-secondary"
                >
                  <span className="text-refine mt-0.5">→</span>
                  {change}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Confidence comparison */}
        {state.status === "complete" && (
          <div className="space-y-3 pt-4 border-t border-border-subtle">
            <div className="flex items-center justify-between text-sm">
              <span className="text-text-muted">Confidence</span>
              <div className="flex items-center gap-2 font-mono">
                <span className="text-text-muted">{confidenceBefore}%</span>
                <ArrowUp
                  className={`w-4 h-4 ${
                    delta > 0
                      ? "text-success"
                      : delta < 0
                      ? "text-error rotate-180"
                      : "text-text-muted"
                  }`}
                />
                <span className="font-semibold text-text">{confidenceAfter}%</span>
                {delta !== 0 && (
                  <span
                    className={`text-xs ${
                      delta > 0 ? "text-success" : "text-error"
                    }`}
                  >
                    ({delta > 0 ? "+" : ""}
                    {delta})
                  </span>
                )}
              </div>
            </div>
            <div className="h-2 bg-surface-elevated rounded-full overflow-hidden relative">
              {/* Before bar (faded) */}
              <div
                className="absolute h-full rounded-full opacity-30"
                style={{
                  width: `${confidenceBefore}%`,
                  backgroundColor: "var(--color-text-muted)",
                }}
              />
              {/* After bar */}
              <motion.div
                className="h-full rounded-full relative z-10"
                style={{
                  backgroundColor:
                    confidenceAfter >= 70
                      ? "var(--color-success)"
                      : confidenceAfter >= 40
                      ? "var(--color-warning)"
                      : "var(--color-error)",
                }}
                initial={{ width: `${confidenceBefore}%` }}
                animate={{ width: `${confidenceAfter}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>
        )}

        {state.status === "running" && !state.content && (
          <div className="flex items-center justify-center py-8 text-text-muted">
            Refining with corrections...
          </div>
        )}
      </div>
    </StepCard>
  );
}
