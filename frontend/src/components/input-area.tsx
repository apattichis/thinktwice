"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, ArrowRight, Search, ShieldCheck, Link } from "lucide-react";
import { cn } from "@/lib/utils";
import type { InputMode } from "@/types";

interface InputAreaProps {
  onSubmit: (input: string, mode: InputMode) => void;
  isLoading: boolean;
  initialValue?: string;
}

const modes: { id: InputMode; label: string; shortLabel: string; icon: typeof Search; description: string }[] = [
  { id: "question", label: "Ask a Question", shortLabel: "Ask", icon: Search, description: "Get a verified, fact-checked answer" },
  { id: "claim", label: "Verify a Claim", shortLabel: "Verify", icon: ShieldCheck, description: "Fact-check any statement" },
  { id: "url", label: "Analyze URL", shortLabel: "URL", icon: Link, description: "Extract and verify claims from a URL" },
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
      {/* Segmented Control */}
      <div className="flex justify-center mb-5">
        <div className="inline-flex p-0.5 rounded-lg bg-bg-active/60 border border-border-subtle">
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={cn(
                "relative px-4 py-1.5 text-[13px] font-medium rounded-md transition-all duration-200",
                mode === m.id
                  ? "text-text-primary"
                  : "text-text-tertiary hover:text-text-secondary"
              )}
            >
              {mode === m.id && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-bg-secondary rounded-md shadow-sm border border-border-default"
                  transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                />
              )}
              <span className="relative z-10 hidden sm:inline">{m.label}</span>
              <span className="relative z-10 sm:hidden">{m.shortLabel}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Input Card */}
      <form onSubmit={handleSubmit}>
        <div className="relative group">
          <div className="relative rounded-2xl bg-bg-secondary border border-border-default overflow-hidden transition-all duration-300 shadow-sm group-focus-within:shadow-lg group-focus-within:shadow-brand/[0.06] group-focus-within:border-brand/30">
            {/* Mode description */}
            <div className="px-5 pt-4 pb-1 flex items-center gap-2">
              <currentMode.icon className="w-4 h-4 text-text-quaternary" />
              <p className="text-[13px] text-text-tertiary">{currentMode.description}</p>
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
                className="w-full bg-transparent px-5 py-3 text-[15px] text-text-primary placeholder-text-quaternary focus:outline-none disabled:opacity-50"
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
                className="w-full bg-transparent px-5 py-3 text-[15px] text-text-primary placeholder-text-quaternary focus:outline-none resize-none disabled:opacity-50"
              />
            )}

            {/* Footer */}
            <div className="flex items-center justify-between px-5 py-2.5 border-t border-border-subtle">
              <p className="text-xs text-text-quaternary">
                Press{" "}
                <kbd className="px-1.5 py-0.5 rounded-md bg-bg-primary text-text-tertiary font-mono text-[11px] border border-border-default">
                  Enter
                </kbd>{" "}
                to submit
              </p>

              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-xl text-[13px] font-semibold transition-all duration-200",
                  input.trim() && !isLoading
                    ? "bg-brand text-white shadow-sm shadow-brand/25 hover:bg-brand-dark active:scale-[0.97]"
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
                      className="flex items-center gap-1.5"
                    >
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Analyzing
                    </motion.div>
                  ) : (
                    <motion.div
                      key="submit"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      className="flex items-center gap-1.5"
                    >
                      Analyze
                      <ArrowRight className="w-3.5 h-3.5" />
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
