"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, Search, Scan } from "lucide-react";
import { StepCard } from "./step-card";
import { cn } from "@/lib/utils";
import type { CritiqueState, Severity } from "@/types";

interface CritiqueViewProps {
  state: CritiqueState;
}

const severityStyles: Record<Severity, { label: string; bg: string; border: string; text: string }> = {
  high: { label: "High", bg: "bg-error/5", border: "border-error/20", text: "text-error" },
  medium: { label: "Medium", bg: "bg-warning/5", border: "border-warning/20", text: "text-warning" },
  low: { label: "Low", bg: "bg-success/5", border: "border-success/20", text: "text-success" },
};

export function CritiqueView({ state }: CritiqueViewProps) {
  const data = state.data;

  return (
    <StepCard
      title="Critique"
      status={state.status}
      color="#f59e0b"
      duration={state.duration_ms}
    >
      {data ? (
        <div className="space-y-8">
          {/* Issues */}
          {data.issues.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-text-secondary mb-4">
                <AlertTriangle className="w-4 h-4 text-warning" />
                Issues Identified
                <span className="ml-auto text-xs text-text-quaternary font-normal">
                  {data.issues.length} found
                </span>
              </div>
              <div className="space-y-3">
                {data.issues.map((issue, i) => {
                  const style = severityStyles[issue.severity];
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className={cn(
                        "p-4 rounded-xl border",
                        style.bg,
                        style.border
                      )}
                    >
                      <div className="flex items-start gap-3">
                        <span
                          className={cn(
                            "shrink-0 text-xs font-bold uppercase px-2 py-1 rounded-md",
                            style.text,
                            style.bg
                          )}
                        >
                          {style.label}
                        </span>
                        <p className="text-sm text-text-secondary leading-relaxed">
                          {issue.description}
                        </p>
                      </div>
                      {issue.quote && (
                        <p className="mt-3 text-xs text-text-tertiary italic pl-4 border-l-2 border-border-default">
                          &ldquo;{issue.quote}&rdquo;
                        </p>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Strengths */}
          {data.strengths.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-text-secondary mb-4">
                <CheckCircle className="w-4 h-4 text-success" />
                Strengths
              </div>
              <div className="grid gap-2">
                {data.strengths.map((strength, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-start gap-3 text-sm text-text-secondary"
                  >
                    <span className="text-success mt-0.5 text-lg leading-none">✓</span>
                    {strength}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Claims */}
          {data.claims_to_verify.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-text-secondary mb-4">
                <Search className="w-4 h-4 text-brand" />
                Claims to Verify
                <span className="ml-auto text-xs text-text-quaternary font-normal">
                  {data.claims_to_verify.length} claims
                </span>
              </div>
              <div className="grid gap-2">
                {data.claims_to_verify.map((claim, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-start gap-3 p-3 rounded-lg bg-bg-tertiary/50 text-sm text-text-secondary"
                  >
                    <span className="text-brand mt-0.5">→</span>
                    {claim}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Confidence */}
          <div className="pt-4 border-t border-border-subtle">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-text-tertiary">Initial Confidence</span>
              <span className="text-lg font-bold font-mono text-text-primary">
                {data.confidence}%
              </span>
            </div>
            <div className="h-3 bg-bg-elevated rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{
                  background:
                    data.confidence >= 70
                      ? "linear-gradient(90deg, #10b981, #34d399)"
                      : data.confidence >= 40
                      ? "linear-gradient(90deg, #f59e0b, #fbbf24)"
                      : "linear-gradient(90deg, #ef4444, #f87171)",
                }}
                initial={{ width: 0 }}
                animate={{ width: `${data.confidence}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            </div>
          </div>
        </div>
      ) : state.status === "running" ? (
        <div className="flex items-center justify-center gap-3 py-12 text-text-tertiary">
          <Scan className="w-5 h-5" />
          <span>Analyzing for issues...</span>
        </div>
      ) : null}
    </StepCard>
  );
}
