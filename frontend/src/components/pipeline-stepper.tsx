"use client";

import { motion } from "framer-motion";
import { Check, Loader2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StepStatus } from "@/types";

interface Step {
  name: string;
  label: string;
  color: string;
  gradient: string;
}

const steps: Step[] = [
  { name: "draft", label: "Draft", color: "#6366f1", gradient: "from-indigo-500 to-blue-500" },
  { name: "critique", label: "Critique", color: "#f59e0b", gradient: "from-amber-500 to-orange-500" },
  { name: "verify", label: "Verify", color: "#8b5cf6", gradient: "from-violet-500 to-purple-500" },
  { name: "refine", label: "Refine", color: "#10b981", gradient: "from-emerald-500 to-green-500" },
];

interface PipelineStepperProps {
  statuses: Record<string, StepStatus>;
  durations: Record<string, number | undefined>;
}

export function PipelineStepper({ statuses, durations }: PipelineStepperProps) {
  return (
    <div className="relative py-8">
      {/* Progress line */}
      <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-border-subtle -translate-y-1/2" />

      <div className="relative flex justify-between max-w-xl mx-auto">
        {steps.map((step, i) => {
          const status = statuses[step.name] || "idle";
          const duration = durations[step.name];
          const isComplete = status === "complete";
          const isRunning = status === "running";
          const isIdle = status === "idle";

          return (
            <div key={step.name} className="flex flex-col items-center gap-3">
              {/* Step circle */}
              <div className="relative">
                {/* Glow for active */}
                {isRunning && (
                  <motion.div
                    className="absolute inset-0 rounded-full blur-xl"
                    style={{ backgroundColor: step.color }}
                    animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0.2, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                )}

                <motion.div
                  className={cn(
                    "relative w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-500",
                    isIdle && "border-border-default bg-bg-secondary",
                    isRunning && "border-transparent",
                    isComplete && "border-transparent"
                  )}
                  style={{
                    background: isComplete || isRunning
                      ? `linear-gradient(135deg, ${step.color}, ${step.color}dd)`
                      : undefined,
                    boxShadow: isComplete
                      ? `0 4px 20px ${step.color}40`
                      : undefined,
                  }}
                  animate={isRunning ? { scale: [1, 1.05, 1] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  {isComplete ? (
                    <Check className="w-5 h-5 text-white" strokeWidth={3} />
                  ) : isRunning ? (
                    <Loader2 className="w-5 h-5 text-white animate-spin" />
                  ) : (
                    <Circle className="w-5 h-5 text-text-quaternary" />
                  )}
                </motion.div>
              </div>

              {/* Label */}
              <div className="text-center">
                <p
                  className={cn(
                    "text-sm font-medium transition-colors",
                    isIdle ? "text-text-quaternary" : "text-text-primary"
                  )}
                  style={{ color: isComplete || isRunning ? step.color : undefined }}
                >
                  {step.label}
                </p>
                {duration !== undefined && (
                  <p className="text-xs text-text-quaternary mt-0.5 font-mono">
                    {(duration / 1000).toFixed(1)}s
                  </p>
                )}
              </div>

              {/* Connector to next */}
              {i < steps.length - 1 && (
                <motion.div
                  className="absolute top-6 h-0.5 bg-gradient-to-r"
                  style={{
                    left: `calc(${(i + 0.5) * 25}% + 24px)`,
                    width: `calc(25% - 48px)`,
                    backgroundImage: isComplete
                      ? `linear-gradient(to right, ${step.color}, ${steps[i + 1].color})`
                      : undefined,
                    backgroundColor: !isComplete ? "transparent" : undefined,
                  }}
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: isComplete ? 1 : 0 }}
                  transition={{ duration: 0.5 }}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
