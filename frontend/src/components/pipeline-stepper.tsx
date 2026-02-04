"use client";

import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StepStatus } from "@/types";

interface Step {
  name: string;
  label: string;
  color: string;
}

const steps: Step[] = [
  { name: "draft", label: "Draft", color: "var(--color-draft)" },
  { name: "critique", label: "Critique", color: "var(--color-critique)" },
  { name: "verify", label: "Verify", color: "var(--color-verify)" },
  { name: "refine", label: "Refine", color: "var(--color-refine)" },
];

interface PipelineStepperProps {
  statuses: Record<string, StepStatus>;
  durations: Record<string, number | undefined>;
}

export function PipelineStepper({ statuses, durations }: PipelineStepperProps) {
  return (
    <div className="flex items-center justify-between max-w-2xl mx-auto py-6">
      {steps.map((step, i) => {
        const status = statuses[step.name] || "idle";
        const duration = durations[step.name];
        const isComplete = status === "complete";
        const isRunning = status === "running";
        const isIdle = status === "idle";

        return (
          <div key={step.name} className="flex items-center flex-1">
            {/* Step indicator */}
            <div className="flex flex-col items-center gap-2">
              <motion.div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                  isIdle && "border-border bg-transparent",
                  isRunning && "border-transparent",
                  isComplete && "border-transparent"
                )}
                style={{
                  backgroundColor: isComplete || isRunning ? step.color : undefined,
                  borderColor: isRunning ? step.color : undefined,
                }}
                animate={isRunning ? { scale: [1, 1.05, 1] } : {}}
                transition={{ repeat: Infinity, duration: 1.5 }}
              >
                {isComplete ? (
                  <Check className="w-5 h-5 text-white" />
                ) : isRunning ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <span
                    className="text-sm font-medium"
                    style={{ color: isIdle ? "var(--color-text-muted)" : "white" }}
                  >
                    {i + 1}
                  </span>
                )}
              </motion.div>

              <span
                className={cn(
                  "text-xs font-medium uppercase tracking-wider transition-colors",
                  isIdle ? "text-text-muted" : "text-text-secondary"
                )}
                style={{ color: isComplete || isRunning ? step.color : undefined }}
              >
                {step.label}
              </span>

              {duration !== undefined && (
                <span className="text-xs text-text-muted font-mono">
                  {(duration / 1000).toFixed(1)}s
                </span>
              )}
            </div>

            {/* Connector */}
            {i < steps.length - 1 && (
              <div className="flex-1 h-0.5 mx-4 bg-border relative overflow-hidden">
                <motion.div
                  className="absolute inset-y-0 left-0"
                  style={{ backgroundColor: step.color }}
                  initial={{ width: 0 }}
                  animate={{ width: isComplete ? "100%" : 0 }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
