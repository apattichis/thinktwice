"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Header } from "@/components/header";
import { InputArea } from "@/components/input-area";
import { ExamplePrompts } from "@/components/example-prompts";
import { HowItWorks } from "@/components/how-it-works";
import { PipelineStepper } from "@/components/pipeline-stepper";
import { DecomposeView } from "@/components/decompose-view";
import { DraftView } from "@/components/draft-view";
import { GateView } from "@/components/gate-view";
import { CritiqueView } from "@/components/critique-view";
import { VerifyView } from "@/components/verify-view";
import { RefineView } from "@/components/refine-view";
import { FinalAnswerView } from "@/components/final-answer-view";
import { MetricsBar } from "@/components/metrics-bar";
import { usePipeline } from "@/hooks/use-pipeline";
import type { InputMode } from "@/types";

export default function Home() {
  const { state, run } = usePipeline();
  const [inputValue, setInputValue] = useState("");
  const [activeMode, setActiveMode] = useState<InputMode>("question");
  const [showHowItWorks, setShowHowItWorks] = useState(false);

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
    <div className="bg-bg-primary" style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <Header
        showHowItWorks={!hasStarted}
        onHowItWorks={() => setShowHowItWorks(true)}
      />
      <HowItWorks open={showHowItWorks} onClose={() => setShowHowItWorks(false)} />

      <main style={{ paddingTop: "80px", paddingBottom: "64px", flex: 1 }}>
        <div style={{ maxWidth: "720px", margin: "0 auto", padding: "0 24px" }}>
          {/* Hero */}
          <AnimatePresence mode="wait">
            {!hasStarted && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.35 }}
                style={{ textAlign: "center", marginBottom: "40px", paddingTop: "48px" }}
              >
                <motion.div
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.08 }}
                >
                  <span
                    style={{
                      fontSize: "13px",
                      fontWeight: 500,
                      color: "#86868b",
                      letterSpacing: "0.02em",
                      marginBottom: "24px",
                      display: "inline-block",
                    }}
                  >
                    Agentic Fact Verification
                  </span>
                </motion.div>

                <h1
                  style={{
                    fontSize: "clamp(40px, 6vw, 56px)",
                    fontWeight: 700,
                    letterSpacing: "-0.03em",
                    lineHeight: 1.08,
                    color: "#1d1d1f",
                    marginBottom: "20px",
                  }}
                >
                  Think twice
                  <br />
                  <span style={{ color: "#86868b" }}>before you trust</span>
                </h1>

                <p
                  style={{
                    fontSize: "18px",
                    color: "#6e6e73",
                    maxWidth: "620px",
                    margin: "0 auto",
                    lineHeight: 1.6,
                  }}
                >
                  An AI agent that drafts, critiques, verifies, and refines its own answers.
                  <br />
                  Watch every step of the reasoning in real time.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input */}
          <div style={{ marginBottom: "24px" }}>
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
                style={{
                  marginTop: "24px",
                  padding: "16px 20px",
                  borderRadius: "16px",
                  background: "rgba(255, 59, 48, 0.06)",
                  border: "1px solid rgba(255, 59, 48, 0.15)",
                }}
              >
                <p style={{ fontSize: "14px", fontWeight: 600, color: "#FF3B30" }}>Something went wrong</p>
                <p style={{ fontSize: "13px", color: "#6e6e73", marginTop: "4px" }}>{state.error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Pipeline */}
          <AnimatePresence>
            {hasStarted && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{ marginTop: "48px" }}
              >
                <PipelineStepper
                  statuses={{
                    decompose: state.decompose.status,
                    draft: state.draft.status,
                    gate: state.gate.status,
                    critique: state.critique.status,
                    verify: state.verify.status,
                    refine: state.refine.status,
                    trust: state.trust.status,
                  }}
                  durations={{
                    decompose: state.decompose.duration_ms,
                    draft: state.draft.duration_ms,
                    gate: state.gate.duration_ms,
                    critique: state.critique.duration_ms,
                    verify: state.verify.duration_ms,
                    refine: state.refine.duration_ms,
                    trust: state.trust.duration_ms,
                  }}
                  iteration={state.currentIteration}
                />

                {/* Reasoning trace */}
                <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "24px" }}>
                  <DecomposeView state={state.decompose} />
                  <DraftView state={state.draft} />
                  <GateView state={state.gate} />
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

                {/* Final answer */}
                {state.finalOutput && (
                  <div style={{ marginTop: "24px" }}>
                    <FinalAnswerView
                      content={state.finalOutput}
                      trustDecision={state.trust.decision}
                      metrics={state.metrics}
                    />
                  </div>
                )}

                {state.metrics && (
                  <div style={{ marginTop: "16px" }}>
                    <MetricsBar metrics={state.metrics} />
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer>
        <div style={{ maxWidth: "720px", margin: "0 auto", padding: "48px 24px 32px", textAlign: "center" }}>
          <p style={{ fontSize: "12px", color: "#c7c7cc", fontWeight: 400 }}>
            Agentic pipeline powered by Anthropic Claude
          </p>
        </div>
      </footer>
    </div>
  );
}
