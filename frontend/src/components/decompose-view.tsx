"use client";

import { motion } from "framer-motion";
import { Layers, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DecomposeState } from "@/types";

interface DecomposeViewProps {
  state: DecomposeState;
}

const priorityStyles: Record<string, { bg: string; text: string }> = {
  high: { bg: "bg-error/[0.08]", text: "text-error" },
  medium: { bg: "bg-warning/[0.08]", text: "text-warning" },
  low: { bg: "bg-text-tertiary/[0.08]", text: "text-text-tertiary" },
};

const typeLabels: Record<string, string> = {
  content: "Content",
  reasoning: "Reasoning",
  accuracy: "Accuracy",
  format: "Format",
  tone: "Tone",
};

export function DecomposeView({ state }: DecomposeViewProps) {
  if (state.status === "idle") return null;

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
          style={{ backgroundColor: "rgba(0, 122, 255, 0.1)" }}
        >
          {state.status === "running" ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: "#007AFF" }} />
          ) : (
            <Layers className="w-3.5 h-3.5" style={{ color: "#007AFF" }} />
          )}
        </div>

        {state.status === "running" ? (
          <span className="text-[13px] text-text-tertiary">
            Analyzing your request...
          </span>
        ) : (
          <span className="text-[13px] text-text-secondary">
            Found{" "}
            <span className="font-semibold text-text-primary">
              {state.constraints.length} constraints
            </span>{" "}
            to satisfy
          </span>
        )}

        {state.duration_ms !== undefined && (
          <span className="ml-auto text-[11px] text-text-quaternary font-mono">
            {(state.duration_ms / 1000).toFixed(1)}s
          </span>
        )}
      </div>

      {state.status === "complete" && state.constraints.length > 0 && (
        <div className="px-4 pb-3 flex flex-wrap gap-1.5">
          {state.constraints.map((c, i) => {
            const priority = priorityStyles[c.priority] || priorityStyles.medium;
            return (
              <motion.span
                key={c.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.03 }}
                className={cn(
                  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[12px]",
                  "bg-bg-primary border border-border-subtle"
                )}
              >
                <span className={cn("text-[10px] font-bold uppercase", priority.text)}>
                  {typeLabels[c.type] || c.type}
                </span>
                <span className="text-text-secondary truncate max-w-[200px]">
                  {c.text}
                </span>
              </motion.span>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
