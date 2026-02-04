"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Header } from "@/components/header";
import { InputArea } from "@/components/input-area";
import { ExamplePrompts } from "@/components/example-prompts";
import { PipelineStepper } from "@/components/pipeline-stepper";
import { DraftView } from "@/components/draft-view";
import { CritiqueView } from "@/components/critique-view";
import { VerifyView } from "@/components/verify-view";
import { RefineView } from "@/components/refine-view";
import { MetricsBar } from "@/components/metrics-bar";
import { usePipeline } from "@/hooks/use-pipeline";
import type { InputMode } from "@/types";

export default function Home() {
  const { state, run } = usePipeline();
  const [inputValue, setInputValue] = useState("");
  const [activeMode, setActiveMode] = useState<InputMode>("question");

  const handleSubmit = useCallback(
    (input: string, mode: InputMode) => {
      setInputValue(input);
      setActiveMode(mode);
      run(input, mode);
    },
    [run]
  );

  const handleExampleSelect = useCallback((text: string) => {
    setInputValue(text);
  }, []);

  const hasStarted = state.draft.status !== "idle";

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        <div className="max-w-3xl mx-auto px-6 py-12">
          {/* Hero section - only show when not started */}
          <AnimatePresence mode="wait">
            {!hasStarted && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="text-center mb-12"
              >
                <h2 className="text-4xl font-bold text-text mb-4 tracking-tight">
                  Get verified answers
                </h2>
                <p className="text-lg text-text-secondary max-w-xl mx-auto">
                  AI that drafts, self-critiques, fact-checks against live sources,
                  and refines its answers with full transparency.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input area */}
          <div className="mb-8">
            <InputArea onSubmit={handleSubmit} isLoading={state.isRunning} />
          </div>

          {/* Example prompts - only show when not started */}
          <AnimatePresence>
            {!hasStarted && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <ExamplePrompts mode={activeMode} onSelect={handleExampleSelect} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error display */}
          <AnimatePresence>
            {state.error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-8 p-4 bg-error/10 border border-error/20 rounded-xl text-error"
              >
                <p className="font-medium">Error</p>
                <p className="text-sm mt-1 opacity-80">{state.error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Pipeline visualization */}
          <AnimatePresence>
            {hasStarted && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-12 space-y-6"
              >
                {/* Stepper */}
                <PipelineStepper
                  statuses={{
                    draft: state.draft.status,
                    critique: state.critique.status,
                    verify: state.verify.status,
                    refine: state.refine.status,
                  }}
                  durations={{
                    draft: state.draft.duration_ms,
                    critique: state.critique.duration_ms,
                    verify: state.verify.duration_ms,
                    refine: state.refine.duration_ms,
                  }}
                />

                {/* Step cards */}
                <div className="space-y-4">
                  <DraftView state={state.draft} />

                  {state.critique.status !== "idle" && (
                    <CritiqueView state={state.critique} />
                  )}

                  {state.verify.status !== "idle" && (
                    <VerifyView state={state.verify} />
                  )}

                  {state.refine.status !== "idle" && (
                    <RefineView state={state.refine} critiqueState={state.critique} />
                  )}
                </div>

                {/* Metrics */}
                {state.metrics && <MetricsBar metrics={state.metrics} />}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border-subtle py-6">
        <div className="max-w-3xl mx-auto px-6 text-center text-sm text-text-muted">
          Powered by FastAPI and Anthropic Claude
        </div>
      </footer>
    </div>
  );
}
