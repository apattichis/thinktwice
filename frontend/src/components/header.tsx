"use client";

import { Github, Lightbulb, X } from "lucide-react";

interface HeaderProps {
  showHowItWorks?: boolean;
  onHowItWorks?: () => void;
  hasApiKey?: boolean;
  onRemoveKey?: () => void;
}

export function Header({ showHowItWorks, onHowItWorks, hasApiKey, onRemoveKey }: HeaderProps) {
  return (
    <header
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        borderBottom: "1px solid rgba(0,0,0,0.04)",
        background: "rgba(251, 251, 253, 0.72)",
        backdropFilter: "blur(40px) saturate(210%)",
        WebkitBackdropFilter: "blur(40px) saturate(210%)",
      }}
    >
      <div style={{ maxWidth: "960px", margin: "0 auto", padding: "0 24px" }}>
        <div style={{ display: "flex", height: "52px", alignItems: "center", justifyContent: "space-between" }}>
          {/* Logo */}
          <a
            href="/"
            style={{ fontSize: "16px", fontWeight: 600, letterSpacing: "-0.02em", color: "#1d1d1f", textDecoration: "none" }}
          >
            ThinkTwice
          </a>

          {/* Nav */}
          <nav style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            {showHowItWorks && (
              <button
                onClick={onHowItWorks}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  fontSize: "14px",
                  color: "#86868b",
                  background: "none",
                  border: "none",
                  borderRadius: "8px",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                className="hover:bg-bg-hover hover:text-text-primary"
              >
                <Lightbulb style={{ width: "16px", height: "16px" }} />
                <span className="hidden sm:inline">How it Works</span>
              </button>
            )}
            {hasApiKey && (
              <button
                onClick={onRemoveKey}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  fontSize: "14px",
                  color: "#86868b",
                  background: "none",
                  border: "none",
                  borderRadius: "8px",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
                className="hover:bg-bg-hover hover:text-text-primary"
              >
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    background: "#34C759",
                    flexShrink: 0,
                  }}
                />
                <span className="hidden sm:inline">API Key</span>
                <X style={{ width: "14px", height: "14px" }} />
              </button>
            )}
            <a
              href="https://github.com/apattichis/thinktwice"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                fontSize: "14px",
                color: "#86868b",
                textDecoration: "none",
                borderRadius: "8px",
                transition: "all 0.2s",
              }}
              className="hover:bg-bg-hover hover:text-text-primary"
            >
              <Github style={{ width: "16px", height: "16px" }} />
              <span className="hidden sm:inline">Source</span>
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
