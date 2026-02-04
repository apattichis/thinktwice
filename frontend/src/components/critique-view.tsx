"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, Search } from "lucide-react";
import { StepCard } from "./step-card";
import { cn } from "@/lib/utils";
import type { CritiqueState, Severity } from "@/types";

interface CritiqueViewProps {
  state: CritiqueState;
}

const severityStyles: Record<Severity, { label: string; bg: string; text: string }> = {
  high: { label: "High", bg: "bg-error/10", text: "text-error" },
  medium: { label: "Medium", bg: "bg-warning/10", text: "text-warning" },
  low: { label: "Low", bg: "bg-success/10", text: "text-success" },
};

export function CritiqueView({ state }: CritiqueViewProps) {
  const data = state.data;

  return (
    <StepCard
      title="Critique"
      status={state.status}
      color="var(--color-critique)"
      duration={state.duration_ms}
    >
      {data ? (
        <div className="space-y-6">
          {/* Issues */}
          {data.issues.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium text-text-secondary">
                <AlertTriangle className="w-4 h-4" />
                Issues Found
              </div>
              <div className="space-y-2">
                {data.issues.map((issue, i) => {
                  const style = severityStyles[issue.severity];
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className={cn(
                        "p-3 rounded-lg border border-border-subtle",
                        style.bg
                      )}
                    >
                      <div className="flex items-start gap-2">
                        <span
                          className={cn(
                            "text-xs font-semibold uppercase px-2 py-0.5 rounded",
                            style.text,
                            style.bg
                          )}
                        >
                          {style.label}
                        </span>
                        <p className="text-sm text-text-secondary flex-1">
                          {issue.description}
                        </p>
                      </div>
                      {issue.quote && (
                        <p className="mt-2 text-xs text-text-muted italic pl-4 border-l-2 border-border">
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
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium text-text-secondary">
                <CheckCircle className="w-4 h-4" />
                Strengths
              </div>
              <div className="space-y-1.5">
                {data.strengths.map((strength, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-start gap-2 text-sm text-text-secondary"
                  >
                    <span className="text-success mt-0.5">✓</span>
                    {strength}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Claims to verify */}
          {data.claims_to_verify.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium text-text-secondary">
                <Search className="w-4 h-4" />
                Claims to Verify
              </div>
              <div className="space-y-1.5">
                {data.claims_to_verify.map((claim, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-start gap-2 text-sm text-text-secondary"
                  >
                    <span className="text-verify mt-0.5">→</span>
                    {claim}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Confidence */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-text-muted">Initial Confidence</span>
              <span className="font-mono font-medium text-text-secondary">
                {data.confidence}%
              </span>
            </div>
            <div className="h-2 bg-surface-elevated rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{
                  backgroundColor:
                    data.confidence >= 70
                      ? "var(--color-success)"
                      : data.confidence >= 40
                      ? "var(--color-warning)"
                      : "var(--color-error)",
                }}
                initial={{ width: 0 }}
                animate={{ width: `${data.confidence}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>
        </div>
      ) : state.status === "running" ? (
        <div className="flex items-center justify-center py-8 text-text-muted">
          Analyzing for issues...
        </div>
      ) : null}
    </StepCard>
  );
}
