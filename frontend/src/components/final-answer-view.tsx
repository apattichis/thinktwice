"use client";

import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { Sparkles, Trophy, FileText, ArrowRight } from "lucide-react";
import type { TrustDecision, PipelineMetrics } from "@/types";

interface FinalAnswerViewProps {
  content: string;
  trustDecision?: TrustDecision;
  metrics?: PipelineMetrics;
}

export function FinalAnswerView({ content, trustDecision, metrics }: FinalAnswerViewProps) {
  const winner = trustDecision?.winner || metrics?.trust_winner || "refined";
  const draftScore = trustDecision?.draft_score;
  const refinedScore = trustDecision?.refined_score;
  const reason = trustDecision?.reason;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="relative rounded-2xl overflow-hidden"
      style={{
        background: "rgba(255, 255, 255, 0.75)",
        backdropFilter: "blur(40px) saturate(200%)",
        WebkitBackdropFilter: "blur(40px) saturate(200%)",
        boxShadow:
          "0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(0, 0, 0, 0.04)",
      }}
    >
      {/* Accent bar */}
      <div
        className="h-[3px]"
        style={{
          background: "linear-gradient(90deg, #007AFF 0%, #5856D6 35%, #AF52DE 65%, #34C759 100%)",
        }}
      />

      {/* Header */}
      <div className="px-6 pt-5 pb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{
              background: "linear-gradient(135deg, #007AFF, #5856D6)",
              boxShadow: "0 2px 8px rgba(88, 86, 214, 0.25)",
            }}
          >
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-[15px] font-semibold text-text-primary tracking-tight">
              Final Answer
            </h3>
            {reason && (
              <p className="text-[12px] text-text-tertiary mt-0.5 max-w-md truncate">
                {reason}
              </p>
            )}
          </div>
        </div>

        {/* Trust badge */}
        <div className="flex items-center gap-2">
          {draftScore !== undefined && refinedScore !== undefined && (
            <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-text-quaternary font-mono">
              <FileText className="w-3 h-3" />
              {draftScore}
              <ArrowRight className="w-3 h-3" />
              <Trophy className="w-3 h-3" />
              {refinedScore}
            </div>
          )}
          <span
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold uppercase tracking-wider"
            style={{
              backgroundColor:
                winner === "draft"
                  ? "rgba(88, 86, 214, 0.08)"
                  : winner === "blended"
                  ? "rgba(175, 82, 222, 0.08)"
                  : "rgba(52, 199, 89, 0.08)",
              color:
                winner === "draft"
                  ? "#5856D6"
                  : winner === "blended"
                  ? "#AF52DE"
                  : "#34C759",
            }}
          >
            {winner === "draft" ? "Original Draft" : winner === "blended" ? "Blended" : "Refined"}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 pb-6">
        <div className="prose max-w-none prose-p:text-[15px] prose-p:leading-relaxed prose-p:text-text-primary prose-headings:text-text-primary prose-li:text-text-primary prose-strong:text-text-primary">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </motion.div>
  );
}
