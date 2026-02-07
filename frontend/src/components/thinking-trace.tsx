"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import {
  Loader2,
  Check,
  ChevronRight,
  ChevronDown,
  Layers,
  FileText,
  Zap,
  AlertTriangle,
  Shield,
  Wand2,
  Scale,
  CheckCircle,
  XCircle,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  PipelineState,
  StepStatus,
  Severity,
  Verdict,
} from "@/types";

interface ThinkingTraceProps {
  state: PipelineState;
}

type StepKey = "decompose" | "draft" | "gate" | "critique" | "verify" | "refine" | "trust";

interface StepConfig {
  key: StepKey;
  label: string;
  color: string;
  icon: typeof Layers;
}

const STEPS: StepConfig[] = [
  { key: "decompose", label: "Decompose", color: "#007AFF", icon: Layers },
  { key: "draft", label: "Draft", color: "#5856D6", icon: FileText },
  { key: "gate", label: "Gate", color: "#FF9500", icon: Zap },
  { key: "critique", label: "Critique", color: "#FF3B30", icon: AlertTriangle },
  { key: "verify", label: "Verify", color: "#AF52DE", icon: Shield },
  { key: "refine", label: "Refine", color: "#34C759", icon: Wand2 },
  { key: "trust", label: "Trust", color: "#30D158", icon: Scale },
];

const spring = { type: "spring" as const, bounce: 0.12, duration: 0.35 };

function getStepStatus(state: PipelineState, key: StepKey): StepStatus {
  return state[key].status;
}

function getStepDuration(state: PipelineState, key: StepKey): number | undefined {
  return state[key].duration_ms;
}

function getStepSummary(state: PipelineState, key: StepKey): string {
  switch (key) {
    case "decompose":
      return state.decompose.status === "complete"
        ? `Found ${state.decompose.constraints.length} constraints`
        : "";
    case "draft":
      return state.draft.status === "complete" ? "Response generated" : "";
    case "gate": {
      const d = state.gate.decision;
      if (!d) return "";
      return d.decision === "skip"
        ? `Fast Path (${d.confidence}%)`
        : `Needs refinement (${d.confidence}%)`;
    }
    case "critique": {
      const c = state.critique.data;
      if (!c) return "";
      return `Found ${c.issues.length} issue${c.issues.length !== 1 ? "s" : ""}`;
    }
    case "verify":
      return state.verify.status === "complete"
        ? `${state.verify.results.length} claim${state.verify.results.length !== 1 ? "s" : ""} checked`
        : "";
    case "refine":
      return state.refine.status === "complete"
        ? `${state.refine.changes_made.length} improvement${state.refine.changes_made.length !== 1 ? "s" : ""} applied`
        : "";
    case "trust": {
      const t = state.trust.decision;
      if (!t) return "";
      return `Selected ${t.winner}`;
    }
    default:
      return "";
  }
}

/* ── Severity styles for critique issues ── */
const severityStyles: Record<Severity, { label: string; color: string; bg: string }> = {
  high: { label: "High", color: "#FF3B30", bg: "rgba(255, 59, 48, 0.08)" },
  medium: { label: "Medium", color: "#FF9500", bg: "rgba(255, 149, 0, 0.08)" },
  low: { label: "Low", color: "#34C759", bg: "rgba(52, 199, 89, 0.08)" },
};

/* ── Verdict config for verify results ── */
const verdictConfig: Record<Verdict, { icon: typeof CheckCircle; label: string; color: string }> = {
  verified: { icon: CheckCircle, label: "Verified", color: "#34C759" },
  refuted: { icon: XCircle, label: "Refuted", color: "#FF3B30" },
  unclear: { icon: HelpCircle, label: "Unclear", color: "#FF9500" },
};

/* ── Priority styles for decompose constraints ── */
const priorityColor: Record<string, string> = {
  high: "#FF3B30",
  medium: "#FF9500",
  low: "#86868b",
};

const typeLabels: Record<string, string> = {
  content: "Content",
  reasoning: "Reasoning",
  accuracy: "Accuracy",
  format: "Format",
  tone: "Tone",
};

