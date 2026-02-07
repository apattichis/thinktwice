"use client";

import { motion } from "framer-motion";
import { Zap, RotateCcw, Loader2 } from "lucide-react";
import type { GateState } from "@/types";

interface GateViewProps {
  state: GateState;
}

export function GateView({ state }: GateViewProps) {
  if (state.status === "idle") return null;

  const isFastPath = state.decision?.decision === "skip";
  const isRunning = state.status === "running";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="rounded-xl border border-border-default overflow-hidden"
      style={{
        background: "rgba(255, 255, 255, 0.5)",
        backdropFilter: "blur(40px) saturate(200%)",
        WebkitBackdropFilter: "blur(40px) saturate(200%)",
      }}
    >
      <div className="px-4 py-3 flex items-center gap-2.5">
        <div
          className="w-6 h-6 rounded-lg flex items-center justify-center"
          style={{
            backgroundColor: isRunning
              ? "rgba(255, 149, 0, 0.1)"
              : isFastPath
              ? "rgba(52, 199, 89, 0.1)"
              : "rgba(255, 149, 0, 0.1)",
          }}
        >
          {isRunning ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: "#FF9500" }} />
          ) : isFastPath ? (
            <Zap className="w-3.5 h-3.5" style={{ color: "#34C759" }} />
          ) : (
            <RotateCcw className="w-3.5 h-3.5" style={{ color: "#FF9500" }} />
          )}
        </div>

        {isRunning ? (
          <span className="text-[13px] text-text-tertiary">
            Evaluating draft quality...
          </span>
        ) : isFastPath ? (
          <span className="text-[13px] text-text-secondary">
            <span className="font-semibold" style={{ color: "#34C759" }}>Fast Path</span>
            {" "}&mdash; Draft quality is sufficient, skipping refinement
          </span>
        ) : (
          <span className="text-[13px] text-text-secondary">
            <span className="font-semibold" style={{ color: "#FF9500" }}>Needs Refinement</span>
            {" "}&mdash; Proceeding with critique, verification, and refinement
          </span>
        )}

        {state.decision?.confidence !== undefined && (
          <span className="ml-auto text-[11px] text-text-quaternary font-mono shrink-0">
            {state.decision.confidence}% confident
          </span>
        )}
      </div>
    </motion.div>
  );
}
