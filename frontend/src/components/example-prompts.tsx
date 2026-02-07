"use client";

import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

const examples = [
  "Is intermittent fasting safe for people with diabetes?",
  "Humans only use 10% of their brain",
  "What causes the northern lights and how far south can they be seen?",
  "The Great Wall of China is visible from space",
];

interface ExamplePromptsProps {
  onSelect: (text: string) => void;
}

export function ExamplePrompts({ onSelect }: ExamplePromptsProps) {
  return (
    <div className="w-full max-w-2xl mx-auto mt-6">
      <p className="text-[13px] text-text-quaternary mb-3 text-center">
        Or try one of these examples
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {examples.map((item, i) => (
          <motion.button
            key={item}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.3 }}
            onClick={() => onSelect(item)}
            className="group relative text-left p-3.5 rounded-xl border border-white/60 hover:border-border-strong transition-all duration-200 hover:shadow-sm"
            style={{
              background: "rgba(255, 255, 255, 0.55)",
              backdropFilter: "blur(30px) saturate(180%)",
              WebkitBackdropFilter: "blur(30px) saturate(180%)",
            }}
          >
            <p className="text-[13px] text-text-secondary group-hover:text-text-primary transition-colors pr-6 line-clamp-2 leading-relaxed">
              {item}
            </p>
            <ArrowUpRight className="absolute top-3.5 right-3.5 w-3.5 h-3.5 text-text-quaternary group-hover:text-brand transition-colors" />
          </motion.button>
        ))}
      </div>
    </div>
  );
}
