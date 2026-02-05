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
    <div className="min-h-screen bg-bg-primary">
      <Header />

      <main className="pt-20 pb-16">
        <div className="max-w-3xl mx-auto px-5 sm:px-6">
          {/* Hero */}
          <AnimatePresence mode="wait">
            {!hasStarted && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.35 }}
                className="text-center mb-10 pt-8"
              >
                <motion.div
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.08 }}
                >
                  <span className="inline-block px-3 py-1 text-[11px] font-semibold text-brand bg-brand/[0.08] rounded-full mb-5 tracking-wide uppercase">
                    AI-Powered Fact Verification
                  </span>
                </motion.div>

                <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-text-primary mb-4 leading-[1.1]">
                  Think twice
                  <br />
                  <span className="text-text-tertiary">before you trust</span>
                </h1>

                <p className="text-base text-text-secondary max-w-md mx-auto leading-relaxed">
                  Get answers that are drafted, self-critiqued, fact-checked against
                  live sources, and refined — all in real-time.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input */}
          <div className="mb-6">
            <InputArea
              onSubmit={handleSubmit}
              isLoading={state.isRunning}
              initialValue={inputValue}
            />
          </div>

          {/* Examples */}
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

          {/* Error */}
          <AnimatePresence>
            {state.error && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-6 p-4 rounded-xl bg-error/[0.06] border border-error/15"
              >
                <p className="text-[13px] font-semibold text-error">Something went wrong</p>
                <p className="text-xs text-text-secondary mt-1">{state.error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Pipeline */}
          <AnimatePresence>
            {hasStarted && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-10 space-y-5"
              >
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

                <div className="space-y-3">
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

                {state.metrics && <MetricsBar metrics={state.metrics} />}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border-subtle">
        <div className="max-w-3xl mx-auto px-5 sm:px-6 py-6 text-center">
          <p className="text-xs text-text-quaternary">
            Powered by FastAPI and Anthropic Claude
          </p>
        </div>
      </footer>
    </div>
  );
}
