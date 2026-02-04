"use client";

import { motion } from "framer-motion";
import {
  Clock,
  TrendingUp,
  Search,
  CheckCircle,
  XCircle,
  AlertCircle,
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
      className="rounded-2xl border border-border-subtle bg-gradient-to-br from-bg-secondary to-bg-tertiary p-4 sm:p-6"
    >
      {/* Mobile layout */}
      <div className="grid grid-cols-2 gap-4 sm:hidden">
        {/* Duration */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-bg-elevated flex items-center justify-center">
            <Clock className="w-4 h-4 text-text-tertiary" />
          </div>
          <div>
            <p className="text-[10px] text-text-quaternary uppercase tracking-wider">Time</p>
            <p className="text-base font-semibold text-text-primary font-mono">
              {(metrics.total_duration_ms / 1000).toFixed(1)}s
            </p>
          </div>
        </div>

        {/* Confidence */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-bg-elevated flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-text-tertiary" />
          </div>
          <div>
            <p className="text-[10px] text-text-quaternary uppercase tracking-wider">Confidence</p>
            <p className="text-base font-semibold font-mono">
              <span className="text-text-primary">{metrics.confidence_after}%</span>
              <span
                className={`ml-1 text-xs ${
                  delta > 0 ? "text-success" : delta < 0 ? "text-error" : "text-text-quaternary"
                }`}
              >
                {delta > 0 ? "+" : ""}{delta}
              </span>
            </p>
          </div>
        </div>

        {/* Verdicts - full width */}
        <div className="col-span-2 flex items-center justify-center gap-6 pt-3 border-t border-border-subtle">
          <span className="flex items-center gap-1.5 text-success font-mono text-sm">
            <CheckCircle className="w-4 h-4" />
            {metrics.claims_verified}
          </span>
          <span className="flex items-center gap-1.5 text-error font-mono text-sm">
            <XCircle className="w-4 h-4" />
            {metrics.claims_refuted}
          </span>
          <span className="flex items-center gap-1.5 text-warning font-mono text-sm">
            <AlertCircle className="w-4 h-4" />
            {metrics.claims_unclear}
          </span>
        </div>
      </div>

      {/* Desktop layout */}
      <div className="hidden sm:flex flex-wrap items-center justify-center gap-8">
        {/* Duration */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-bg-elevated flex items-center justify-center">
            <Clock className="w-5 h-5 text-text-tertiary" />
          </div>
          <div>
            <p className="text-xs text-text-quaternary uppercase tracking-wider">Duration</p>
            <p className="text-lg font-semibold text-text-primary font-mono">
              {(metrics.total_duration_ms / 1000).toFixed(1)}s
            </p>
          </div>
        </div>

        <div className="w-px h-12 bg-border-subtle" />

        {/* Confidence */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-bg-elevated flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-text-tertiary" />
          </div>
          <div>
            <p className="text-xs text-text-quaternary uppercase tracking-wider">Confidence</p>
            <p className="text-lg font-semibold font-mono">
              <span className="text-text-tertiary">{metrics.confidence_before}%</span>
              <span className="text-text-quaternary mx-2">→</span>
              <span className="text-text-primary">{metrics.confidence_after}%</span>
              <span
                className={`ml-2 text-sm ${
                  delta > 0 ? "text-success" : delta < 0 ? "text-error" : "text-text-quaternary"
                }`}
              >
                {delta > 0 ? "+" : ""}
                {delta}
              </span>
            </p>
          </div>
        </div>

        <div className="w-px h-12 bg-border-subtle" />

        {/* Claims */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-bg-elevated flex items-center justify-center">
            <Search className="w-5 h-5 text-text-tertiary" />
          </div>
          <div>
            <p className="text-xs text-text-quaternary uppercase tracking-wider">Claims Checked</p>
            <div className="flex items-center gap-4 mt-1">
              <span className="flex items-center gap-1.5 text-success font-mono">
                <CheckCircle className="w-4 h-4" />
                {metrics.claims_verified}
              </span>
              <span className="flex items-center gap-1.5 text-error font-mono">
                <XCircle className="w-4 h-4" />
                {metrics.claims_refuted}
              </span>
              <span className="flex items-center gap-1.5 text-warning font-mono">
                <AlertCircle className="w-4 h-4" />
                {metrics.claims_unclear}
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
