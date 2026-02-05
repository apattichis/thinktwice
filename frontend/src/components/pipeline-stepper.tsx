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
  { name: "draft", label: "Draft", color: "#5856D6" },
  { name: "critique", label: "Critique", color: "#FF9500" },
  { name: "verify", label: "Verify", color: "#AF52DE" },
  { name: "refine", label: "Refine", color: "#34C759" },
];

interface PipelineStepperProps {
  statuses: Record<string, StepStatus>;
  durations: Record<string, number | undefined>;
}

export function PipelineStepper({ statuses, durations }: PipelineStepperProps) {
  return (
    <div className="py-4">
      {/* Desktop */}
      <div className="hidden sm:flex items-center justify-between max-w-lg mx-auto relative">
        {/* Background track */}
        <div className="absolute top-[18px] left-8 right-8 h-[2px] bg-border-default rounded-full" />

        {steps.map((step, i) => {
          const status = statuses[step.name] || "idle";
          const duration = durations[step.name];
          const isComplete = status === "complete";
          const isRunning = status === "running";
          const isIdle = status === "idle";

          return (
            <div key={step.name} className="relative flex flex-col items-center gap-2 z-10">
              {/* Filled connector */}
              {i > 0 && statuses[steps[i - 1].name] === "complete" && (
                <motion.div
                  className="absolute top-[18px] right-full h-[2px] mr-4"
                  style={{
                    width: "calc(100% - 8px)",
                    backgroundColor: steps[i - 1].color,
                  }}
                  initial={{ scaleX: 0, transformOrigin: "left" }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                />
              )}

              {/* Circle */}
              <div className="relative">
                {isRunning && (
                  <motion.div
                    className="absolute -inset-1 rounded-full opacity-20"
                    style={{ backgroundColor: step.color }}
                    animate={{ scale: [1, 1.4, 1], opacity: [0.3, 0.1, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                )}

                <motion.div
                  className={cn(
                    "relative w-9 h-9 rounded-full flex items-center justify-center transition-all duration-300",
                    isIdle && "bg-bg-secondary border-2 border-border-default",
                    (isRunning || isComplete) && "border-0"
                  )}
                  style={{
                    backgroundColor: isComplete || isRunning ? step.color : undefined,
                    boxShadow: isComplete ? `0 2px 8px ${step.color}30` : undefined,
                  }}
                  animate={isRunning ? { scale: [1, 1.04, 1] } : {}}
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
              </div>

              {/* Label */}
              <div className="text-center">
                <p
                  className={cn(
                    "text-[11px] font-semibold uppercase tracking-wider transition-colors",
                    isIdle ? "text-text-quaternary" : "text-text-secondary"
                  )}
                  style={{ color: isComplete || isRunning ? step.color : undefined }}
                >
                  {step.label}
                </p>
                {duration !== undefined && (
                  <p className="text-[11px] text-text-quaternary mt-0.5 font-mono">
                    {(duration / 1000).toFixed(1)}s
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Mobile */}
      <div className="flex sm:hidden items-center justify-between px-2">
        {steps.map((step, i) => {
          const status = statuses[step.name] || "idle";
          const isComplete = status === "complete";
          const isRunning = status === "running";
          const isIdle = status === "idle";

          return (
            <div key={step.name} className="flex items-center">
              <div className="flex flex-col items-center gap-1">
                <motion.div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center transition-all",
                    isIdle && "bg-bg-secondary border-2 border-border-default",
                    (isRunning || isComplete) && "border-0"
                  )}
                  style={{
                    backgroundColor: isComplete || isRunning ? step.color : undefined,
                  }}
                  animate={isRunning ? { scale: [1, 1.08, 1] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  {isComplete ? (
                    <Check className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
                  ) : isRunning ? (
                    <Loader2 className="w-3.5 h-3.5 text-white animate-spin" />
                  ) : (
                    <span className="text-[11px] text-text-quaternary font-medium">{i + 1}</span>
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

              {i < steps.length - 1 && (
                <div className="w-5 h-[2px] mx-1 bg-border-default rounded-full relative">
                  {isComplete && (
                    <motion.div
                      className="absolute inset-0 rounded-full"
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
