"use client";

import { motion } from "framer-motion";
import { useExamples } from "@/hooks/use-examples";
import type { InputMode } from "@/types";

interface ExamplePromptsProps {
  mode: InputMode;
  onSelect: (text: string) => void;
}

export function ExamplePrompts({ mode, onSelect }: ExamplePromptsProps) {
  const { examples, loading } = useExamples();

  if (loading || !examples) return null;

  const items =
    mode === "question"
      ? examples.questions
      : mode === "claim"
      ? examples.claims
      : examples.urls;

  if (!items.length) return null;

  return (
    <div className="space-y-3">
      <p className="text-sm text-text-muted">Try an example</p>
      <div className="flex flex-wrap gap-2">
        {items.slice(0, 4).map((item, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            onClick={() => onSelect(item)}
            className="px-4 py-2 text-sm text-text-secondary bg-surface border border-border rounded-full hover:border-border hover:bg-surface-elevated transition-all duration-200"
          >
            {item.length > 50 ? item.slice(0, 50) + "..." : item}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
