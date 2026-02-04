"use client";

import ReactMarkdown from "react-markdown";
import { FileText } from "lucide-react";
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
      color="#6366f1"
      duration={state.duration_ms}
    >
      {state.content ? (
        <div className="prose max-w-none">
          <ReactMarkdown>{state.content}</ReactMarkdown>
        </div>
      ) : state.status === "running" ? (
        <div className="flex items-center justify-center gap-3 py-12 text-text-tertiary">
          <FileText className="w-5 h-5" />
          <span>Generating initial response...</span>
        </div>
      ) : null}
    </StepCard>
  );
}
