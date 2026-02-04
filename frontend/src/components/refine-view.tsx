"use client";

import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { ArrowUp, CheckCircle, Wand2 } from "lucide-react";
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
      color="#10b981"
      duration={state.duration_ms}
    >
      <div className="space-y-6">
        {/* Content */}
        {state.content && (
          <div className="prose max-w-none">
            <ReactMarkdown>{state.content}</ReactMarkdown>
          </div>
        )}

        {/* Changes */}
        {state.changes_made.length > 0 && (
          <div className="pt-6 border-t border-border-subtle">
            <div className="flex items-center gap-2 text-sm font-medium text-text-secondary mb-4">
              <CheckCircle className="w-4 h-4 text-success" />
              Improvements Made
              <span className="ml-auto text-xs text-text-quaternary font-normal">
                {state.changes_made.length} changes
              </span>
            </div>
            <div className="grid gap-2">
              {state.changes_made.map((change, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-start gap-3 text-sm text-text-secondary"
                >
                  <span className="text-success mt-0.5">→</span>
                  {change}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Confidence */}
        {state.status === "complete" && (
          <div className="pt-6 border-t border-border-subtle">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-text-tertiary">Confidence Improvement</span>
              <div className="flex items-center gap-3 font-mono">
                <span className="text-text-quaternary">{confidenceBefore}%</span>
                <ArrowUp
                  className={`w-4 h-4 ${
                    delta > 0
                      ? "text-success"
                      : delta < 0
                      ? "text-error rotate-180"
                      : "text-text-quaternary"
                  }`}
                />
                <span className="text-xl font-bold text-text-primary">{confidenceAfter}%</span>
                {delta !== 0 && (
                  <span
                    className={`text-sm font-semibold px-2 py-0.5 rounded-md ${
                      delta > 0 ? "text-success bg-success/10" : "text-error bg-error/10"
                    }`}
                  >
                    {delta > 0 ? "+" : ""}
                    {delta}
                  </span>
                )}
              </div>
            </div>

            {/* Progress bar comparison */}
            <div className="relative h-4 bg-bg-elevated rounded-full overflow-hidden">
              {/* Before */}
              <div
                className="absolute inset-y-0 left-0 bg-text-quaternary/30 rounded-full"
                style={{ width: `${confidenceBefore}%` }}
              />
              {/* After */}
              <motion.div
                className="absolute inset-y-0 left-0 rounded-full"
                style={{
                  background:
                    confidenceAfter >= 70
                      ? "linear-gradient(90deg, #10b981, #34d399)"
                      : confidenceAfter >= 40
                      ? "linear-gradient(90deg, #f59e0b, #fbbf24)"
                      : "linear-gradient(90deg, #ef4444, #f87171)",
                }}
                initial={{ width: `${confidenceBefore}%` }}
                animate={{ width: `${confidenceAfter}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            </div>
          </div>
        )}

        {state.status === "running" && !state.content && (
          <div className="flex items-center justify-center gap-3 py-12 text-text-tertiary">
            <Wand2 className="w-5 h-5" />
            <span>Refining with corrections...</span>
          </div>
        )}
      </div>
    </StepCard>
  );
}
