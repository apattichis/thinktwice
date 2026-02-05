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
    <div style={{ width: "100%", maxWidth: "640px", margin: "0 auto" }}>
      {/* Segmented Control */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: "20px" }}>
        <div
          style={{
            display: "inline-flex",
            padding: "3px",
            borderRadius: "10px",
            background: "rgba(0, 0, 0, 0.06)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
            gap: "2px",
          }}
        >
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={cn(
                "relative transition-all duration-200",
                mode === m.id ? "text-text-primary" : "text-text-tertiary hover:text-text-secondary"
              )}
              style={{
                padding: "8px 18px",
                fontSize: "14px",
                fontWeight: 500,
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
                background: "transparent",
                position: "relative",
                zIndex: 1,
              }}
            >
              {mode === m.id && (
                <motion.div
                  layoutId="activeTab"
                  style={{
                    position: "absolute",
                    inset: 0,
                    background: "rgba(255, 255, 255, 0.85)",
                    backdropFilter: "blur(20px)",
                    WebkitBackdropFilter: "blur(20px)",
                    borderRadius: "8px",
                    boxShadow: "0 1px 4px rgba(0,0,0,0.08), 0 0.5px 1px rgba(0,0,0,0.06)",
                  }}
                  transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                />
              )}
              <span style={{ position: "relative", zIndex: 2 }} className="hidden sm:inline">{m.label}</span>
              <span style={{ position: "relative", zIndex: 2 }} className="sm:hidden">{m.shortLabel}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Input Card */}
      <form onSubmit={handleSubmit}>
        <div className="group">
          <div
            className="transition-all duration-300 group-focus-within:shadow-lg group-focus-within:shadow-brand/[0.08]"
            style={{
              borderRadius: "16px",
              background: "rgba(255, 255, 255, 0.72)",
              backdropFilter: "blur(40px) saturate(210%)",
              WebkitBackdropFilter: "blur(40px) saturate(210%)",
              border: "1px solid rgba(0,0,0,0.08)",
              overflow: "hidden",
              boxShadow: "0 2px 16px rgba(0,0,0,0.06), 0 0 1px rgba(0,0,0,0.1)",
            }}
          >
            {/* Input */}
            {mode === "url" ? (
              <input
                type="url"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="https://example.com/article"
                disabled={isLoading}
                style={{
                  width: "100%",
                  background: "transparent",
                  padding: "16px 20px",
                  fontSize: "16px",
                  color: "#1d1d1f",
                  border: "none",
                  outline: "none",
                  opacity: isLoading ? 0.5 : 1,
                }}
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
                style={{
                  width: "100%",
                  background: "transparent",
                  padding: "16px 20px",
                  fontSize: "16px",
                  color: "#1d1d1f",
                  border: "none",
                  outline: "none",
                  resize: "none",
                  opacity: isLoading ? 0.5 : 1,
                  fontFamily: "inherit",
                }}
              />
            )}

            {/* Footer */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "10px 20px",
                borderTop: "1px solid rgba(0,0,0,0.05)",
              }}
            >
              <p style={{ fontSize: "13px", color: "#aeaeb2" }}>
                Press{" "}
                <kbd
                  style={{
                    padding: "2px 6px",
                    borderRadius: "5px",
                    background: "#f5f5f7",
                    color: "#86868b",
                    fontFamily: "var(--font-mono)",
                    fontSize: "11px",
                    border: "1px solid rgba(0,0,0,0.08)",
                  }}
                >
                  Enter
                </kbd>{" "}
                to submit
              </p>

              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "8px 18px",
                  borderRadius: "10px",
                  fontSize: "14px",
                  fontWeight: 600,
                  border: "none",
                  cursor: input.trim() && !isLoading ? "pointer" : "not-allowed",
                  background: input.trim() && !isLoading ? "#007AFF" : "#e8e8ed",
                  color: input.trim() && !isLoading ? "#ffffff" : "#aeaeb2",
                  boxShadow: input.trim() && !isLoading ? "0 2px 8px rgba(0, 122, 255, 0.3)" : "none",
                  transition: "all 0.2s",
                }}
              >
                <AnimatePresence mode="wait">
                  {isLoading ? (
                    <motion.div
                      key="loading"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      style={{ display: "flex", alignItems: "center", gap: "6px" }}
                    >
                      <Loader2 style={{ width: "14px", height: "14px" }} className="animate-spin" />
                      Analyzing
                    </motion.div>
                  ) : (
                    <motion.div
                      key="submit"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      style={{ display: "flex", alignItems: "center", gap: "6px" }}
                    >
                      Analyze
                      <ArrowRight style={{ width: "14px", height: "14px" }} />
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
