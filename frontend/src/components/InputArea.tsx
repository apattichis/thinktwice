import { useState } from 'react';
import { MessageSquare, ClipboardCheck, Link, Send, Loader2 } from 'lucide-react';
import type { InputMode } from '../types';

interface InputAreaProps {
  onSubmit: (input: string, mode: InputMode) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const tabs: { mode: InputMode; label: string; icon: typeof MessageSquare; placeholder: string }[] = [
  {
    mode: 'question',
    label: 'Question',
    icon: MessageSquare,
    placeholder: 'What would you like me to think twice about?',
  },
  {
    mode: 'claim',
    label: 'Fact-Check',
    icon: ClipboardCheck,
    placeholder: 'Paste a claim to verify...',
  },
  {
    mode: 'url',
    label: 'Analyze URL',
    icon: Link,
    placeholder: 'https://example.com/article',
  },
];

export function InputArea({ onSubmit, isLoading, disabled }: InputAreaProps) {
  const [activeTab, setActiveTab] = useState<InputMode>('question');
  const [input, setInput] = useState('');

  const currentTab = tabs.find(t => t.mode === activeTab)!;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading && !disabled) {
      onSubmit(input.trim(), activeTab);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
    if (e.key === 'Escape') {
      setInput('');
    }
  };

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden">
      {/* Tabs */}
      <div className="flex border-b border-border">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.mode;
          return (
            <button
              key={tab.mode}
              onClick={() => setActiveTab(tab.mode)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                isActive
                  ? 'text-primary border-b-2 border-step-draft bg-elevated/50'
                  : 'text-muted hover:text-secondary hover:bg-elevated/30'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4">
        <div className="relative">
          {activeTab === 'url' ? (
            <input
              type="url"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={currentTab.placeholder}
              disabled={isLoading || disabled}
              className="w-full bg-elevated border border-border rounded-lg px-4 py-3 pr-12 text-primary placeholder-muted focus:outline-none focus:border-step-draft focus:ring-1 focus:ring-step-draft/50 disabled:opacity-50"
            />
          ) : (
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={currentTab.placeholder}
              disabled={isLoading || disabled}
              rows={3}
              className="w-full bg-elevated border border-border rounded-lg px-4 py-3 pr-12 text-primary placeholder-muted focus:outline-none focus:border-step-draft focus:ring-1 focus:ring-step-draft/50 resize-none disabled:opacity-50"
            />
          )}
          <button
            type="submit"
            disabled={!input.trim() || isLoading || disabled}
            className="absolute right-3 bottom-3 p-2 rounded-lg bg-step-draft text-white hover:bg-step-draft/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        <p className="mt-2 text-xs text-muted">
          Press Enter to submit, Shift+Enter for new line, Escape to clear
        </p>
      </form>
    </div>
  );
}
