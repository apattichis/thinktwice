"use client";

import { Github, Shield } from "lucide-react";

export function Header() {
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
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "30px",
                height: "30px",
                borderRadius: "8px",
                background: "linear-gradient(145deg, rgba(255,255,255,0.9), rgba(230,230,235,0.7))",
                backdropFilter: "blur(20px)",
                WebkitBackdropFilter: "blur(20px)",
                border: "1px solid rgba(255,255,255,0.6)",
                boxShadow: "0 2px 8px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.8)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Shield style={{ width: "14px", height: "14px", color: "#8e8e93" }} strokeWidth={2} />
            </div>
            <span style={{ fontSize: "16px", fontWeight: 600, letterSpacing: "-0.02em", color: "#1d1d1f" }}>
              ThinkTwice
            </span>
          </div>

          {/* Nav */}
          <nav>
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
