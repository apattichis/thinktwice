export type InputMode = 'question' | 'claim' | 'url';

export type StepName = 'draft' | 'critique' | 'verify' | 'refine' | 'extract';

export type StepStatus = 'pending' | 'running' | 'complete' | 'error';

export type Verdict = 'verified' | 'refuted' | 'unclear';

export type Severity = 'low' | 'medium' | 'high';

export interface ThinkRequest {
  input: string;
  mode: InputMode;
  run_single_shot?: boolean;
}

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

export interface RefinedResponse {
  content: string;
  confidence: number;
  changes_made: string[];
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

export interface StepStartEvent {
  step: StepName;
  status: 'running';
  label: string;
}

export interface StepStreamEvent {
  step: StepName;
  token: string;
}

export interface StepCompleteEvent {
  step: StepName;
  status: 'complete' | 'error';
  duration_ms?: number;
  content?: string | Critique;
  error?: string;
  // Verify specific
  verified?: number;
  refuted?: number;
  unclear?: number;
  web_verified?: boolean;
  // Refine specific
  confidence?: number;
  changes_made?: string[];
}

export interface VerifyClaimEvent extends VerificationResult {}

export interface PipelineCompleteEvent extends PipelineMetrics {}

export interface StepState {
  status: StepStatus;
  duration_ms?: number;
  content?: string;
  error?: string;
}

export interface DraftState extends StepState {
  content?: string;
}

export interface CritiqueState extends StepState {
  critique?: Critique;
}

export interface VerifyState extends StepState {
  results: VerificationResult[];
  verified: number;
  refuted: number;
  unclear: number;
  web_verified: boolean;
}

export interface RefineState extends StepState {
  content?: string;
  confidence?: number;
  changes_made?: string[];
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

export interface ExamplesResponse {
  questions: string[];
  claims: string[];
  urls: string[];
}
