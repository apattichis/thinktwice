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
    bg: "bg-success/[0.06]",
    border: "border-success/15",
  },
  refuted: {
    icon: XCircle,
    label: "Refuted",
    color: "text-error",
    bg: "bg-error/[0.06]",
    border: "border-error/15",
  },
  unclear: {
    icon: HelpCircle,
    label: "Unclear",
    color: "text-warning",
    bg: "bg-warning/[0.06]",
    border: "border-warning/15",
  },
};

export function VerifyView({ state }: VerifyViewProps) {
  return (
    <StepCard
      title="Verify"
      status={state.status}
      color="#AF52DE"
      duration={state.duration_ms}
    >
      <div className="space-y-3">
        {/* Warning */}
        {!state.web_verified && state.results.length > 0 && (
          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-warning/[0.06] border border-warning/15">
            <AlertTriangle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
            <div>
              <p className="text-[13px] font-medium text-warning">Limited Verification</p>
              <p className="text-xs text-text-tertiary mt-0.5">
                Verified using AI knowledge only. Add a search API key for web-based fact checking.
              </p>
            </div>
          </div>
        )}

        {/* Results */}
        {state.results.length > 0 ? (
          <div className="space-y-2.5">
            {state.results.map((result, i) => {
              const config = verdictConfig[result.verdict];
              const Icon = config.icon;

              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className={cn("p-4 rounded-xl border", config.bg, config.border)}
                >
                  <div className="flex items-start gap-3">
                    <div className={cn("shrink-0 w-7 h-7 rounded-lg flex items-center justify-center", config.bg)}>
                      <Icon className={cn("w-4 h-4", config.color)} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className={cn("text-[11px] font-bold uppercase", config.color)}>
                        {config.label}
                      </span>
                      <p className="text-[13px] font-medium text-text-primary mt-1">
                        {result.claim}
                      </p>
                      <p className="text-[13px] text-text-secondary leading-relaxed mt-1">
                        {result.explanation}
                      </p>
                      {result.source && (
                        <a
                          href={result.source}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 mt-2 text-xs text-brand hover:text-brand-dark transition-colors"
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
          <div className="flex items-center justify-center gap-3 py-10 text-text-tertiary">
            <Globe className="w-5 h-5 animate-gentle-pulse" />
            <span className="text-sm">Verifying claims against sources...</span>
          </div>
        ) : state.status === "complete" ? (
          <div className="flex items-center justify-center gap-3 py-10 text-text-quaternary">
            <CheckCircle className="w-5 h-5" />
            <span className="text-sm">No claims required verification</span>
          </div>
        ) : null}
      </div>
    </StepCard>
  );
}
