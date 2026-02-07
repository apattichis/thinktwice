"use client";

import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { Sparkles, Clock, TrendingUp, CheckCircle, Shield } from "lucide-react";
import type { TrustDecision, PipelineMetrics } from "@/types";

interface FinalAnswerViewProps {
  content: string;
  trustDecision?: TrustDecision;
  metrics?: PipelineMetrics;
}

export function FinalAnswerView({ content, trustDecision, metrics }: FinalAnswerViewProps) {
  const winner = trustDecision?.winner || metrics?.trust_winner;
  const delta = metrics
    ? metrics.confidence_after - metrics.confidence_before
    : undefined;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="rounded-xl overflow-hidden"
      style={{
        background: "rgba(255, 255, 255, 0.75)",
        backdropFilter: "blur(40px) saturate(200%)",
        WebkitBackdropFilter: "blur(40px) saturate(200%)",
        boxShadow:
          "0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(0, 0, 0, 0.04)",
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-3" style={{ padding: "28px 36px 12px" }}>
        <div
          className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, #007AFF, #5856D6)",
            boxShadow: "0 2px 8px rgba(88, 86, 214, 0.2)",
          }}
        >
          <Sparkles className="w-3.5 h-3.5 text-white" />
        </div>
        <h3
          className="text-[15px] font-semibold tracking-tight"
          style={{ color: "#1d1d1f" }}
        >
          Answer
        </h3>
      </div>

      {/* Content */}
      <div style={{ padding: "0 36px 28px" }}>
        <div className="prose max-w-none prose-p:text-[15px] prose-p:leading-relaxed prose-p:text-[#1d1d1f] prose-headings:text-[#1d1d1f] prose-li:text-[#1d1d1f] prose-strong:text-[#1d1d1f]">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>

      {/* Metrics footer */}
      {metrics && (
        <div
          className="flex flex-wrap items-center gap-x-5 gap-y-2"
          style={{
            padding: "14px 36px",
            borderTop: "1px solid rgba(0,0,0,0.04)",
          }}
        >
          {/* Duration */}
          <div className="flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-[#aeaeb2]" />
            <span className="text-[12px] text-[#86868b] font-mono">
              {(metrics.total_duration_ms / 1000).toFixed(1)}s
            </span>
          </div>

          {/* Confidence delta */}
          {delta !== undefined && delta !== 0 && (
            <div className="flex items-center gap-1.5">
              <TrendingUp className="w-3 h-3 text-[#aeaeb2]" />
              <span
                className="text-[12px] font-mono font-medium"
                style={{ color: delta > 0 ? "#34C759" : "#FF3B30" }}
              >
                {delta > 0 ? "+" : ""}
                {delta}% confidence
              </span>
            </div>
          )}

          {/* Claims verified */}
          {metrics.claims_checked > 0 && (
            <div className="flex items-center gap-1.5">
              <CheckCircle className="w-3 h-3 text-[#aeaeb2]" />
              <span className="text-[12px] text-[#86868b]">
                {metrics.claims_verified} verified
              </span>
            </div>
          )}

          {/* Trust winner */}
          {winner && winner !== "N/A" && (
            <div className="flex items-center gap-1.5">
              <Shield className="w-3 h-3 text-[#aeaeb2]" />
              <span
                className="text-[12px] font-medium capitalize"
                style={{
                  color: winner === "draft" ? "#5856D6" : "#34C759",
                }}
              >
                {winner}
              </span>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
}
