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
    <div className="min-h-screen gradient-bg">
      <Header />

      <main className="pt-24 pb-16">
        <div className="max-w-4xl mx-auto px-6">
          {/* Hero */}
          <AnimatePresence mode="wait">
            {!hasStarted && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="text-center mb-12"
              >
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.1 }}
                >
                  <span className="inline-block px-4 py-1.5 text-xs font-medium text-brand-light bg-brand/10 rounded-full border border-brand/20 mb-6">
                    AI-Powered Fact Verification
                  </span>
                </motion.div>

                <h1 className="text-5xl sm:text-6xl font-bold tracking-tight mb-6">
                  <span className="gradient-text">Think twice</span>
                  <br />
                  <span className="text-text-primary">before you trust</span>
                </h1>

                <p className="text-lg text-text-secondary max-w-xl mx-auto leading-relaxed">
                  Get answers that are drafted, self-critiqued, fact-checked against
                  live sources, and refined — all in real-time transparency.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input */}
          <div className="mb-8">
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
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-8 p-5 rounded-2xl bg-error/10 border border-error/20"
              >
                <p className="font-semibold text-error">Something went wrong</p>
                <p className="text-sm text-error/80 mt-1">{state.error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Pipeline */}
          <AnimatePresence>
            {hasStarted && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-16 space-y-8"
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

                {/* Cards */}
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
      <footer className="border-t border-border-subtle">
        <div className="max-w-4xl mx-auto px-6 py-8 text-center">
          <p className="text-sm text-text-quaternary">
            Powered by FastAPI and Anthropic Claude
          </p>
        </div>
      </footer>
    </div>
  );
}
