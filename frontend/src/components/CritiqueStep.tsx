import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle, Search } from 'lucide-react';
import { StepCard } from './StepCard';
import type { CritiqueState, Severity } from '../types';

interface CritiqueStepProps {
  state: CritiqueState;
}

const severityConfig: Record<Severity, { label: string; color: string; bg: string }> = {
  high: { label: 'HIGH', color: 'text-verdict-refuted', bg: 'bg-verdict-refuted/10' },
  medium: { label: 'MEDIUM', color: 'text-verdict-unclear', bg: 'bg-verdict-unclear/10' },
  low: { label: 'LOW', color: 'text-verdict-verified', bg: 'bg-verdict-verified/10' },
};

export function CritiqueStep({ state }: CritiqueStepProps) {
  const critique = state.critique;

  return (
    <StepCard
      title="Critique"
      status={state.status}
      duration={state.duration_ms}
      color="var(--critique)"
      error={state.error}
    >
      {critique && (
        <div className="space-y-6">
          {/* Issues */}
          {critique.issues.length > 0 && (
            <div>
              <h4 className="step-label text-xs text-muted mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Issues Found ({critique.issues.length})
              </h4>
              <div className="space-y-2">
                {critique.issues.map((issue, i) => {
                  const config = severityConfig[issue.severity];
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className={`p-3 rounded-lg border border-border ${config.bg}`}
                    >
                      <div className="flex items-start gap-2">
                        <span className={`text-xs font-mono font-bold ${config.color}`}>
                          {config.label}
                        </span>
                        <span className="text-sm text-secondary">{issue.description}</span>
                      </div>
                      {issue.quote && (
                        <p className="mt-2 text-xs text-muted italic border-l-2 border-border pl-2">
                          "{issue.quote}"
                        </p>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Strengths */}
          {critique.strengths.length > 0 && (
            <div>
              <h4 className="step-label text-xs text-muted mb-3 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Strengths ({critique.strengths.length})
              </h4>
              <div className="space-y-2">
                {critique.strengths.map((strength, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-2 text-sm text-secondary"
                  >
                    <span className="text-verdict-verified">✓</span>
                    {strength}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Claims to verify */}
          {critique.claims_to_verify.length > 0 && (
            <div>
              <h4 className="step-label text-xs text-muted mb-3 flex items-center gap-2">
                <Search className="w-4 h-4" />
                Claims to Verify ({critique.claims_to_verify.length})
              </h4>
              <div className="space-y-2">
                {critique.claims_to_verify.map((claim, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex items-start gap-2 text-sm text-secondary"
                  >
                    <span className="text-step-verify">🔍</span>
                    {claim}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Confidence bar */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="step-label text-xs text-muted">Initial Confidence</span>
              <span className="text-sm font-mono text-secondary">{critique.confidence}%</span>
            </div>
            <div className="h-2 bg-elevated rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{
                  backgroundColor:
                    critique.confidence >= 70
                      ? 'var(--verified)'
                      : critique.confidence >= 40
                      ? 'var(--unclear)'
                      : 'var(--refuted)',
                }}
                initial={{ width: 0 }}
                animate={{ width: `${critique.confidence}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
          </div>
        </div>
      )}
      {state.status === 'running' && !critique && (
        <div className="h-20 flex items-center justify-center text-muted">
          Analyzing draft for issues...
        </div>
      )}
    </StepCard>
  );
}
