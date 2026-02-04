"use client";

import { motion } from "framer-motion";
import { Check, Loader2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StepStatus } from "@/types";

interface Step {
  name: string;
  label: string;
  color: string;
}

const steps: Step[] = [
  { name: "draft", label: "Draft", color: "#6366f1" },
  { name: "critique", label: "Critique", color: "#f59e0b" },
  { name: "verify", label: "Verify", color: "#8b5cf6" },
  { name: "refine", label: "Refine", color: "#10b981" },
];

interface PipelineStepperProps {
  statuses: Record<string, StepStatus>;
  durations: Record<string, number | undefined>;
}

export function PipelineStepper({ statuses, durations }: PipelineStepperProps) {
  return (
    <div className="py-6">
      {/* Desktop - horizontal */}
      <div className="hidden sm:flex items-center justify-between max-w-xl mx-auto relative">
        {/* Background line */}
        <div className="absolute top-5 left-6 right-6 h-0.5 bg-border-subtle" />

        {steps.map((step, i) => {
          const status = statuses[step.name] || "idle";
          const duration = durations[step.name];
          const isComplete = status === "complete";
          const isRunning = status === "running";
          const isIdle = status === "idle";

          return (
            <div key={step.name} className="relative flex flex-col items-center gap-3 z-10">
              {/* Connector line (completed) */}
              {i > 0 && statuses[steps[i - 1].name] === "complete" && (
                <motion.div
                  className="absolute top-5 right-full h-0.5 mr-3"
                  style={{
                    width: "calc(100% - 24px)",
                    backgroundColor: steps[i - 1].color,
                  }}
                  initial={{ scaleX: 0, transformOrigin: "left" }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: 0.5 }}
                />
              )}

              {/* Step circle */}
              <div className="relative">
                {isRunning && (
                  <motion.div
                    className="absolute inset-0 rounded-full blur-lg"
                    style={{ backgroundColor: step.color }}
                    animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0.2, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                )}

                <motion.div
                  className={cn(
                    "relative w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                    isIdle && "border-border-default bg-bg-secondary",
                    (isRunning || isComplete) && "border-transparent"
                  )}
                  style={{
                    backgroundColor: isComplete || isRunning ? step.color : undefined,
                    boxShadow: isComplete ? `0 4px 15px ${step.color}40` : undefined,
                  }}
                  animate={isRunning ? { scale: [1, 1.05, 1] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  {isComplete ? (
                    <Check className="w-5 h-5 text-white" strokeWidth={2.5} />
                  ) : isRunning ? (
                    <Loader2 className="w-5 h-5 text-white animate-spin" />
                  ) : (
                    <Circle className="w-4 h-4 text-text-quaternary" />
                  )}
                </motion.div>
              </div>

              {/* Label */}
              <div className="text-center">
                <p
                  className={cn(
                    "text-xs font-semibold uppercase tracking-wider transition-colors",
                    isIdle ? "text-text-quaternary" : "text-text-secondary"
                  )}
                  style={{ color: isComplete || isRunning ? step.color : undefined }}
                >
                  {step.label}
                </p>
                {duration !== undefined && (
                  <p className="text-xs text-text-quaternary mt-1 font-mono">
                    {(duration / 1000).toFixed(1)}s
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Mobile - compact horizontal */}
      <div className="flex sm:hidden items-center justify-between px-4">
        {steps.map((step, i) => {
          const status = statuses[step.name] || "idle";
          const isComplete = status === "complete";
          const isRunning = status === "running";
          const isIdle = status === "idle";

          return (
            <div key={step.name} className="flex items-center">
              {/* Step indicator */}
              <div className="flex flex-col items-center gap-1">
                <motion.div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all",
                    isIdle && "border-border-default bg-bg-secondary",
                    (isRunning || isComplete) && "border-transparent"
                  )}
                  style={{
                    backgroundColor: isComplete || isRunning ? step.color : undefined,
                  }}
                  animate={isRunning ? { scale: [1, 1.1, 1] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  {isComplete ? (
                    <Check className="w-4 h-4 text-white" strokeWidth={2.5} />
                  ) : isRunning ? (
                    <Loader2 className="w-4 h-4 text-white animate-spin" />
                  ) : (
                    <span className="text-xs text-text-quaternary font-medium">{i + 1}</span>
                  )}
                </motion.div>
                <span
                  className={cn(
                    "text-[10px] font-medium uppercase tracking-wider",
                    isIdle ? "text-text-quaternary" : "text-text-secondary"
                  )}
                  style={{ color: isComplete || isRunning ? step.color : undefined }}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector */}
              {i < steps.length - 1 && (
                <div className="w-6 h-0.5 mx-1 bg-border-subtle relative">
                  {isComplete && (
                    <motion.div
                      className="absolute inset-0"
                      style={{ backgroundColor: step.color }}
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ duration: 0.3 }}
                    />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
