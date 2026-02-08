"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Eye, EyeOff, ArrowRight, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiKeyGateProps {
  onKeyValid: (key: string) => void;
}

export function ApiKeyGate({ onKeyValid }: ApiKeyGateProps) {
  const [key, setKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [error, setError] = useState("");
  const [validating, setValidating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    const trimmed = key.trim();
    if (!trimmed.startsWith("sk-ant-")) {
      setError("Key must start with sk-ant-");
      return;
    }

    setValidating(true);
    try {
      const res = await fetch(`${API_BASE}/api/validate-key`, {
        method: "POST",
        headers: { "X-API-Key": trimmed },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.detail || "Invalid API key.");
        return;
      }
      onKeyValid(trimmed);
    } catch {
      setError("Could not reach the server. Is the backend running?");
    } finally {
      setValidating(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35 }}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingTop: "80px",
      }}
    >
      {/* Title */}
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.08 }}
        style={{ textAlign: "center", marginBottom: "40px" }}
      >
        <span
          style={{
            fontSize: "13px",
            fontWeight: 500,
            color: "#86868b",
            letterSpacing: "0.02em",
            marginBottom: "24px",
            display: "inline-block",
          }}
        >
          Agentic Fact Verification
        </span>
        <h1
          style={{
            fontSize: "clamp(40px, 6vw, 56px)",
            fontWeight: 700,
            letterSpacing: "-0.03em",
            lineHeight: 1.08,
            color: "#1d1d1f",
            marginBottom: "20px",
          }}
        >
          Think twice
          <br />
          <span style={{ color: "#86868b" }}>before you trust</span>
        </h1>
        <p
          style={{
            fontSize: "18px",
            color: "#6e6e73",
            maxWidth: "620px",
            margin: "0 auto",
            lineHeight: 1.6,
          }}
        >
          An AI agent that drafts, critiques, verifies, and refines its own
          answers.
        </p>
      </motion.div>

      {/* Glass card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18, duration: 0.4 }}
        style={{
          width: "100%",
          maxWidth: "440px",
          padding: "32px",
          borderRadius: "20px",
          background: "rgba(255, 255, 255, 0.65)",
          backdropFilter: "blur(40px) saturate(210%)",
          WebkitBackdropFilter: "blur(40px) saturate(210%)",
          border: "1px solid rgba(0, 0, 0, 0.06)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.04)",
        }}
      >
        <h2
          style={{
            fontSize: "17px",
            fontWeight: 600,
            color: "#1d1d1f",
            marginBottom: "4px",
          }}
        >
          Enter your API key
        </h2>
        <p
          style={{
            fontSize: "14px",
            color: "#86868b",
            marginBottom: "20px",
            lineHeight: 1.5,
          }}
        >
          Paste your Anthropic API key to get started. It stays in your browser
          and is never stored on our servers.
        </p>

        <form onSubmit={handleSubmit}>
          {/* Input wrapper */}
          <div
            style={{
              position: "relative",
              marginBottom: "12px",
            }}
          >
            <input
              type={showKey ? "text" : "password"}
              value={key}
              onChange={(e) => {
                setKey(e.target.value);
                if (error) setError("");
              }}
              placeholder="sk-ant-api03-..."
              autoFocus
              style={{
                width: "100%",
                padding: "12px 44px 12px 14px",
                fontSize: "14px",
                fontFamily: "var(--font-jetbrains), monospace",
                borderRadius: "12px",
                border: error
                  ? "1px solid rgba(255, 59, 48, 0.4)"
                  : "1px solid rgba(0, 0, 0, 0.1)",
                background: "rgba(255, 255, 255, 0.8)",
                color: "#1d1d1f",
                outline: "none",
                transition: "border-color 0.2s",
                boxSizing: "border-box",
              }}
              onFocus={(e) => {
                if (!error)
                  e.currentTarget.style.borderColor = "rgba(0, 122, 255, 0.5)";
              }}
              onBlur={(e) => {
                if (!error)
                  e.currentTarget.style.borderColor = "rgba(0, 0, 0, 0.1)";
              }}
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              style={{
                position: "absolute",
                right: "10px",
                top: "50%",
                transform: "translateY(-50%)",
                background: "none",
                border: "none",
                color: "#86868b",
                cursor: "pointer",
                padding: "4px",
                display: "flex",
                alignItems: "center",
              }}
            >
              {showKey ? (
                <EyeOff style={{ width: "18px", height: "18px" }} />
              ) : (
                <Eye style={{ width: "18px", height: "18px" }} />
              )}
            </button>
          </div>

          {/* Error */}
          {error && (
            <p
              style={{
                fontSize: "13px",
                color: "#FF3B30",
                marginBottom: "12px",
              }}
            >
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={validating || !key.trim()}
            style={{
              width: "100%",
              padding: "12px",
              fontSize: "15px",
              fontWeight: 600,
              color: "#fff",
              background:
                validating || !key.trim() ? "#b0b0b5" : "#007AFF",
              border: "none",
              borderRadius: "12px",
              cursor: validating || !key.trim() ? "default" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              transition: "background 0.2s",
            }}
          >
            {validating ? (
              <>
                <Loader2
                  style={{
                    width: "16px",
                    height: "16px",
                    animation: "spin 1s linear infinite",
                  }}
                />
                Validating...
              </>
            ) : (
              <>
                Get Started
                <ArrowRight style={{ width: "16px", height: "16px" }} />
              </>
            )}
          </button>
        </form>

        {/* Privacy note + link */}
        <div
          style={{
            marginTop: "16px",
            paddingTop: "16px",
            borderTop: "1px solid rgba(0, 0, 0, 0.06)",
          }}
        >
          <p
            style={{
              fontSize: "12px",
              color: "#c7c7cc",
              lineHeight: 1.5,
              textAlign: "center",
            }}
          >
            Your key is stored in sessionStorage and cleared when you close the
            tab.{" "}
            <a
              href="https://console.anthropic.com/"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#007AFF", textDecoration: "none" }}
            >
              Get an API key
            </a>
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
}
