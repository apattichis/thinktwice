"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PenLine, MessageSquareWarning, ShieldCheck, Sparkles } from "lucide-react";

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

const CYCLE_MS = 3000;

export function HowItWorks() {
  const [active, setActive] = useState(0);

  const advance = useCallback(() => {
    setActive((prev) => (prev + 1) % steps.length);
  }, []);

  useEffect(() => {
    const id = setInterval(advance, CYCLE_MS);
    return () => clearInterval(id);
  }, [advance]);

  const handleClick = (i: number) => setActive(i);

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Pipeline track */}
      <div
        style={{
          borderRadius: "20px",
          background: "rgba(255, 255, 255, 0.65)",
          backdropFilter: "blur(40px) saturate(200%)",
          WebkitBackdropFilter: "blur(40px) saturate(200%)",
          border: "1px solid rgba(0,0,0,0.06)",
          boxShadow:
            "0 4px 24px rgba(0,0,0,0.04), 0 1px 3px rgba(0,0,0,0.06)",
          padding: "32px 28px 28px",
        }}
      >
        {/* Step nodes + beam */}
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
              left: "20px",
              right: "20px",
              height: "3px",
              background: "rgba(0,0,0,0.06)",
              borderRadius: "2px",
              transform: "translateY(-50%)",
            }}
          />

          {/* Progress beam */}
          <motion.div
            style={{
              position: "absolute",
              top: "50%",
              left: "20px",
              height: "3px",
              borderRadius: "2px",
              transform: "translateY(-50%)",
              background: `linear-gradient(90deg, ${steps[0].color}, ${steps[active].color})`,
            }}
            animate={{
              width: `${(active / (steps.length - 1)) * (100 - (40 / 640) * 100)}%`,
            }}
            transition={{ type: "spring", bounce: 0.15, duration: 0.6 }}
          />

          {/* Nodes */}
          {steps.map((step, i) => {
            const isActive = i === active;
            const isPast = i < active;
            const isFuture = i > active;

            return (
              <button
                key={step.label}
                onClick={() => handleClick(i)}
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
                {/* Node dot */}
                <div style={{ position: "relative" }}>
                  {/* Glow ring */}
                  {isActive && (
                    <motion.div
                      style={{
                        position: "absolute",
                        inset: "-6px",
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
                      width: "40px",
                      height: "40px",
                      borderRadius: "50%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      border: "2px solid",
                      borderColor: isFuture
                        ? "rgba(0,0,0,0.1)"
                        : step.color,
                      background: isActive || isPast ? step.color : "white",
                      boxShadow: isActive
                        ? `0 4px 16px ${step.color}40`
                        : "none",
                    }}
                    animate={{
                      scale: isActive ? [1, 1.06, 1] : 1,
                    }}
                    transition={
                      isActive
                        ? { duration: 2, repeat: Infinity }
                        : { type: "spring", bounce: 0.15, duration: 0.4 }
                    }
                  >
                    <step.icon
                      style={{
                        width: "18px",
                        height: "18px",
                        color:
                          isActive || isPast
                            ? "white"
                            : isFuture
                            ? "rgba(0,0,0,0.2)"
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
            borderRadius: "14px",
            background: "rgba(0,0,0,0.03)",
            padding: "20px 24px",
            minHeight: "88px",
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
                  marginBottom: "6px",
                }}
              >
                <motion.div
                  initial={{ rotate: -15, scale: 0.8 }}
                  animate={{ rotate: 0, scale: 1 }}
                  transition={{ type: "spring", bounce: 0.3, duration: 0.4 }}
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
                  lineHeight: 1.55,
                  color: "#6e6e73",
                  margin: 0,
                }}
              >
                {steps[active].description}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Step dots indicator */}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "6px",
            marginTop: "16px",
          }}
        >
          {steps.map((step, i) => (
            <motion.button
              key={step.label}
              onClick={() => handleClick(i)}
              style={{
                width: i === active ? "20px" : "6px",
                height: "6px",
                borderRadius: "3px",
                background: i === active ? step.color : "rgba(0,0,0,0.12)",
                border: "none",
                cursor: "pointer",
                padding: 0,
              }}
              animate={{
                width: i === active ? 20 : 6,
                background: i === active ? step.color : "rgba(0,0,0,0.12)",
              }}
              transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
