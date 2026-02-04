"use client";

import { motion } from "framer-motion";
import { ExternalLink, AlertTriangle, CheckCircle, XCircle, HelpCircle, Globe } from "lucide-react";
import { StepCard } from "./step-card";
import { cn } from "@/lib/utils";
import type { VerifyState, Verdict } from "@/types";

interface VerifyViewProps {
  state: VerifyState;
}

const verdictConfig: Record<Verdict, { icon: typeof CheckCircle; label: string; color: string; bg: string; border: string }> = {
  verified: {
    icon: CheckCircle,
    label: "Verified",
    color: "text-success",
    bg: "bg-success/5",
    border: "border-success/20",
  },
  refuted: {
    icon: XCircle,
    label: "Refuted",
    color: "text-error",
    bg: "bg-error/5",
    border: "border-error/20",
  },
  unclear: {
    icon: HelpCircle,
    label: "Unclear",
    color: "text-warning",
    bg: "bg-warning/5",
    border: "border-warning/20",
  },
};

export function VerifyView({ state }: VerifyViewProps) {
  return (
    <StepCard
      title="Verify"
      status={state.status}
      color="#8b5cf6"
      duration={state.duration_ms}
    >
      <div className="space-y-4">
        {/* Warning */}
        {!state.web_verified && state.results.length > 0 && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-warning/5 border border-warning/20">
            <AlertTriangle className="w-5 h-5 text-warning shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-warning">Limited Verification</p>
              <p className="text-xs text-warning/80 mt-1">
                Verified using AI knowledge only. Add a search API key for web-based fact checking.
              </p>
            </div>
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
                    "p-4 rounded-xl border",
                    config.bg,
                    config.border
                  )}
                >
                  <div className="flex items-start gap-4">
                    <div className={cn("shrink-0 w-8 h-8 rounded-lg flex items-center justify-center", config.bg)}>
                      <Icon className={cn("w-5 h-5", config.color)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={cn("text-xs font-bold uppercase", config.color)}>
                          {config.label}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-text-primary mb-2">
                        {result.claim}
                      </p>
                      <p className="text-sm text-text-secondary leading-relaxed">
                        {result.explanation}
                      </p>
                      {result.source && (
                        <a
                          href={result.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 mt-3 text-xs text-brand-light hover:text-brand transition-colors"
                        >
                          <ExternalLink className="w-3 h-3" />
                          {result.source_title || "View Source"}
                        </a>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        ) : state.status === "running" ? (
          <div className="flex items-center justify-center gap-3 py-12 text-text-tertiary">
            <Globe className="w-5 h-5 animate-pulse" />
            <span>Verifying claims against sources...</span>
          </div>
        ) : state.status === "complete" ? (
          <div className="flex items-center justify-center gap-3 py-12 text-text-quaternary">
            <CheckCircle className="w-5 h-5" />
            <span>No claims required verification</span>
          </div>
        ) : null}
      </div>
    </StepCard>
  );
}
