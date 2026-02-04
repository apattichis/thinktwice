"use client";

import { motion } from "framer-motion";
import { ExternalLink, AlertTriangle, CheckCircle, XCircle, HelpCircle } from "lucide-react";
import { StepCard } from "./step-card";
import { cn } from "@/lib/utils";
import type { VerifyState, Verdict } from "@/types";

interface VerifyViewProps {
  state: VerifyState;
}

const verdictConfig: Record<Verdict, { icon: typeof CheckCircle; label: string; color: string; bg: string }> = {
  verified: {
    icon: CheckCircle,
    label: "Verified",
    color: "text-success",
    bg: "bg-success/10",
  },
  refuted: {
    icon: XCircle,
    label: "Refuted",
    color: "text-error",
    bg: "bg-error/10",
  },
  unclear: {
    icon: HelpCircle,
    label: "Unclear",
    color: "text-warning",
    bg: "bg-warning/10",
  },
};

export function VerifyView({ state }: VerifyViewProps) {
  return (
    <StepCard
      title="Verify"
      status={state.status}
      color="var(--color-verify)"
      duration={state.duration_ms}
    >
      <div className="space-y-4">
        {/* Web verification warning */}
        {!state.web_verified && state.results.length > 0 && (
          <div className="flex items-center gap-2 p-3 bg-warning/10 border border-warning/20 rounded-lg text-sm text-warning">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>
              Verified using AI knowledge only. Add a search API key for web
              verification.
            </span>
          </div>
        )}

        {/* Results */}
        {state.results.length > 0 ? (
          <div className="space-y-3">
            {state.results.map((result, i) => {
              const config = verdictConfig[result.verdict];
              const Icon = config.icon;

              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className={cn(
                    "p-4 rounded-lg border border-border-subtle",
                    config.bg
                  )}
                >
                  <div className="flex items-start gap-3">
                    <Icon className={cn("w-5 h-5 mt-0.5 flex-shrink-0", config.color)} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={cn(
                            "text-xs font-semibold uppercase",
                            config.color
                          )}
                        >
                          {config.label}
                        </span>
                      </div>
                      <p className="text-sm text-text mb-2">{result.claim}</p>
                      <p className="text-sm text-text-secondary">
                        {result.explanation}
                      </p>
                      {result.source && (
                        <a
                          href={result.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 mt-2 text-xs text-accent hover:underline"
                        >
                          <ExternalLink className="w-3 h-3" />
                          {result.source_title || "Source"}
                        </a>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        ) : state.status === "running" ? (
          <div className="flex items-center justify-center py-8 text-text-muted">
            Verifying claims against sources...
          </div>
        ) : state.status === "complete" ? (
          <div className="flex items-center justify-center py-8 text-text-muted">
            No claims to verify
          </div>
        ) : null}
      </div>
    </StepCard>
  );
}
