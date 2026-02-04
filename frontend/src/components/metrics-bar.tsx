"use client";

import { motion } from "framer-motion";
import {
  Clock,
  TrendingUp,
  Search,
  CheckCircle,
  XCircle,
  HelpCircle,
} from "lucide-react";
import type { PipelineMetrics } from "@/types";

interface MetricsBarProps {
  metrics: PipelineMetrics;
}

export function MetricsBar({ metrics }: MetricsBarProps) {
  const delta = metrics.confidence_after - metrics.confidence_before;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface border border-border rounded-xl p-4"
    >
      <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
        {/* Duration */}
        <div className="flex items-center gap-2 text-text-secondary">
          <Clock className="w-4 h-4 text-text-muted" />
          <span className="font-mono">
            {(metrics.total_duration_ms / 1000).toFixed(1)}s
          </span>
        </div>

        <div className="w-px h-4 bg-border hidden sm:block" />

        {/* Confidence */}
        <div className="flex items-center gap-2 text-text-secondary">
          <TrendingUp className="w-4 h-4 text-text-muted" />
          <span className="font-mono">
            {metrics.confidence_before}% → {metrics.confidence_after}%
          </span>
          <span
            className={`font-mono text-xs ${
              delta > 0 ? "text-success" : delta < 0 ? "text-error" : "text-text-muted"
            }`}
          >
            ({delta > 0 ? "+" : ""}
            {delta})
          </span>
        </div>

        <div className="w-px h-4 bg-border hidden sm:block" />

        {/* Claims */}
        <div className="flex items-center gap-2 text-text-secondary">
          <Search className="w-4 h-4 text-text-muted" />
          <span className="font-mono">{metrics.claims_checked} claims</span>
        </div>

        <div className="w-px h-4 bg-border hidden sm:block" />

        {/* Verdicts */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-success">
            <CheckCircle className="w-4 h-4" />
            <span className="font-mono">{metrics.claims_verified}</span>
          </div>
          <div className="flex items-center gap-1 text-error">
            <XCircle className="w-4 h-4" />
            <span className="font-mono">{metrics.claims_refuted}</span>
          </div>
          <div className="flex items-center gap-1 text-warning">
            <HelpCircle className="w-4 h-4" />
            <span className="font-mono">{metrics.claims_unclear}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
