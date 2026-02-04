import type { ThinkRequest, ExamplesResponse } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchExamples(): Promise<ExamplesResponse> {
  const response = await fetch(`${API_BASE}/api/examples`);
  if (!response.ok) {
    throw new Error('Failed to fetch examples');
  }
  return response.json();
}

export async function healthCheck(): Promise<{ status: string; search_enabled: boolean; search_provider: string | null }> {
  const response = await fetch(`${API_BASE}/api/health`);
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}

export async function* streamThink(request: ThinkRequest): AsyncGenerator<{ event: string; data: unknown }> {
  const response = await fetch(`${API_BASE}/api/think`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
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
            yield { event: currentEvent, data: JSON.parse(currentData) };
          } catch {
            // Skip malformed JSON
          }
          currentEvent = '';
          currentData = '';
        }
      }
    }
  }
}
