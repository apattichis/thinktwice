import { motion } from 'framer-motion';
import { ExternalLink, AlertTriangle } from 'lucide-react';
import { StepCard } from './StepCard';
import type { VerifyState, Verdict } from '../types';

interface VerifyStepProps {
  state: VerifyState;
}

const verdictConfig: Record<Verdict, { emoji: string; label: string; color: string; bg: string }> = {
  verified: { emoji: '✅', label: 'VERIFIED', color: 'text-verdict-verified', bg: 'bg-verdict-verified/10' },
  refuted: { emoji: '❌', label: 'REFUTED', color: 'text-verdict-refuted', bg: 'bg-verdict-refuted/10' },
  unclear: { emoji: '⚠️', label: 'UNCLEAR', color: 'text-verdict-unclear', bg: 'bg-verdict-unclear/10' },
};

export function VerifyStep({ state }: VerifyStepProps) {
  return (
    <StepCard
      title="Verify"
      status={state.status}
      duration={state.duration_ms}
      color="var(--verify)"
      error={state.error}
    >
      <div className="space-y-4">
        {/* Web verification warning */}
        {!state.web_verified && state.results.length > 0 && (
          <div className="flex items-center gap-2 p-3 bg-elevated rounded-lg text-sm text-muted border border-border">
            <AlertTriangle className="w-4 h-4 text-verdict-unclear flex-shrink-0" />
            <span>
              Verified against AI knowledge only. Add a search API key for web verification.
            </span>
          </div>
        )}

        {/* Results */}
        <div className="space-y-3">
          {state.results.map((result, i) => {
            const config = verdictConfig[result.verdict];
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.15 }}
                className={`p-4 rounded-lg border border-border ${config.bg}`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg">{config.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-mono font-bold ${config.color}`}>
                        {config.label}
                      </span>
                    </div>
                    <p className="text-sm text-primary mb-2">{result.claim}</p>
                    <p className="text-sm text-secondary">{result.explanation}</p>
                    {result.source && (
                      <a
                        href={result.source}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-2 text-xs text-step-draft hover:underline"
                      >
                        <ExternalLink className="w-3 h-3" />
                        {result.source_title || 'Source'}
                      </a>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {state.status === 'running' && state.results.length === 0 && (
          <div className="h-20 flex items-center justify-center text-muted">
            Verifying claims against sources...
          </div>
        )}

        {state.status === 'complete' && state.results.length === 0 && (
          <div className="h-20 flex items-center justify-center text-muted">
            No claims to verify
          </div>
        )}
      </div>
    </StepCard>
  );
}
