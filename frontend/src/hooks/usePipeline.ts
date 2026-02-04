import { useCallback, useState } from 'react';
import { useSSE } from './useSSE';
import type {
  ThinkRequest,
  PipelineState,
  StepStartEvent,
  StepStreamEvent,
  StepCompleteEvent,
  VerifyClaimEvent,
  PipelineCompleteEvent,
  Critique,
  VerificationResult,
} from '../types';

const initialState: PipelineState = {
  isRunning: false,
  draft: { status: 'pending' },
  critique: { status: 'pending' },
  verify: { status: 'pending', results: [], verified: 0, refuted: 0, unclear: 0, web_verified: true },
  refine: { status: 'pending' },
};

export function usePipeline() {
  const [state, setState] = useState<PipelineState>(initialState);
  const { isConnected, error: sseError, startStream, stopStream } = useSSE();

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  const handleEvent = useCallback((event: { event: string; data: unknown }) => {
    const { event: eventType, data } = event;

    switch (eventType) {
      case 'step_start': {
        const e = data as StepStartEvent;
        if (e.step === 'draft') {
          setState(prev => ({ ...prev, draft: { ...prev.draft, status: 'running' } }));
        } else if (e.step === 'critique') {
          setState(prev => ({ ...prev, critique: { ...prev.critique, status: 'running' } }));
        } else if (e.step === 'verify') {
          setState(prev => ({ ...prev, verify: { ...prev.verify, status: 'running' } }));
        } else if (e.step === 'refine') {
          setState(prev => ({ ...prev, refine: { ...prev.refine, status: 'running' } }));
        }
        break;
      }

      case 'step_stream': {
        const e = data as StepStreamEvent;
        if (e.step === 'draft') {
          setState(prev => ({
            ...prev,
            draft: {
              ...prev.draft,
              content: (prev.draft.content || '') + e.token,
            },
          }));
        } else if (e.step === 'refine') {
          setState(prev => ({
            ...prev,
            refine: {
              ...prev.refine,
              content: (prev.refine.content || '') + e.token,
            },
          }));
        }
        break;
      }

      case 'step_complete': {
        const e = data as StepCompleteEvent;
        if (e.step === 'draft') {
          setState(prev => ({
            ...prev,
            draft: {
              status: e.status === 'error' ? 'error' : 'complete',
              duration_ms: e.duration_ms,
              content: typeof e.content === 'string' ? e.content : prev.draft.content,
              error: e.error,
            },
          }));
        } else if (e.step === 'critique') {
          setState(prev => ({
            ...prev,
            critique: {
              status: e.status === 'error' ? 'error' : 'complete',
              duration_ms: e.duration_ms,
              critique: e.content as Critique | undefined,
              error: e.error,
            },
          }));
        } else if (e.step === 'verify') {
          setState(prev => ({
            ...prev,
            verify: {
              ...prev.verify,
              status: e.status === 'error' ? 'error' : 'complete',
              duration_ms: e.duration_ms,
              verified: e.verified ?? prev.verify.verified,
              refuted: e.refuted ?? prev.verify.refuted,
              unclear: e.unclear ?? prev.verify.unclear,
              web_verified: e.web_verified ?? prev.verify.web_verified,
              error: e.error,
            },
          }));
        } else if (e.step === 'refine') {
          setState(prev => ({
            ...prev,
            refine: {
              status: e.status === 'error' ? 'error' : 'complete',
              duration_ms: e.duration_ms,
              content: typeof e.content === 'string' ? e.content : prev.refine.content,
              confidence: e.confidence,
              changes_made: e.changes_made,
              error: e.error,
            },
          }));
        }
        break;
      }

      case 'verify_claim': {
        const e = data as VerifyClaimEvent;
        const result: VerificationResult = {
          claim: e.claim,
          verdict: e.verdict,
          source: e.source,
          source_title: e.source_title,
          explanation: e.explanation,
          web_verified: e.web_verified,
        };
        setState(prev => ({
          ...prev,
          verify: {
            ...prev.verify,
            results: [...prev.verify.results, result],
          },
        }));
        break;
      }

      case 'pipeline_complete': {
        const e = data as PipelineCompleteEvent;
        setState(prev => ({
          ...prev,
          isRunning: false,
          metrics: e,
        }));
        break;
      }
    }
  }, []);

  const run = useCallback(async (request: ThinkRequest) => {
    reset();
    setState(prev => ({ ...prev, isRunning: true }));

    try {
      await startStream(request, handleEvent);
    } catch (err) {
      setState(prev => ({
        ...prev,
        isRunning: false,
        error: err instanceof Error ? err.message : 'Pipeline failed',
      }));
    }
  }, [reset, startStream, handleEvent]);

  const stop = useCallback(() => {
    stopStream();
    setState(prev => ({ ...prev, isRunning: false }));
  }, [stopStream]);

  return {
    state,
    isConnected,
    error: sseError || state.error,
    run,
    stop,
    reset,
  };
}
