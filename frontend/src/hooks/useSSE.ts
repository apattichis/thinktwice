import { useCallback, useRef, useState } from 'react';
import type { ThinkRequest } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SSEEvent {
  event: string;
  data: unknown;
}

interface UseSSEReturn {
  isConnected: boolean;
  error: string | null;
  startStream: (request: ThinkRequest, onEvent: (event: SSEEvent) => void) => Promise<void>;
  stopStream: () => void;
}

export function useSSE(): UseSSEReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const startStream = useCallback(async (
    request: ThinkRequest,
    onEvent: (event: SSEEvent) => void
  ) => {
    // Clean up any existing stream
    stopStream();
    setError(null);
    setIsConnected(true);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE}/api/think`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = '';
        let currentData = '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7);
          } else if (line.startsWith('data: ')) {
            currentData = line.slice(6);
            if (currentEvent && currentData) {
              try {
                onEvent({ event: currentEvent, data: JSON.parse(currentData) });
              } catch {
                // Skip malformed JSON
              }
              currentEvent = '';
              currentData = '';
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Stream was intentionally stopped
        return;
      }
      const errorMessage = err instanceof Error ? err.message : 'Stream failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsConnected(false);
      abortControllerRef.current = null;
    }
  }, [stopStream]);

  return {
    isConnected,
    error,
    startStream,
    stopStream,
  };
}
