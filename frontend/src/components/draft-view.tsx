"use client";

import ReactMarkdown from "react-markdown";
import { StepCard } from "./step-card";
import type { DraftState } from "@/types";

interface DraftViewProps {
  state: DraftState;
}

export function DraftView({ state }: DraftViewProps) {
  return (
    <StepCard
      title="Draft"
      status={state.status}
      color="var(--color-draft)"
      duration={state.duration_ms}
    >
      {state.content ? (
        <div className="prose max-w-none">
          <ReactMarkdown>{state.content}</ReactMarkdown>
        </div>
      ) : state.status === "running" ? (
        <div className="flex items-center justify-center py-8 text-text-muted">
          Generating initial response...
        </div>
      ) : null}
    </StepCard>
  );
}
