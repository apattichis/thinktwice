"use client";

import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

const examples = [
  {
    label: "Alien invasion article",
    description: "6 paragraphs, 2nd starts with 'President'",
    prompt:
      'Write an obviously fake news article saying that aliens have invaded earth. Make it funny. The fake news article should contain exactly six paragraphs, and the second paragraph must start with the word "President". Separate paragraphs by double line breaks ("\\n\\n")',
  },
  {
    label: "Pikachu trivia question",
    description: "Think out loud, answer in exact format",
    prompt:
      'Is Pikachu one of the Avengers? Think out loud, then answer with one of the following options: "My answer is yes.", "My answer is no.", "My answer is maybe."',
  },
  {
    label: "Lowercase Swiss itinerary",
    description: "3 bullets, all lowercase, postscript",
    prompt:
      "Can you create an itinerary for a 5 day trip to switzerland that includes exactly 3 bullet points in markdown format, in all lowercase letters, and a postscript at the end starting with P.S.?",
  },
  {
    label: "Music evaluation rubric",
    description: "Quoted, 6 sections, 5+ capitalized words",
    prompt:
      'Write a rubric for evaluating a musical composition. Please wrap your entire reply with double quotation marks. There should be exactly 6 paragraphs separated by the markdown divider: ***\nIn your response, use words with all capital letters (such as "RUBRIC") at least 5 times.',
  },
];

interface ExamplePromptsProps {
  onSelect: (text: string) => void;
}

export function ExamplePrompts({ onSelect }: ExamplePromptsProps) {
  return (
    <div className="w-full max-w-2xl mx-auto" style={{ marginTop: "32px" }}>
      <p
        style={{
          fontSize: "13px",
          color: "#aeaeb2",
          textAlign: "center",
          marginBottom: "16px",
        }}
      >
        Or try one of these examples
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2" style={{ gap: "12px" }}>
        {examples.map((item, i) => (
          <motion.button
            key={item.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.3 }}
            onClick={() => onSelect(item.prompt)}
            className="group relative text-left rounded-2xl border border-white/60 hover:border-border-strong transition-all duration-200 hover:shadow-sm"
            style={{
              padding: "16px 18px",
              background: "rgba(255, 255, 255, 0.55)",
              backdropFilter: "blur(30px) saturate(180%)",
              WebkitBackdropFilter: "blur(30px) saturate(180%)",
            }}
          >
            <p
              className="group-hover:text-text-primary transition-colors"
              style={{
                fontSize: "14.5px",
                fontWeight: 560,
                color: "#1d1d1f",
                marginBottom: "5px",
                paddingRight: "24px",
              }}
            >
              {item.label}
            </p>
            <p
              className="group-hover:text-text-secondary transition-colors"
              style={{
                fontSize: "13px",
                color: "#aeaeb2",
                lineHeight: 1.45,
              }}
            >
              {item.description}
            </p>
            <ArrowUpRight
              className="group-hover:text-brand transition-colors"
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                width: "14px",
                height: "14px",
                color: "#d1d1d6",
              }}
            />
          </motion.button>
        ))}
      </div>
    </div>
  );
}
