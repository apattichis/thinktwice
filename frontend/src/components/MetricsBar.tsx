import { motion } from 'framer-motion';
import { Clock, TrendingUp, Search, CheckCircle, XCircle, HelpCircle } from 'lucide-react';
import type { PipelineMetrics } from '../types';

interface MetricsBarProps {
  metrics: PipelineMetrics;
}

export function MetricsBar({ metrics }: MetricsBarProps) {
  const confidenceDelta = metrics.confidence_after - metrics.confidence_before;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card rounded-xl border border-border p-4"
    >
      <div className="flex flex-wrap items-center justify-center gap-4 md:gap-8 text-sm">
        {/* Duration */}
        <div className="flex items-center gap-2 text-secondary">
          <Clock className="w-4 h-4 text-muted" />
          <span className="font-mono">{(metrics.total_duration_ms / 1000).toFixed(1)}s</span>
        </div>

        <div className="w-px h-4 bg-border hidden md:block" />

        {/* Confidence change */}
        <div className="flex items-center gap-2 text-secondary">
          <TrendingUp className="w-4 h-4 text-muted" />
          <span className="font-mono">
            {metrics.confidence_before}% → {metrics.confidence_after}%
          </span>
          <span
            className={`font-mono text-xs ${
              confidenceDelta > 0
                ? 'text-verdict-verified'
                : confidenceDelta < 0
                ? 'text-verdict-refuted'
                : 'text-muted'
            }`}
          >
            ({confidenceDelta > 0 ? '+' : ''}{confidenceDelta})
          </span>
        </div>

        <div className="w-px h-4 bg-border hidden md:block" />

        {/* Claims checked */}
        <div className="flex items-center gap-2 text-secondary">
          <Search className="w-4 h-4 text-muted" />
          <span className="font-mono">{metrics.claims_checked} claims</span>
        </div>

        <div className="w-px h-4 bg-border hidden md:block" />

        {/* Verdicts */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-verdict-verified">
            <CheckCircle className="w-4 h-4" />
            <span className="font-mono">{metrics.claims_verified}</span>
          </div>
          <div className="flex items-center gap-1 text-verdict-refuted">
            <XCircle className="w-4 h-4" />
            <span className="font-mono">{metrics.claims_refuted}</span>
          </div>
          <div className="flex items-center gap-1 text-verdict-unclear">
            <HelpCircle className="w-4 h-4" />
            <span className="font-mono">{metrics.claims_unclear}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
