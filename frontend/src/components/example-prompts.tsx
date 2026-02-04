"use client";

import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
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
    <div className="w-full max-w-2xl mx-auto mt-8">
      <p className="text-sm text-text-quaternary mb-4 text-center">
        Or try one of these examples
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {items.slice(0, 4).map((item, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            onClick={() => onSelect(item)}
            className="group relative text-left p-4 rounded-xl border border-border-subtle bg-bg-secondary/50 hover:bg-bg-tertiary hover:border-border-default transition-all duration-200"
          >
            <p className="text-sm text-text-secondary group-hover:text-text-primary transition-colors pr-6 line-clamp-2">
              {item}
            </p>
            <ArrowUpRight className="absolute top-4 right-4 w-4 h-4 text-text-quaternary group-hover:text-brand transition-colors" />
          </motion.button>
        ))}
      </div>
    </div>
  );
}
