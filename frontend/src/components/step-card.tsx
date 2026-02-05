"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Clock, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StepStatus } from "@/types";

interface StepCardProps {
  title: string;
  status: StepStatus;
  color: string;
  duration?: number;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export function StepCard({
  title,
  status,
  color,
  duration,
  children,
  defaultOpen = true,
}: StepCardProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const isRunning = status === "running";
  const isComplete = status === "complete";
  const isIdle = status === "idle";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="relative"
    >
      <div
        className={cn(
          "relative rounded-2xl border overflow-hidden transition-all duration-300",
          isRunning
            ? "bg-bg-secondary shadow-md shadow-black/[0.04]"
            : "bg-bg-secondary shadow-sm",
          "border-border-default"
        )}
        style={{
          borderColor: isRunning ? `${color}30` : undefined,
        }}
      >
        {/* Header */}
        <button
          onClick={() => !isIdle && setIsOpen(!isOpen)}
          disabled={isIdle}
          className={cn(
            "w-full flex items-center justify-between px-5 py-3.5 transition-colors",
            !isIdle && "hover:bg-bg-hover/50 cursor-pointer"
          )}
        >
          <div className="flex items-center gap-3">
            {/* Indicator dot */}
            <div className="relative">
              <div
                className={cn(
                  "w-2.5 h-2.5 rounded-full transition-all",
                  isIdle && "bg-text-quaternary/40"
                )}
                style={{ backgroundColor: !isIdle ? color : undefined }}
              />
              {isRunning && (
                <motion.div
                  className="absolute inset-0 rounded-full"
                  style={{ backgroundColor: color }}
                  animate={{ scale: [1, 2.5, 1], opacity: [0.6, 0, 0.6] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}
            </div>

            {/* Title */}
            <span
              className="text-[13px] font-semibold uppercase tracking-wider transition-colors"
              style={{ color: isIdle ? "var(--color-text-quaternary)" : color }}
            >
              {title}
            </span>

            {/* Status indicators */}
            {isRunning && (
              <span className="flex items-center gap-1.5 text-xs text-text-tertiary">
                <Loader2 className="w-3 h-3 animate-spin" />
                Processing
              </span>
            )}

            {isComplete && duration !== undefined && (
              <span className="flex items-center gap-1 text-[11px] text-text-quaternary font-mono">
                <Clock className="w-3 h-3" />
                {(duration / 1000).toFixed(1)}s
              </span>
            )}
          </div>

          {!isIdle && (
            <motion.div
              animate={{ rotate: isOpen ? 180 : 0 }}
              transition={{ duration: 0.2 }}
              className="text-text-quaternary"
            >
              <ChevronDown className="w-4 h-4" />
            </motion.div>
          )}
        </button>

        {/* Content */}
        <AnimatePresence initial={false}>
          {isOpen && !isIdle && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
            >
              <div className="px-5 pb-5 border-t border-border-subtle pt-4">
                {children}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
