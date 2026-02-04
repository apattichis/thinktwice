"use client";

import { Sparkles } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl bg-background/80 border-b border-border-subtle">
      <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-text tracking-tight">
              ThinkTwice
            </h1>
          </div>
        </div>
        <nav className="flex items-center gap-1">
          <a
            href="https://github.com/apattichis/thinktwice"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-2 text-sm text-text-secondary hover:text-text transition-colors rounded-lg hover:bg-surface-elevated"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
