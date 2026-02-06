"""Pipeline schemas for the ThinkTwice self-correcting reasoning pipeline."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConstraintType(str, Enum):
    CONTENT = "content"
    REASONING = "reasoning"
    ACCURACY = "accuracy"
    FORMAT = "format"
    TONE = "tone"


class ConstraintPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Constraint(BaseModel):
    id: str = Field(description="Unique constraint ID like C1, C2...")
    type: ConstraintType
    description: str
    priority: ConstraintPriority
    verifiable: bool


class DecomposeResult(BaseModel):
    main_task: str
    constraints: list[Constraint]
    implicit_constraints: list[str]
    difficulty_estimate: str  # easy, medium, hard


class SubQuestion(BaseModel):
    constraint_id: str
    question: str
    answer: str
    passed: bool


class GateResult(BaseModel):
    sub_questions: list[SubQuestion]
    gate_decision: str  # "skip" or "refine"
    gate_confidence: int = Field(ge=0, le=100)
    failing_constraints: list[str]


class ConstraintVerdict(str, Enum):
    SATISFIED = "satisfied"
    PARTIALLY_SATISFIED = "partially_satisfied"
    VIOLATED = "violated"


class ConstraintEvaluation(BaseModel):
    constraint_id: str
    verdict: ConstraintVerdict
    confidence: int = Field(ge=0, le=100)
    feedback: Optional[str] = None
    evidence_quote: Optional[str] = None


class ClaimToVerify(BaseModel):
    id: str  # V1, V2...
    claim: str
    source_constraint: str
    source_quote: str


class CritiqueResult(BaseModel):
    constraint_evaluations: list[ConstraintEvaluation]
    claims_to_verify: list[ClaimToVerify]
    overall_confidence: int = Field(ge=0, le=100)
    strengths_to_preserve: list[str]


class ClaimVerdict(str, Enum):
    VERIFIED = "verified"
    REFUTED = "refuted"
    UNCLEAR = "unclear"


class VerificationResult(BaseModel):
    claim_id: str
    claim: str
    web_verdict: ClaimVerdict
    web_source: Optional[str] = None
    web_explanation: str
    self_verdict: Optional[ClaimVerdict] = None
    self_derivation: Optional[str] = None
    combined_verdict: ClaimVerdict
    combined_confidence: int = Field(ge=0, le=100)
    web_verified: bool


class ChangeRecord(BaseModel):
    target_id: str  # constraint_id or claim_id
    change: str
    type: str  # content_addition, factual_correction, language_softening, etc.


class RefineResult(BaseModel):
    refined_response: str
    changes_made: list[ChangeRecord]
    confidence_after: int = Field(ge=0, le=100)


class ConvergenceDecision(str, Enum):
    CONVERGED = "converged"
    CONTINUE = "continue"
    MAX_ITERATIONS = "max_iterations_reached"


class ConvergenceResult(BaseModel):
    decision: ConvergenceDecision
    satisfied_count: int
    total_count: int
    confidence: int = Field(ge=0, le=100)
    unsatisfied_constraints: list[str]


class TrustResult(BaseModel):
    winner: str  # "draft" or "refined" or "blended"
    reasoning: str
    draft_score: int = Field(ge=0, le=100)
    refined_score: int = Field(ge=0, le=100)
    final_output: str
    blended: bool
    blend_notes: Optional[str] = None


class PipelineMetrics(BaseModel):
    total_duration: float
    phase_durations: dict[str, float]
    gate_decision: str
    iterations_used: int
    trust_winner: str
    constraints_total: int
    constraints_satisfied: int
    claims_total: int
    claims_verified: int
    claims_refuted: int
    claims_unclear: int
    confidence_initial: int
    confidence_final: int
    fast_path: bool
    token_usage: Optional[dict[str, int]] = None
