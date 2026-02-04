import { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { fetchExamples } from '../utils/api';
import type { InputMode, ExamplesResponse } from '../types';

interface ExamplePromptsProps {
  activeMode: InputMode;
  onSelect: (text: string, mode: InputMode) => void;
}

export function ExamplePrompts({ activeMode, onSelect }: ExamplePromptsProps) {
  const [examples, setExamples] = useState<ExamplesResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchExamples()
      .then(setExamples)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading || !examples) {
    return null;
  }

  const currentExamples =
    activeMode === 'question' ? examples.questions :
    activeMode === 'claim' ? examples.claims :
    examples.urls;

  if (currentExamples.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm text-muted">
        <Sparkles className="w-4 h-4" />
        <span>Try an example</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {currentExamples.map((example, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
            onClick={() => onSelect(example, activeMode)}
            className="px-3 py-2 text-sm text-secondary bg-card border border-border rounded-lg hover:bg-elevated hover:border-step-draft/50 transition-colors text-left"
          >
            {example.length > 60 ? example.slice(0, 60) + '...' : example}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
