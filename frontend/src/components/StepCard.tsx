import { useState } from 'react';
import { ChevronDown, ChevronUp, Clock, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { StepStatus } from '../types';

interface StepCardProps {
  title: string;
  status: StepStatus;
  duration?: number;
  color: string;
  error?: string;
  defaultExpanded?: boolean;
  children: React.ReactNode;
}

export function StepCard({
  title,
  status,
  duration,
  color,
  error,
  defaultExpanded = true,
  children,
}: StepCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const isRunning = status === 'running';
  const isComplete = status === 'complete';
  const isError = status === 'error';
  const isPending = status === 'pending';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-card rounded-xl border overflow-hidden transition-colors ${
        isRunning ? 'border-opacity-100' : 'border-border'
      }`}
      style={{
        borderColor: isRunning ? color : undefined,
        boxShadow: isRunning ? `0 0 20px ${color}20` : undefined,
      }}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        disabled={isPending}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-elevated/50 transition-colors disabled:cursor-default"
      >
        <div className="flex items-center gap-3">
          {/* Status indicator */}
          <div
            className={`w-3 h-3 rounded-full ${
              isPending ? 'bg-muted' : ''
            }`}
            style={{ backgroundColor: isPending ? undefined : color }}
          >
            {isRunning && (
              <motion.div
                className="w-full h-full rounded-full"
                style={{ backgroundColor: color }}
                animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
              />
            )}
          </div>

          {/* Title */}
          <span
            className="step-label text-sm"
            style={{ color: isPending ? 'var(--text-muted)' : color }}
          >
            {title}
          </span>

          {/* Status badge */}
          {isRunning && (
            <span className="flex items-center gap-1 text-xs text-secondary">
              <Loader2 className="w-3 h-3 animate-spin" />
              Running...
            </span>
          )}
          {isComplete && duration !== undefined && (
            <span className="flex items-center gap-1 text-xs text-muted">
              <Clock className="w-3 h-3" />
              {(duration / 1000).toFixed(1)}s
            </span>
          )}
          {isError && (
            <span className="flex items-center gap-1 text-xs text-verdict-refuted">
              <AlertCircle className="w-3 h-3" />
              Error
            </span>
          )}
        </div>

        {/* Expand/collapse */}
        {!isPending && (
          <div className="text-muted">
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </div>
        )}
      </button>

      {/* Content */}
      <AnimatePresence>
        {isExpanded && !isPending && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-border"
          >
            <div className="px-4 py-4">
              {error ? (
                <div className="p-3 bg-verdict-refuted/10 border border-verdict-refuted/30 rounded-lg text-verdict-refuted text-sm">
                  {error}
                </div>
              ) : (
                children
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
