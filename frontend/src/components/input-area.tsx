"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { InputMode } from "@/types";

interface InputAreaProps {
  onSubmit: (input: string, mode: InputMode) => void;
  isLoading: boolean;
  initialValue?: string;
}

const modes: { id: InputMode; label: string; description: string }[] = [
  { id: "question", label: "Ask a Question", description: "Get a verified, fact-checked answer" },
  { id: "claim", label: "Verify a Claim", description: "Fact-check any statement" },
  { id: "url", label: "Analyze Article", description: "Extract and verify claims from a URL" },
];

export function InputArea({ onSubmit, isLoading, initialValue = "" }: InputAreaProps) {
  const [mode, setMode] = useState<InputMode>("question");
  const [input, setInput] = useState(initialValue);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (initialValue) setInput(initialValue);
  }, [initialValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSubmit(input.trim(), mode);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const currentMode = modes.find((m) => m.id === mode)!;

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Mode selector */}
      <div className="flex justify-center mb-6">
        <div className="inline-flex p-1 rounded-2xl bg-bg-secondary border border-border-subtle">
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={cn(
                "relative px-5 py-2.5 text-sm font-medium rounded-xl transition-all duration-200",
                mode === m.id
                  ? "text-text-primary"
                  : "text-text-tertiary hover:text-text-secondary"
              )}
            >
              {mode === m.id && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-bg-elevated rounded-xl shadow-lg"
                  transition={{ type: "spring", bounce: 0.15, duration: 0.5 }}
                />
              )}
              <span className="relative z-10">{m.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Input card */}
      <form onSubmit={handleSubmit}>
        <div className="relative group">
          {/* Glow effect */}
          <div className="absolute -inset-1 bg-gradient-to-r from-brand/20 via-purple-500/20 to-blue-500/20 rounded-3xl blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />

          {/* Main input card */}
          <div className="relative rounded-2xl bg-bg-secondary border border-border-default overflow-hidden transition-all duration-300 group-focus-within:border-brand/50 group-focus-within:shadow-2xl group-focus-within:shadow-brand/5">
            {/* Description */}
            <div className="px-5 pt-4 pb-2">
              <p className="text-sm text-text-tertiary">{currentMode.description}</p>
            </div>

            {/* Input */}
            {mode === "url" ? (
              <input
                type="url"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="https://example.com/article"
                disabled={isLoading}
                className="w-full bg-transparent px-5 py-3 text-base text-text-primary placeholder-text-quaternary focus:outline-none disabled:opacity-50"
              />
            ) : (
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  mode === "question"
                    ? "What would you like to know?"
                    : "Enter a claim to fact-check..."
                }
                disabled={isLoading}
                rows={3}
                className="w-full bg-transparent px-5 py-3 text-base text-text-primary placeholder-text-quaternary focus:outline-none resize-none disabled:opacity-50"
              />
            )}

            {/* Footer */}
            <div className="flex items-center justify-between px-5 py-3 border-t border-border-subtle bg-bg-tertiary/50">
              <p className="text-xs text-text-quaternary">
                Press <kbd className="px-1.5 py-0.5 rounded bg-bg-hover text-text-tertiary font-mono text-xs">Enter</kbd> to submit
              </p>

              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className={cn(
                  "flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                  input.trim() && !isLoading
                    ? "bg-gradient-to-r from-brand to-indigo-600 text-white shadow-lg shadow-brand/25 hover:shadow-xl hover:shadow-brand/30 hover:scale-[1.02] active:scale-[0.98]"
                    : "bg-bg-hover text-text-quaternary cursor-not-allowed"
                )}
              >
                <AnimatePresence mode="wait">
                  {isLoading ? (
                    <motion.div
                      key="loading"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      className="flex items-center gap-2"
                    >
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing
                    </motion.div>
                  ) : (
                    <motion.div
                      key="submit"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      className="flex items-center gap-2"
                    >
                      <Sparkles className="w-4 h-4" />
                      Analyze
                    </motion.div>
                  )}
                </AnimatePresence>
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
