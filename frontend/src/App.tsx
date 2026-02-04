import { useState, useCallback } from 'react';
import { Layout } from './components/Layout';
import { InputArea } from './components/InputArea';
import { PipelineStepper } from './components/PipelineStepper';
import { DraftStep } from './components/DraftStep';
import { CritiqueStep } from './components/CritiqueStep';
import { VerifyStep } from './components/VerifyStep';
import { RefineStep } from './components/RefineStep';
import { MetricsBar } from './components/MetricsBar';
import { ExamplePrompts } from './components/ExamplePrompts';
import { usePipeline } from './hooks/usePipeline';
import type { InputMode } from './types';

function App() {
  const { state, run, error } = usePipeline();
  const [activeMode, setActiveMode] = useState<InputMode>('question');

  const handleSubmit = useCallback((input: string, mode: InputMode) => {
    run({ input, mode });
  }, [run]);

  const handleExampleSelect = useCallback((text: string, mode: InputMode) => {
    setActiveMode(mode);
    handleSubmit(text, mode);
  }, [handleSubmit]);

  const hasStarted = state.draft.status !== 'pending';

  return (
    <Layout>
      <div className="space-y-8">
        {/* Input area */}
        <InputArea
          onSubmit={handleSubmit}
          isLoading={state.isRunning}
        />

        {/* Example prompts (only show before pipeline starts) */}
        {!hasStarted && (
          <ExamplePrompts
            activeMode={activeMode}
            onSelect={handleExampleSelect}
          />
        )}

        {/* Error display */}
        {error && (
          <div className="p-4 bg-verdict-refuted/10 border border-verdict-refuted/30 rounded-xl text-verdict-refuted">
            <p className="font-medium">Error</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Pipeline visualization */}
        {hasStarted && (
          <>
            {/* Progress stepper */}
            <PipelineStepper
              stepStatuses={{
                draft: state.draft.status,
                critique: state.critique.status,
                verify: state.verify.status,
                refine: state.refine.status,
                extract: 'pending',
              }}
              durations={{
                draft: state.draft.duration_ms,
                critique: state.critique.duration_ms,
                verify: state.verify.duration_ms,
                refine: state.refine.duration_ms,
                extract: undefined,
              }}
            />

            {/* Step cards */}
            <div className="space-y-4">
              <DraftStep state={state.draft} />
              {state.critique.status !== 'pending' && (
                <CritiqueStep state={state.critique} />
              )}
              {state.verify.status !== 'pending' && (
                <VerifyStep state={state.verify} />
              )}
              {state.refine.status !== 'pending' && (
                <RefineStep state={state.refine} critiqueState={state.critique} />
              )}
            </div>

            {/* Final metrics */}
            {state.metrics && <MetricsBar metrics={state.metrics} />}
          </>
        )}
      </div>
    </Layout>
  );
}

export default App;
