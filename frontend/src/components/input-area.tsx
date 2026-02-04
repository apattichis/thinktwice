"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare,
  ClipboardCheck,
  Link2,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { InputMode } from "@/types";

interface InputAreaProps {
  onSubmit: (input: string, mode: InputMode) => void;
  isLoading: boolean;
}

const tabs: { mode: InputMode; label: string; icon: typeof MessageSquare; placeholder: string }[] = [
  {
    mode: "question",
    label: "Ask",
    icon: MessageSquare,
    placeholder: "Ask anything and get a verified answer...",
  },
  {
    mode: "claim",
    label: "Verify",
    icon: ClipboardCheck,
    placeholder: "Paste a claim to fact-check...",
  },
  {
    mode: "url",
    label: "Analyze",
    icon: Link2,
    placeholder: "https://example.com/article",
  },
];

export function InputArea({ onSubmit, isLoading }: InputAreaProps) {
  const [mode, setMode] = useState<InputMode>("question");
  const [input, setInput] = useState("");

  const currentTab = tabs.find((t) => t.mode === mode)!;

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

  return (
    <div className="w-full">
      {/* Mode tabs */}
      <div className="flex gap-1 mb-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = mode === tab.mode;
          return (
            <button
              key={tab.mode}
              onClick={() => setMode(tab.mode)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200",
                isActive
                  ? "bg-surface-elevated text-text"
                  : "text-text-muted hover:text-text-secondary hover:bg-surface"
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <div className="relative bg-surface border border-border rounded-2xl overflow-hidden transition-all duration-200 focus-within:border-accent/50 focus-within:ring-4 focus-within:ring-accent/10">
            {mode === "url" ? (
              <input
                type="url"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={currentTab.placeholder}
                disabled={isLoading}
                className="w-full bg-transparent px-5 py-4 pr-14 text-text placeholder-text-muted focus:outline-none disabled:opacity-50"
              />
            ) : (
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={currentTab.placeholder}
                disabled={isLoading}
                rows={3}
                className="w-full bg-transparent px-5 py-4 pr-14 text-text placeholder-text-muted focus:outline-none resize-none disabled:opacity-50"
              />
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={cn(
                "absolute right-3 bottom-3 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200",
                input.trim() && !isLoading
                  ? "bg-accent text-white hover:bg-accent-hover"
                  : "bg-surface-elevated text-text-muted"
              )}
            >
              <AnimatePresence mode="wait">
                {isLoading ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                  >
                    <Loader2 className="w-5 h-5 animate-spin" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="submit"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                  >
                    <ArrowRight className="w-5 h-5" />
                  </motion.div>
                )}
              </AnimatePresence>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
