import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { ArrowUp, CheckCircle } from 'lucide-react';
import { StepCard } from './StepCard';
import type { RefineState, CritiqueState } from '../types';

interface RefineStepProps {
  state: RefineState;
  critiqueState: CritiqueState;
}

export function RefineStep({ state, critiqueState }: RefineStepProps) {
  const confidenceBefore = critiqueState.critique?.confidence ?? 0;
  const confidenceAfter = state.confidence ?? confidenceBefore;
  const confidenceDelta = confidenceAfter - confidenceBefore;

  return (
    <StepCard
      title="Refine"
      status={state.status}
      duration={state.duration_ms}
      color="var(--refine)"
      error={state.error}
    >
      <div className="space-y-6">
        {/* Refined content */}
        {state.content && (
          <div className="prose prose-sm prose-invert max-w-none">
            <ReactMarkdown>{state.content}</ReactMarkdown>
          </div>
        )}

        {/* Changes made */}
        {state.changes_made && state.changes_made.length > 0 && (
          <div className="border-t border-border pt-4">
            <h4 className="step-label text-xs text-muted mb-3 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Changes Made ({state.changes_made.length})
            </h4>
            <div className="space-y-2">
              {state.changes_made.map((change, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-2 text-sm text-secondary"
                >
                  <span className="text-step-refine">→</span>
                  {change}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Confidence comparison */}
        {state.status === 'complete' && (
          <div className="border-t border-border pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="step-label text-xs text-muted">Confidence</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono text-muted">{confidenceBefore}%</span>
                <ArrowUp
                  className={`w-4 h-4 ${
                    confidenceDelta > 0
                      ? 'text-verdict-verified'
                      : confidenceDelta < 0
                      ? 'text-verdict-refuted rotate-180'
                      : 'text-muted'
                  }`}
                />
                <span className="text-sm font-mono text-primary font-bold">{confidenceAfter}%</span>
                {confidenceDelta !== 0 && (
                  <span
                    className={`text-xs font-mono ${
                      confidenceDelta > 0 ? 'text-verdict-verified' : 'text-verdict-refuted'
                    }`}
                  >
                    ({confidenceDelta > 0 ? '+' : ''}{confidenceDelta})
                  </span>
                )}
              </div>
            </div>
            <div className="h-2 bg-elevated rounded-full overflow-hidden relative">
              {/* Before bar (faded) */}
              <div
                className="absolute h-full rounded-full opacity-30"
                style={{
                  width: `${confidenceBefore}%`,
                  backgroundColor: 'var(--text-muted)',
                }}
              />
              {/* After bar */}
              <motion.div
                className="h-full rounded-full relative z-10"
                style={{
                  backgroundColor:
                    confidenceAfter >= 70
                      ? 'var(--verified)'
                      : confidenceAfter >= 40
                      ? 'var(--unclear)'
                      : 'var(--refuted)',
                }}
                initial={{ width: `${confidenceBefore}%` }}
                animate={{ width: `${confidenceAfter}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            </div>
          </div>
        )}

        {state.status === 'running' && !state.content && (
          <div className="h-20 flex items-center justify-center text-muted">
            Refining response with corrections...
          </div>
        )}
      </div>
    </StepCard>
  );
}
