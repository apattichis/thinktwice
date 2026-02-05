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
  high: { label: "High", bg: "bg-error/[0.06]", border: "border-error/15", text: "text-error" },
  medium: { label: "Medium", bg: "bg-warning/[0.06]", border: "border-warning/15", text: "text-warning" },
  low: { label: "Low", bg: "bg-success/[0.06]", border: "border-success/15", text: "text-success" },
};

export function CritiqueView({ state }: CritiqueViewProps) {
  const data = state.data;

  return (
    <StepCard
      title="Critique"
      status={state.status}
      color="#FF9500"
      duration={state.duration_ms}
    >
      {data ? (
        <div className="space-y-6">
          {/* Issues */}
          {data.issues.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-[13px] font-medium text-text-primary mb-3">
                <AlertTriangle className="w-4 h-4 text-warning" />
                Issues Identified
                <span className="ml-auto text-[11px] text-text-quaternary font-normal">
                  {data.issues.length} found
                </span>
              </div>
              <div className="space-y-2.5">
                {data.issues.map((issue, i) => {
                  const style = severityStyles[issue.severity];
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.04 }}
                      className={cn("p-3.5 rounded-xl border", style.bg, style.border)}
                    >
                      <div className="flex items-start gap-2.5">
                        <span className={cn("shrink-0 text-[11px] font-bold uppercase px-1.5 py-0.5 rounded-md", style.text, style.bg)}>
                          {style.label}
                        </span>
                        <p className="text-[13px] text-text-secondary leading-relaxed">
                          {issue.description}
                        </p>
                      </div>
                      {issue.quote && (
                        <p className="mt-2.5 text-xs text-text-tertiary italic pl-3.5 border-l-2 border-border-default">
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
              <div className="flex items-center gap-2 text-[13px] font-medium text-text-primary mb-3">
                <CheckCircle className="w-4 h-4 text-success" />
                Strengths
              </div>
              <div className="grid gap-1.5">
                {data.strengths.map((strength, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="flex items-start gap-2.5 text-[13px] text-text-secondary"
                  >
                    <CheckCircle className="w-3.5 h-3.5 text-success shrink-0 mt-0.5" />
                    {strength}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Claims */}
          {data.claims_to_verify.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-[13px] font-medium text-text-primary mb-3">
                <Search className="w-4 h-4 text-brand" />
                Claims to Verify
                <span className="ml-auto text-[11px] text-text-quaternary font-normal">
                  {data.claims_to_verify.length} claims
                </span>
              </div>
              <div className="grid gap-1.5">
                {data.claims_to_verify.map((claim, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="flex items-start gap-2.5 p-2.5 rounded-lg bg-bg-primary text-[13px] text-text-secondary"
                  >
                    <span className="text-brand mt-0.5 shrink-0">&#8250;</span>
                    {claim}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Confidence */}
          <div className="pt-4 border-t border-border-subtle">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-[13px] text-text-tertiary">Initial Confidence</span>
              <span className="text-base font-bold font-mono text-text-primary">
                {data.confidence}%
              </span>
            </div>
            <div className="h-2 bg-bg-primary rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{
                  background:
                    data.confidence >= 70
                      ? "#34C759"
                      : data.confidence >= 40
                      ? "#FF9500"
                      : "#FF3B30",
                }}
                initial={{ width: 0 }}
                animate={{ width: `${data.confidence}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>
        </div>
      ) : state.status === "running" ? (
        <div className="flex items-center justify-center gap-3 py-10 text-text-tertiary">
          <Scan className="w-5 h-5" />
          <span className="text-sm">Analyzing for issues...</span>
        </div>
      ) : null}
    </StepCard>
  );
}
