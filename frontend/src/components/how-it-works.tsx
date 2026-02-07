"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  PenLine,
  MessageSquareWarning,
  ShieldCheck,
  Sparkles,
  X,
  Play,
} from "lucide-react";

const steps = [
  {
    label: "Draft",
    color: "#5856D6",
    icon: PenLine,
    headline: "Generate an initial answer",
    description:
      "The agent drafts a comprehensive response using its knowledge, then identifies claims that need verification.",
  },
  {
    label: "Critique",
    color: "#FF9500",
    icon: MessageSquareWarning,
    headline: "Challenge every claim",
    description:
      "A second pass critically examines the draft, flagging weak reasoning, unsupported claims, and potential biases.",
  },
  {
    label: "Verify",
    color: "#AF52DE",
    icon: ShieldCheck,
    headline: "Cross-check with evidence",
    description:
      "Each flagged claim is independently verified against trusted sources, producing a verdict for every assertion.",
  },
  {
    label: "Refine",
    color: "#34C759",
    icon: Sparkles,
    headline: "Produce the final answer",
    description:
      "The original draft is rewritten to incorporate verification results, correcting errors and strengthening accuracy.",
  },
];

const CYCLE_MS = 3500;

interface HowItWorksProps {
  open: boolean;
  onClose: () => void;
}

