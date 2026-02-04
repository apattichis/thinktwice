import ReactMarkdown from 'react-markdown';
import { StepCard } from './StepCard';
import type { DraftState } from '../types';

interface DraftStepProps {
  state: DraftState;
}

export function DraftStep({ state }: DraftStepProps) {
  return (
    <StepCard
      title="Draft"
      status={state.status}
      duration={state.duration_ms}
      color="var(--draft)"
      error={state.error}
    >
      {state.content && (
        <div className="prose prose-sm prose-invert max-w-none">
          <ReactMarkdown>{state.content}</ReactMarkdown>
        </div>
      )}
      {state.status === 'running' && !state.content && (
        <div className="h-20 flex items-center justify-center text-muted">
          Generating initial response...
        </div>
      )}
    </StepCard>
  );
}
