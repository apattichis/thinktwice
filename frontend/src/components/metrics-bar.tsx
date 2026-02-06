"use client";

import { motion } from "framer-motion";
import {
  Clock,
  TrendingUp,
  Search,
  CheckCircle,
  XCircle,
  AlertCircle,
  Zap,
  RotateCcw,
  Shield,
  ListChecks,
} from "lucide-react";
import type { PipelineMetrics } from "@/types";

interface MetricsBarProps {
  metrics: PipelineMetrics;
}

export function MetricsBar({ metrics }: MetricsBarProps) {
  const delta = metrics.confidence_after - metrics.confidence_before;
  const hasGate = metrics.gate_decision !== undefined;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-white/60 p-4 sm:p-5"
      style={{
        background: "rgba(255, 255, 255, 0.55)",
        backdropFilter: "blur(40px) saturate(200%)",
        WebkitBackdropFilter: "blur(40px) saturate(200%)",
        boxShadow: "0 1px 8px rgba(0,0,0,0.04), 0 0 1px rgba(0,0,0,0.06)",
      }}
    >
      {/* Mobile */}
      <div className="grid grid-cols-2 gap-4 sm:hidden">
        <MetricCell
          icon={<Clock className="w-4 h-4 text-text-tertiary" />}
          label="Time"
          value={`${(metrics.total_duration_ms / 1000).toFixed(1)}s`}
        />
        <MetricCell
          icon={<TrendingUp className="w-4 h-4 text-text-tertiary" />}
          label="Confidence"
          value={
            <span className="text-sm font-semibold font-mono">
              <span className="text-text-primary">{metrics.confidence_after}%</span>
              <DeltaBadge delta={delta} />
            </span>
          }
        />

        {hasGate && (
          <>
            <MetricCell
              icon={<Zap className="w-4 h-4 text-text-tertiary" />}
              label="Gate"
              value={
                <span className={`text-sm font-semibold ${metrics.fast_path ? "text-success" : "text-warning"}`}>
                  {metrics.fast_path ? "Fast Path" : "Refined"}
                </span>
              }
            />
            {!metrics.fast_path && (
              <MetricCell
                icon={<RotateCcw className="w-4 h-4 text-text-tertiary" />}
                label="Iterations"
                value={`${metrics.iterations_used || 0}`}
              />
            )}
          </>
        )}

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
        <MetricCell
          icon={<Clock className="w-4 h-4 text-text-tertiary" />}
          label="Duration"
          value={`${(metrics.total_duration_ms / 1000).toFixed(1)}s`}
          desktop
        />

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
              <DeltaBadge delta={delta} />
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

        {/* Pipeline-specific metrics */}
        {hasGate && (
          <>
            <div className="w-px h-10 bg-border-subtle" />

            <MetricCell
              icon={<Zap className="w-4 h-4 text-text-tertiary" />}
              label="Gate"
              value={
                <span className={`text-base font-semibold ${metrics.fast_path ? "text-success" : "text-[#FF9500]"}`}>
                  {metrics.fast_path ? "Fast Path" : "Refined"}
                </span>
              }
              desktop
            />

            {!metrics.fast_path && metrics.iterations_used !== undefined && (
              <>
                <div className="w-px h-10 bg-border-subtle" />
                <MetricCell
                  icon={<RotateCcw className="w-4 h-4 text-text-tertiary" />}
                  label="Iterations"
                  value={`${metrics.iterations_used}`}
                  desktop
                />
              </>
            )}

            {metrics.constraints_total !== undefined && (
              <>
                <div className="w-px h-10 bg-border-subtle" />
                <MetricCell
                  icon={<ListChecks className="w-4 h-4 text-text-tertiary" />}
                  label="Constraints"
                  value={`${metrics.constraints_satisfied ?? 0}/${metrics.constraints_total}`}
                  desktop
                />
              </>
            )}

            {metrics.trust_winner && metrics.trust_winner !== "N/A" && (
              <>
                <div className="w-px h-10 bg-border-subtle" />
                <MetricCell
                  icon={<Shield className="w-4 h-4 text-text-tertiary" />}
                  label="Trust Winner"
                  value={
                    <span className="text-base font-semibold text-text-primary capitalize">
                      {metrics.trust_winner}
                    </span>
                  }
                  desktop
                />
              </>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}

function DeltaBadge({ delta }: { delta: number }) {
  return (
    <span
      className={`ml-1.5 text-xs ${
        delta > 0 ? "text-success" : delta < 0 ? "text-error" : "text-text-quaternary"
      }`}
    >
      {delta > 0 ? "+" : ""}
      {delta}
    </span>
  );
}

function MetricCell({
  icon,
  label,
  value,
  desktop,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  desktop?: boolean;
}) {
  const size = desktop ? "w-9 h-9 rounded-xl" : "w-8 h-8 rounded-lg";
  const labelSize = desktop ? "text-[11px]" : "text-[10px]";
  const valueSize = desktop ? "text-base" : "text-sm";

  return (
    <div className="flex items-center gap-2.5">
      <div className={`${size} bg-bg-primary flex items-center justify-center`}>
        {icon}
      </div>
      <div>
        <p className={`${labelSize} text-text-quaternary uppercase tracking-wider`}>{label}</p>
        {typeof value === "string" ? (
          <p className={`${valueSize} font-semibold text-text-primary font-mono`}>{value}</p>
        ) : (
          value
        )}
      </div>
    </div>
  );
}
