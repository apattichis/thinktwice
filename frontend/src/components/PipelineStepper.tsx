import { Check, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import type { StepStatus, StepName } from '../types';

interface Step {
  name: StepName;
  label: string;
  color: string;
}

const steps: Step[] = [
  { name: 'draft', label: 'Draft', color: 'var(--draft)' },
  { name: 'critique', label: 'Critique', color: 'var(--critique)' },
  { name: 'verify', label: 'Verify', color: 'var(--verify)' },
  { name: 'refine', label: 'Refine', color: 'var(--refine)' },
];

interface PipelineStepperProps {
  stepStatuses: Record<StepName, StepStatus>;
  durations: Record<StepName, number | undefined>;
}

export function PipelineStepper({ stepStatuses, durations }: PipelineStepperProps) {
  return (
    <div className="flex items-center justify-between gap-2 py-4">
      {steps.map((step, index) => {
        const status = stepStatuses[step.name];
        const duration = durations[step.name];
        const isActive = status === 'running';
        const isComplete = status === 'complete';
        const isPending = status === 'pending';

        return (
          <div key={step.name} className="flex items-center flex-1">
            {/* Step indicator */}
            <div className="flex flex-col items-center gap-1 flex-shrink-0">
              <motion.div
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all ${
                  isComplete
                    ? 'border-transparent'
                    : isActive
                    ? 'border-transparent'
                    : 'border-border bg-card'
                }`}
                style={{
                  backgroundColor: isComplete || isActive ? step.color : undefined,
                  color: isComplete || isActive ? 'white' : 'var(--text-muted)',
                }}
                animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                transition={{ repeat: Infinity, duration: 1.5 }}
              >
                {isComplete ? (
                  <Check className="w-5 h-5" />
                ) : isActive ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <span className="text-sm font-mono">{index + 1}</span>
                )}
              </motion.div>
              <span
                className={`step-label text-xs ${
                  isPending ? 'text-muted' : 'text-secondary'
                }`}
                style={{ color: isActive || isComplete ? step.color : undefined }}
              >
                {step.label}
              </span>
              {duration !== undefined && (
                <span className="text-xs text-muted font-mono">
                  {(duration / 1000).toFixed(1)}s
                </span>
              )}
            </div>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div className="flex-1 h-0.5 mx-2 bg-border relative">
                <motion.div
                  className="absolute inset-y-0 left-0"
                  style={{ backgroundColor: step.color }}
                  initial={{ width: 0 }}
                  animate={{ width: isComplete ? '100%' : 0 }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
