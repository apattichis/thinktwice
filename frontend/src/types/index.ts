export type InputMode = "question" | "claim" | "url";

export type StepName = "draft" | "critique" | "verify" | "refine";

export type StepStatus = "idle" | "running" | "complete" | "error";

export type Verdict = "verified" | "refuted" | "unclear";

export type Severity = "low" | "medium" | "high";

export type ConstraintVerdict = "satisfied" | "violated" | "partial" | "unknown";

export interface CritiqueIssue {
  description: string;
  severity: Severity;
  quote?: string;
}

export interface Critique {
  issues: CritiqueIssue[];
  strengths: string[];
  claims_to_verify: string[];
  confidence: number;
}

export interface VerificationResult {
  claim: string;
  verdict: Verdict;
  source?: string;
  source_title?: string;
  explanation: string;
  web_verified: boolean;
}

// V2 types
export interface Constraint {
  id: string;
  text: string;
  type: string;
  priority: string;
}

export interface ConstraintEvaluation {
  constraint_id: string;
  constraint_text: string;
  verdict: ConstraintVerdict;
  confidence: number;
  explanation: string;
}

export interface GateDecision {
  decision: "skip" | "refine";
  confidence: number;
  sub_questions: Array<{ question: string; answer: string; passed: boolean }>;
  reason: string;
}

export interface TrustDecision {
  winner: "draft" | "refined";
  draft_score: number;
  refined_score: number;
  reason: string;
}

export interface PipelineMetrics {
  total_duration_ms: number;
  confidence_before: number;
  confidence_after: number;
  issues_found: number;
  issues_addressed: number;
  claims_checked: number;
  claims_verified: number;
  claims_refuted: number;
  claims_unclear: number;
  web_verified: boolean;
  // V2 metrics
  gate_decision?: string;
  fast_path?: boolean;
  iterations_used?: number;
  constraints_total?: number;
  constraints_satisfied?: number;
  trust_winner?: string;
}

export interface DraftState {
  status: StepStatus;
  content: string;
  duration_ms?: number;
}

export interface CritiqueState {
  status: StepStatus;
  data?: Critique;
  duration_ms?: number;
}

export interface VerifyState {
  status: StepStatus;
  results: VerificationResult[];
  duration_ms?: number;
  web_verified: boolean;
}

export interface RefineState {
  status: StepStatus;
  content: string;
  confidence?: number;
  changes_made: string[];
  duration_ms?: number;
}

// V2 state
export interface DecomposeState {
  status: StepStatus;
  constraints: Constraint[];
  duration_ms?: number;
}

export interface GateState {
  status: StepStatus;
  decision?: GateDecision;
  duration_ms?: number;
}

export interface TrustState {
  status: StepStatus;
  decision?: TrustDecision;
  duration_ms?: number;
}

export interface PipelineState {
  isRunning: boolean;
  error?: string;
  pipelineVersion: "v1" | "v2";
  currentIteration: number;
  draft: DraftState;
  critique: CritiqueState;
  verify: VerifyState;
  refine: RefineState;
  // V2 phases
  decompose: DecomposeState;
  gate: GateState;
  trust: TrustState;
  constraintVerdicts: ConstraintEvaluation[];
  metrics?: PipelineMetrics;
}
