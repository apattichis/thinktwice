export type InputMode = "question" | "claim" | "url";

export type StepName = "draft" | "critique" | "verify" | "refine";

export type StepStatus = "idle" | "running" | "complete" | "error";

export type Verdict = "verified" | "refuted" | "unclear";

export type Severity = "low" | "medium" | "high";

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

export interface PipelineState {
  isRunning: boolean;
  error?: string;
  draft: DraftState;
  critique: CritiqueState;
  verify: VerifyState;
  refine: RefineState;
  metrics?: PipelineMetrics;
}
