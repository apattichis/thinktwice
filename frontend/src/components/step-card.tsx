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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "rounded-xl border overflow-hidden transition-all duration-300",
        isRunning ? "border-opacity-100 shadow-lg" : "border-border bg-surface"
      )}
      style={{
        borderColor: isRunning ? color : undefined,
        boxShadow: isRunning ? `0 0 30px ${color}15` : undefined,
      }}
    >
      {/* Header */}
      <button
        onClick={() => !isIdle && setIsOpen(!isOpen)}
        disabled={isIdle}
        className={cn(
          "w-full flex items-center justify-between px-5 py-4 transition-colors",
          !isIdle && "hover:bg-surface-elevated cursor-pointer"
        )}
      >
        <div className="flex items-center gap-3">
          {/* Status indicator */}
          <div
            className={cn("w-2.5 h-2.5 rounded-full transition-all")}
            style={{
              backgroundColor: isIdle ? "var(--color-border)" : color,
            }}
          >
            {isRunning && (
              <motion.div
                className="w-full h-full rounded-full"
                style={{ backgroundColor: color }}
                animate={{ scale: [1, 1.8, 1], opacity: [1, 0.3, 1] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
              />
            )}
          </div>

          {/* Title */}
          <span
            className={cn(
              "text-sm font-semibold uppercase tracking-wider transition-colors"
            )}
            style={{ color: isIdle ? "var(--color-text-muted)" : color }}
          >
            {title}
          </span>

          {/* Status */}
          {isRunning && (
            <span className="flex items-center gap-1.5 text-xs text-text-secondary">
              <Loader2 className="w-3 h-3 animate-spin" />
              Processing...
            </span>
          )}

          {isComplete && duration !== undefined && (
            <span className="flex items-center gap-1.5 text-xs text-text-muted">
              <Clock className="w-3 h-3" />
              {(duration / 1000).toFixed(1)}s
            </span>
          )}
        </div>

        {/* Expand/collapse */}
        {!isIdle && (
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="text-text-muted"
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
            transition={{ duration: 0.2 }}
          >
            <div className="px-5 pb-5 border-t border-border-subtle pt-4">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
