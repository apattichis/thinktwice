import { Brain } from 'lucide-react';

export function Header() {
  return (
    <header className="border-b border-border bg-card">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-step-draft/10">
            <Brain className="w-6 h-6 text-step-draft" />
          </div>
          <div>
            <h1 className="text-xl font-mono font-semibold text-primary">
              ThinkTwice
            </h1>
            <p className="text-xs text-muted">
              AI that catches its own mistakes
            </p>
          </div>
        </div>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-muted hover:text-secondary transition-colors text-sm"
        >
          View Source
        </a>
      </div>
    </header>
  );
}
