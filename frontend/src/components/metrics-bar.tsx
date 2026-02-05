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
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-border-default bg-bg-secondary p-4 sm:p-5 shadow-sm"
    >
      {/* Mobile */}
      <div className="grid grid-cols-2 gap-4 sm:hidden">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-bg-primary flex items-center justify-center">
            <Clock className="w-4 h-4 text-text-tertiary" />
          </div>
          <div>
            <p className="text-[10px] text-text-quaternary uppercase tracking-wider">Time</p>
            <p className="text-sm font-semibold text-text-primary font-mono">
              {(metrics.total_duration_ms / 1000).toFixed(1)}s
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-bg-primary flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-text-tertiary" />
          </div>
          <div>
            <p className="text-[10px] text-text-quaternary uppercase tracking-wider">Confidence</p>
            <p className="text-sm font-semibold font-mono">
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

        <div className="col-span-2 flex items-center justify-center gap-5 pt-3 border-t border-border-subtle">
          <span className="flex items-center gap-1.5 text-success font-mono text-[13px]">
            <CheckCircle className="w-3.5 h-3.5" />
            {metrics.claims_verified}
          </span>
          <span className="flex items-center gap-1.5 text-error font-mono text-[13px]">
            <XCircle className="w-3.5 h-3.5" />
            {metrics.claims_refuted}
          </span>
          <span className="flex items-center gap-1.5 text-warning font-mono text-[13px]">
            <AlertCircle className="w-3.5 h-3.5" />
            {metrics.claims_unclear}
          </span>
        </div>
      </div>

      {/* Desktop */}
      <div className="hidden sm:flex flex-wrap items-center justify-center gap-7">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-bg-primary flex items-center justify-center">
            <Clock className="w-4 h-4 text-text-tertiary" />
          </div>
          <div>
            <p className="text-[11px] text-text-quaternary uppercase tracking-wider">Duration</p>
            <p className="text-base font-semibold text-text-primary font-mono">
              {(metrics.total_duration_ms / 1000).toFixed(1)}s
            </p>
          </div>
        </div>

        <div className="w-px h-10 bg-border-subtle" />

        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-bg-primary flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-text-tertiary" />
          </div>
          <div>
            <p className="text-[11px] text-text-quaternary uppercase tracking-wider">Confidence</p>
            <p className="text-base font-semibold font-mono">
              <span className="text-text-tertiary">{metrics.confidence_before}%</span>
              <span className="text-text-quaternary mx-1.5">&#8594;</span>
              <span className="text-text-primary">{metrics.confidence_after}%</span>
              <span
                className={`ml-1.5 text-xs ${
                  delta > 0 ? "text-success" : delta < 0 ? "text-error" : "text-text-quaternary"
                }`}
              >
                {delta > 0 ? "+" : ""}
                {delta}
              </span>
            </p>
          </div>
        </div>

        <div className="w-px h-10 bg-border-subtle" />

        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-bg-primary flex items-center justify-center">
            <Search className="w-4 h-4 text-text-tertiary" />
          </div>
          <div>
            <p className="text-[11px] text-text-quaternary uppercase tracking-wider">Claims Checked</p>
            <div className="flex items-center gap-3 mt-0.5">
              <span className="flex items-center gap-1.5 text-success font-mono text-sm">
                <CheckCircle className="w-3.5 h-3.5" />
                {metrics.claims_verified}
              </span>
              <span className="flex items-center gap-1.5 text-error font-mono text-sm">
                <XCircle className="w-3.5 h-3.5" />
                {metrics.claims_refuted}
              </span>
              <span className="flex items-center gap-1.5 text-warning font-mono text-sm">
                <AlertCircle className="w-3.5 h-3.5" />
                {metrics.claims_unclear}
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
