"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Header } from "@/components/header";
import { InputArea } from "@/components/input-area";
import { ExamplePrompts } from "@/components/example-prompts";
import { HowItWorks } from "@/components/how-it-works";
import { ThinkingTrace } from "@/components/thinking-trace";
import { FinalAnswerView } from "@/components/final-answer-view";
import { usePipeline } from "@/hooks/use-pipeline";

export default function Home() {
  const { state, run } = usePipeline();
  const [inputValue, setInputValue] = useState("");
  const [showHowItWorks, setShowHowItWorks] = useState(false);

  const handleSubmit = useCallback(
    (input: string) => {
      setInputValue(input);
      run(input);
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
                <ExamplePrompts onSelect={handleExampleSelect} />
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
                style={{ marginTop: "32px" }}
              >
                {/* Final answer — appears at TOP when ready */}
                {state.finalOutput && (
                  <div style={{ marginBottom: "16px" }}>
                    <FinalAnswerView
                      content={state.finalOutput}
                      trustDecision={state.trust.decision}
                      metrics={state.metrics}
                    />
                  </div>
                )}

                {/* Thinking trace — accordion of steps */}
                <ThinkingTrace state={state} />
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
