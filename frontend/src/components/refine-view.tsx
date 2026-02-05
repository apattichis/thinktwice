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
      color="#34C759"
      duration={state.duration_ms}
    >
      <div className="space-y-5">
        {/* Content */}
        {state.content && (
          <div className="prose max-w-none">
            <ReactMarkdown>{state.content}</ReactMarkdown>
          </div>
        )}

        {/* Changes */}
        {state.changes_made.length > 0 && (
          <div className="pt-5 border-t border-border-subtle">
            <div className="flex items-center gap-2 text-[13px] font-medium text-text-primary mb-3">
              <CheckCircle className="w-4 h-4 text-success" />
              Improvements Made
              <span className="ml-auto text-[11px] text-text-quaternary font-normal">
                {state.changes_made.length} changes
              </span>
            </div>
            <div className="grid gap-1.5">
              {state.changes_made.map((change, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="flex items-start gap-2.5 text-[13px] text-text-secondary"
                >
                  <span className="text-success mt-0.5 shrink-0">&#8250;</span>
                  {change}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Confidence */}
        {state.status === "complete" && (
          <div className="pt-5 border-t border-border-subtle">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[13px] text-text-tertiary">Confidence Improvement</span>
              <div className="flex items-center gap-2.5 font-mono">
                <span className="text-sm text-text-quaternary">{confidenceBefore}%</span>
                <ArrowUp
                  className={`w-3.5 h-3.5 ${
                    delta > 0
                      ? "text-success"
                      : delta < 0
                      ? "text-error rotate-180"
                      : "text-text-quaternary"
                  }`}
                />
                <span className="text-lg font-bold text-text-primary">{confidenceAfter}%</span>
                {delta !== 0 && (
                  <span
                    className={`text-xs font-semibold px-1.5 py-0.5 rounded-md ${
                      delta > 0 ? "text-success bg-success/10" : "text-error bg-error/10"
                    }`}
                  >
                    {delta > 0 ? "+" : ""}
                    {delta}
                  </span>
                )}
              </div>
            </div>

            <div className="relative h-2 bg-bg-primary rounded-full overflow-hidden">
              <div
                className="absolute inset-y-0 left-0 bg-text-quaternary/20 rounded-full"
                style={{ width: `${confidenceBefore}%` }}
              />
              <motion.div
                className="absolute inset-y-0 left-0 rounded-full"
                style={{
                  background:
                    confidenceAfter >= 70
                      ? "#34C759"
                      : confidenceAfter >= 40
                      ? "#FF9500"
                      : "#FF3B30",
                }}
                initial={{ width: `${confidenceBefore}%` }}
                animate={{ width: `${confidenceAfter}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>
        )}

        {state.status === "running" && !state.content && (
          <div className="flex items-center justify-center gap-3 py-10 text-text-tertiary">
            <Wand2 className="w-5 h-5" />
            <span className="text-sm">Refining with corrections...</span>
          </div>
        )}
      </div>
    </StepCard>
  );
}
