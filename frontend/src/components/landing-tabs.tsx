"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ExamplePrompts } from "@/components/example-prompts";
import { HowItWorks } from "@/components/how-it-works";
import type { InputMode } from "@/types";

const tabs = [
  { id: "how", label: "How it Works" },
  { id: "examples", label: "Try Examples" },
] as const;

type TabId = (typeof tabs)[number]["id"];

interface LandingTabsProps {
  mode: InputMode;
  onSelect: (text: string) => void;
}

export function LandingTabs({ mode, onSelect }: LandingTabsProps) {
  const [activeTab, setActiveTab] = useState<TabId>("how");

  return (
    <div className="w-full max-w-2xl mx-auto mt-6">
      {/* Segmented control */}
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
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "7px 16px",
                fontSize: "13px",
                fontWeight: 500,
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
                background: "transparent",
                position: "relative",
                zIndex: 1,
                color: activeTab === tab.id ? "#1d1d1f" : "#86868b",
                transition: "color 0.2s",
              }}
            >
              {activeTab === tab.id && (
                <motion.div
                  layoutId="landingTab"
                  style={{
                    position: "absolute",
                    inset: 0,
                    background: "rgba(255, 255, 255, 0.85)",
                    backdropFilter: "blur(20px)",
                    WebkitBackdropFilter: "blur(20px)",
                    borderRadius: "8px",
                    boxShadow:
                      "0 1px 4px rgba(0,0,0,0.08), 0 0.5px 1px rgba(0,0,0,0.06)",
                  }}
                  transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                />
              )}
              <span style={{ position: "relative", zIndex: 2 }}>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <AnimatePresence mode="wait">
        {activeTab === "how" ? (
          <motion.div
            key="how"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            <HowItWorks />
          </motion.div>
        ) : (
          <motion.div
            key="examples"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            <ExamplePrompts mode={mode} onSelect={onSelect} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