export function ThinkingTrace({ state }: ThinkingTraceProps) {
  const isComplete = !!state.finalOutput;
  const [traceOpen, setTraceOpen] = useState(true);
  const [expandedSteps, setExpandedSteps] = useState<Set<StepKey>>(new Set());
  const prevRunningRef = useRef<StepKey | null>(null);

  // Find the currently running step
  const runningStep = STEPS.find((s) => getStepStatus(state, s.key) === "running")?.key ?? null;

  // Auto-expand running step, auto-collapse previous
  useEffect(() => {
    if (runningStep && runningStep !== prevRunningRef.current) {
      setExpandedSteps(new Set([runningStep]));
      prevRunningRef.current = runningStep;
    }
  }, [runningStep]);

  // When pipeline completes, collapse the trace
  useEffect(() => {
    if (isComplete) {
      setTraceOpen(false);
      setExpandedSteps(new Set());
    }
  }, [isComplete]);

  const toggleStep = (key: StepKey) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // Visible steps: only show steps that are not idle
  const visibleSteps = STEPS.filter((s) => getStepStatus(state, s.key) !== "idle");

  // Count completed steps for the "View reasoning" label
  const completedCount = STEPS.filter((s) => getStepStatus(state, s.key) === "complete").length;
  const totalDuration = state.metrics?.total_duration_ms;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
      className="rounded-2xl overflow-hidden"
      style={{
        background: "rgba(255, 255, 255, 0.55)",
        backdropFilter: "blur(30px) saturate(180%)",
        WebkitBackdropFilter: "blur(30px) saturate(180%)",
        boxShadow: "0 1px 8px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.04)",
      }}
    >
      {/* Header — "Thinking..." or "View reasoning" */}
      <button
        onClick={() => setTraceOpen(!traceOpen)}
        className="w-full flex items-center gap-2.5 px-5 py-3 cursor-pointer hover:bg-black/[0.02] transition-colors"
      >
        <motion.div
          animate={{ rotate: traceOpen ? 90 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronRight className="w-3.5 h-3.5 text-[#86868b]" />
        </motion.div>

        {isComplete ? (
          <span className="text-[13px] text-[#86868b]">
            View reasoning
            <span className="text-[12px] text-[#aeaeb2] ml-1.5">
              ({completedCount} step{completedCount !== 1 ? "s" : ""}
              {totalDuration ? `, ${(totalDuration / 1000).toFixed(1)}s` : ""})
            </span>
          </span>
        ) : (
          <span className="text-[13px] text-[#1d1d1f] font-medium flex items-center gap-2">
            Thinking
            <motion.span
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="text-[#86868b]"
            >
              ...
            </motion.span>
          </span>
        )}
      </button>

      {/* Steps accordion */}
      <AnimatePresence initial={false}>
        {traceOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="border-t" style={{ borderColor: "rgba(0,0,0,0.04)" }}>
              {visibleSteps.map((step) => (
                <StepRow
                  key={step.key}
                  config={step}
                  state={state}
                  isExpanded={expandedSteps.has(step.key)}
                  onToggle={() => toggleStep(step.key)}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

/* ═══════════════════════════════════════════════════════
   Step Row — single row + expandable detail
   ═══════════════════════════════════════════════════════ */

interface StepRowProps {
  config: StepConfig;
  state: PipelineState;
  isExpanded: boolean;
  onToggle: () => void;
}

function StepRow({ config, state, isExpanded, onToggle }: StepRowProps) {
  const status = getStepStatus(state, config.key);
  const duration = getStepDuration(state, config.key);
  const summary = getStepSummary(state, config.key);
  const isRunning = status === "running";
  const isComplete = status === "complete";
  const hasDetails = isRunning || isComplete;

  return (
    <div
      className="border-b last:border-b-0"
      style={{ borderColor: "rgba(0,0,0,0.04)" }}
    >
      {/* Row header */}
      <button
        onClick={hasDetails ? onToggle : undefined}
        className={cn(
          "w-full flex items-center gap-3 px-5 h-10",
          hasDetails && "cursor-pointer hover:bg-black/[0.02] transition-colors"
        )}
      >
        {/* Status icon */}
        <div className="w-4 h-4 flex items-center justify-center shrink-0">
          {isRunning ? (
            <Loader2
              className="w-3.5 h-3.5 animate-spin"
              style={{ color: config.color }}
            />
          ) : isComplete ? (
            <Check
              className="w-3.5 h-3.5"
              style={{ color: config.color }}
              strokeWidth={2.5}
            />
          ) : (
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: "#d1d1d6" }}
            />
          )}
        </div>

        {/* Step name */}
        <span
          className="text-[13px] font-semibold shrink-0"
          style={{ color: isComplete || isRunning ? "#1d1d1f" : "#aeaeb2" }}
        >
          {config.label}
        </span>

        {/* Summary */}
        {summary && (
          <span className="text-[13px] text-[#6e6e73] truncate">
            &mdash; {summary}
          </span>
        )}

        {/* Right side: duration + chevron */}
        <div className="ml-auto flex items-center gap-2 shrink-0">
          {duration !== undefined && (
            <span className="text-[12px] text-[#aeaeb2] font-mono">
              {(duration / 1000).toFixed(1)}s
            </span>
          )}
          {hasDetails && (
            <motion.div
              animate={{ rotate: isExpanded ? 90 : 0 }}
              transition={{ duration: 0.15 }}
            >
              <ChevronRight className="w-3 h-3 text-[#d1d1d6]" />
            </motion.div>
          )}
        </div>
      </button>

      {/* Expandable detail content */}
      <AnimatePresence initial={false}>
        {isExpanded && hasDetails && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-4 pt-1 pl-12">
              <StepDetail stepKey={config.key} state={state} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   Step Detail — content for each expanded step
   ═══════════════════════════════════════════════════════ */

function StepDetail({ stepKey, state }: { stepKey: StepKey; state: PipelineState }) {
  switch (stepKey) {
    case "decompose":
      return <DecomposeDetail state={state} />;
    case "draft":
      return <DraftDetail state={state} />;
    case "gate":
      return <GateDetail state={state} />;
    case "critique":
      return <CritiqueDetail state={state} />;
    case "verify":
      return <VerifyDetail state={state} />;
    case "refine":
      return <RefineDetail state={state} />;
    case "trust":
      return <TrustDetail state={state} />;
  }
}

/* ── Decompose: constraint tags ── */
function DecomposeDetail({ state }: { state: PipelineState }) {
  const { constraints } = state.decompose;
  if (constraints.length === 0) {
    return <RunningPlaceholder text="Analyzing constraints..." />;
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {constraints.map((c, i) => (
        <span
          key={c.id}
          className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[12px] border"
          style={{
            borderColor: "rgba(0,0,0,0.06)",
            background: "rgba(255,255,255,0.7)",
          }}
        >
          <span
            className="text-[10px] font-bold uppercase"
            style={{ color: priorityColor[c.priority] || "#86868b" }}
          >
            {typeLabels[c.type] || c.type}
          </span>
          <span className="text-[#6e6e73] truncate max-w-[200px]">{c.text}</span>
        </span>
      ))}
    </div>
  );
}

/* ── Draft: streaming markdown ── */
function DraftDetail({ state }: { state: PipelineState }) {
  if (!state.draft.content) {
    return <RunningPlaceholder text="Generating response..." />;
  }
  return (
    <div className="prose prose-sm max-w-none prose-p:text-[13px] prose-p:leading-relaxed prose-p:text-[#6e6e73] prose-headings:text-[#1d1d1f] prose-li:text-[#6e6e73] prose-strong:text-[#1d1d1f] max-h-[300px] overflow-y-auto">
      <ReactMarkdown>{state.draft.content}</ReactMarkdown>
    </div>
  );
}

/* ── Gate: confidence bar + decision ── */
function GateDetail({ state }: { state: PipelineState }) {
  const decision = state.gate.decision;
  if (!decision) {
    return <RunningPlaceholder text="Evaluating quality..." />;
  }
  const isFastPath = decision.decision === "skip";
  return (
    <div className="space-y-2">
      {/* Confidence bar */}
      <div className="flex items-center gap-3">
        <div
          className="flex-1 h-1.5 rounded-full overflow-hidden"
          style={{ backgroundColor: "rgba(0,0,0,0.04)" }}
        >
          <motion.div
            className="h-full rounded-full"
            style={{
              backgroundColor: isFastPath ? "#34C759" : "#FF9500",
            }}
            initial={{ width: 0 }}
            animate={{ width: `${decision.confidence}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </div>
        <span className="text-[12px] font-mono text-[#6e6e73] shrink-0">
          {decision.confidence}%
        </span>
      </div>
      <p className="text-[12px] text-[#86868b]">{decision.reason}</p>
    </div>
  );
}

/* ── Critique: issues list ── */
function CritiqueDetail({ state }: { state: PipelineState }) {
  const data = state.critique.data;
  if (!data) {
    return <RunningPlaceholder text="Analyzing for issues..." />;
  }
  return (
    <div className="space-y-2">
      {data.issues.map((issue, i) => {
        const sev = severityStyles[issue.severity];
        return (
          <div key={i} className="flex items-start gap-2">
            <span
              className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded shrink-0 mt-0.5"
              style={{ color: sev.color, backgroundColor: sev.bg }}
            >
              {sev.label}
            </span>
            <span className="text-[12px] text-[#6e6e73] leading-relaxed">
              {issue.description}
            </span>
          </div>
        );
      })}
      {data.confidence !== undefined && (
        <div className="flex items-center gap-2 pt-1">
          <span className="text-[12px] text-[#86868b]">Confidence:</span>
          <span className="text-[12px] font-mono font-semibold text-[#1d1d1f]">
            {data.confidence}%
          </span>
        </div>
      )}
    </div>
  );
}

/* ── Verify: claim verdict list ── */
function VerifyDetail({ state }: { state: PipelineState }) {
  const results = state.verify.results;
  if (results.length === 0) {
    return <RunningPlaceholder text="Verifying claims..." />;
  }
  return (
    <div className="space-y-2">
      {results.map((result, i) => {
        const cfg = verdictConfig[result.verdict];
        const Icon = cfg.icon;
        return (
          <div key={i} className="flex items-start gap-2">
            <Icon
              className="w-3.5 h-3.5 shrink-0 mt-0.5"
              style={{ color: cfg.color }}
            />
            <div className="min-w-0">
              <span
                className="text-[10px] font-bold uppercase mr-1.5"
                style={{ color: cfg.color }}
              >
                {cfg.label}
              </span>
              <span className="text-[12px] text-[#6e6e73]">
                {result.claim}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Refine: streaming markdown + changes ── */
function RefineDetail({ state }: { state: PipelineState }) {
  if (!state.refine.content && state.refine.changes_made.length === 0) {
    return <RunningPlaceholder text="Refining response..." />;
  }
  return (
    <div className="space-y-3">
      {state.refine.content && (
        <div className="prose prose-sm max-w-none prose-p:text-[13px] prose-p:leading-relaxed prose-p:text-[#6e6e73] prose-headings:text-[#1d1d1f] prose-li:text-[#6e6e73] prose-strong:text-[#1d1d1f] max-h-[300px] overflow-y-auto">
          <ReactMarkdown>{state.refine.content}</ReactMarkdown>
        </div>
      )}
      {state.refine.changes_made.length > 0 && (
        <div className="space-y-1">
          {state.refine.changes_made.map((change, i) => (
            <div key={i} className="flex items-start gap-2 text-[12px] text-[#6e6e73]">
              <CheckCircle className="w-3 h-3 shrink-0 mt-0.5 text-[#34C759]" />
              {change}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Trust: winner badge + score comparison ── */
function TrustDetail({ state }: { state: PipelineState }) {
  const decision = state.trust.decision;
  if (!decision) {
    return <RunningPlaceholder text="Comparing versions..." />;
  }
  const winnerColor = decision.winner === "draft" ? "#5856D6" : "#34C759";
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <span
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[12px] font-semibold uppercase"
        style={{
          color: winnerColor,
          backgroundColor: decision.winner === "draft"
            ? "rgba(88, 86, 214, 0.08)"
            : "rgba(52, 199, 89, 0.08)",
        }}
      >
        {decision.winner === "draft" ? "Original" : "Refined"} wins
      </span>
      <span className="text-[12px] text-[#86868b] font-mono">
        {decision.draft_score} vs {decision.refined_score}
      </span>
    </div>
  );
}

/* ── Running placeholder ── */
function RunningPlaceholder({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 py-1">
      <Loader2 className="w-3 h-3 animate-spin text-[#86868b]" />
      <span className="text-[12px] text-[#86868b]">{text}</span>
    </div>
  );
}