export function HowItWorks({ open, onClose }: HowItWorksProps) {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    clearTimer();
    timerRef.current = setInterval(() => {
      setActive((prev) => (prev + 1) % steps.length);
    }, CYCLE_MS);
  }, [clearTimer]);

  // Start/stop auto-cycle based on open + paused state
  useEffect(() => {
    if (open && !paused) {
      startTimer();
    } else {
      clearTimer();
    }
    return clearTimer;
  }, [open, paused, startTimer, clearTimer]);

  // Reset when opening
  useEffect(() => {
    if (open) {
      setActive(0);
      setPaused(false);
    }
  }, [open]);

  const handleStepClick = (i: number) => {
    setActive(i);
    setPaused(true);
    clearTimer();
  };

  const handleResume = () => {
    setPaused(false);
  };

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          onClick={onClose}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
            background: "rgba(0, 0, 0, 0.4)",
            backdropFilter: "blur(8px)",
            WebkitBackdropFilter: "blur(8px)",
          }}
        >
          {/* Modal container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 12 }}
            transition={{ type: "spring", bounce: 0.15, duration: 0.5 }}
            onClick={(e) => e.stopPropagation()}
            style={{
              width: "100%",
              maxWidth: "560px",
              borderRadius: "24px",
              background: "rgba(255, 255, 255, 0.65)",
              backdropFilter: "blur(40px) saturate(200%)",
              WebkitBackdropFilter: "blur(40px) saturate(200%)",
              border: "1px solid rgba(0, 0, 0, 0.06)",
              boxShadow:
                "0 24px 80px rgba(0, 0, 0, 0.12), 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04)",
              padding: "36px 32px 32px",
              position: "relative",
            }}
          >
            {/* Close button */}
            <button
              onClick={onClose}
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                border: "none",
                background: "rgba(0, 0, 0, 0.06)",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "background 0.2s",
              }}
              className="hover:bg-bg-hover"
            >
              <X style={{ width: "16px", height: "16px", color: "#6e6e73" }} />
            </button>

            {/* Title */}
            <div style={{ textAlign: "center", marginBottom: "28px" }}>
              <h2
                style={{
                  fontSize: "20px",
                  fontWeight: 650,
                  letterSpacing: "-0.02em",
                  color: "#1d1d1f",
                  margin: 0,
                }}
              >
                How it Works
              </h2>
              <p
                style={{
                  fontSize: "13px",
                  color: "#86868b",
                  marginTop: "6px",
                }}
              >
                Four steps to a verified answer
              </p>
            </div>

            {/* Pipeline track */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                position: "relative",
                marginBottom: "28px",
              }}
            >
              {/* Background track */}
              <div
                style={{
                  position: "absolute",
                  top: "50%",
                  left: "24px",
                  right: "24px",
                  height: "3px",
                  background: "rgba(0, 0, 0, 0.06)",
                  borderRadius: "2px",
                  transform: "translateY(-50%)",
                }}
              />

              {/* Progress beam */}
              <motion.div
                style={{
                  position: "absolute",
                  top: "50%",
                  left: "24px",
                  height: "3px",
                  borderRadius: "2px",
                  transform: "translateY(-50%)",
                  background: `linear-gradient(90deg, ${steps[0].color}, ${steps[active].color})`,
                }}
                animate={{
                  width: `${(active / (steps.length - 1)) * (100 - (48 / 496) * 100)}%`,
                }}
                transition={{ type: "spring", bounce: 0.15, duration: 0.5 }}
              />

              {/* Nodes */}
              {steps.map((step, i) => {
                const isActive = i === active;
                const isPast = i < active;
                const isFuture = i > active;

                return (
                  <button
                    key={step.label}
                    onClick={() => handleStepClick(i)}
                    style={{
                      flex: 1,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: "10px",
                      position: "relative",
                      zIndex: 2,
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      padding: 0,
                    }}
                  >
                    {/* Node circle */}
                    <div style={{ position: "relative" }}>
                      {/* Glow ring */}
                      {isActive && (
                        <motion.div
                          style={{
                            position: "absolute",
                            inset: "-7px",
                            borderRadius: "50%",
                            background: step.color,
                            opacity: 0.15,
                          }}
                          animate={{
                            scale: [1, 1.3, 1],
                            opacity: [0.15, 0.08, 0.15],
                          }}
                          transition={{ duration: 2, repeat: Infinity }}
                        />
                      )}
                      <motion.div
                        style={{
                          width: "48px",
                          height: "48px",
                          borderRadius: "50%",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          border: "2px solid",
                          borderColor: isFuture
                            ? "rgba(0, 0, 0, 0.1)"
                            : step.color,
                          background:
                            isActive || isPast ? step.color : "white",
                          boxShadow: isActive
                            ? `0 4px 16px ${step.color}40`
                            : "none",
                        }}
                        animate={{
                          scale: isActive ? [1, 1.06, 1] : 1,
                        }}
                        whileHover={
                          !isActive
                            ? { scale: 1.1, boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }
                            : undefined
                        }
                        transition={
                          isActive
                            ? { duration: 2, repeat: Infinity }
                            : { type: "spring", bounce: 0.15, duration: 0.4 }
                        }
                      >
                        <step.icon
                          style={{
                            width: "20px",
                            height: "20px",
                            color:
                              isActive || isPast
                                ? "white"
                                : isFuture
                                ? "rgba(0, 0, 0, 0.2)"
                                : step.color,
                          }}
                        />
                      </motion.div>
                    </div>

                    {/* Label */}
                    <motion.span
                      style={{
                        fontSize: "13px",
                        fontWeight: isActive ? 600 : 500,
                        color: isActive
                          ? step.color
                          : isFuture
                          ? "#aeaeb2"
                          : "#1d1d1f",
                        transition: "color 0.2s",
                      }}
                    >
                      {step.label}
                    </motion.span>
                  </button>
                );
              })}
            </div>

            {/* Description card */}
            <div
              style={{
                borderRadius: "16px",
                background: "rgba(0, 0, 0, 0.03)",
                padding: "24px 28px",
                minHeight: "96px",
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* Accent bar */}
              <motion.div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: "3px",
                  height: "100%",
                  borderRadius: "0 2px 2px 0",
                }}
                animate={{ background: steps[active].color }}
                transition={{ duration: 0.3 }}
              />

              <AnimatePresence mode="wait">
                <motion.div
                  key={active}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.25 }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      marginBottom: "8px",
                    }}
                  >
                    <motion.div
                      initial={{ rotate: -15, scale: 0.8 }}
                      animate={{ rotate: 0, scale: 1 }}
                      transition={{
                        type: "spring",
                        bounce: 0.3,
                        duration: 0.4,
                      }}
                    >
                      {(() => {
                        const Icon = steps[active].icon;
                        return (
                          <Icon
                            style={{
                              width: "15px",
                              height: "15px",
                              color: steps[active].color,
                            }}
                          />
                        );
                      })()}
                    </motion.div>
                    <span
                      style={{
                        fontSize: "14px",
                        fontWeight: 600,
                        color: "#1d1d1f",
                      }}
                    >
                      {steps[active].headline}
                    </span>
                  </div>
                  <p
                    style={{
                      fontSize: "13px",
                      lineHeight: 1.6,
                      color: "#6e6e73",
                      margin: 0,
                    }}
                  >
                    {steps[active].description}
                  </p>
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Step dots + Resume pill */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "6px",
                marginTop: "20px",
                position: "relative",
              }}
            >
              {steps.map((step, i) => (
                <motion.button
                  key={step.label}
                  onClick={() => handleStepClick(i)}
                  style={{
                    width: i === active ? "20px" : "6px",
                    height: "6px",
                    borderRadius: "3px",
                    background:
                      i === active ? step.color : "rgba(0, 0, 0, 0.12)",
                    border: "none",
                    cursor: "pointer",
                    padding: 0,
                  }}
                  animate={{
                    width: i === active ? 20 : 6,
                    background:
                      i === active ? step.color : "rgba(0, 0, 0, 0.12)",
                  }}
                  transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                />
              ))}

              {/* Resume pill */}
              <AnimatePresence>
                {paused && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ type: "spring", bounce: 0.15, duration: 0.35 }}
                    onClick={handleResume}
                    style={{
                      position: "absolute",
                      right: 0,
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                      padding: "4px 12px",
                      borderRadius: "12px",
                      border: "none",
                      background: "rgba(0, 0, 0, 0.06)",
                      cursor: "pointer",
                      fontSize: "12px",
                      fontWeight: 500,
                      color: "#6e6e73",
                      transition: "background 0.2s, color 0.2s",
                    }}
                    className="hover:bg-bg-hover hover:text-text-primary"
                  >
                    <Play style={{ width: "10px", height: "10px" }} />
                    Resume
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
