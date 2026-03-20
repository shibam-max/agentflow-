'use client';

import { useState, useEffect, useCallback } from 'react';
import { AgentStep } from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export function useAgentStream(taskId: string | null) {
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const es = new EventSource(`${API_URL}/api/tasks/${taskId}/stream`, {
      withCredentials: true,
    });

    es.onmessage = (e) => {
      try {
        const event: AgentStep = JSON.parse(e.data);
        setSteps((prev) => [...prev, event]);
        if (event.type === 'FINAL' || event.type === 'ERROR') {
          setIsComplete(true);
          es.close();
        }
      } catch {
        setError('Failed to parse stream event');
      }
    };

    es.onerror = () => {
      setError('Stream connection lost');
      es.close();
    };

    return () => es.close();
  }, [taskId]);

  const reset = useCallback(() => {
    setSteps([]);
    setIsComplete(false);
    setError(null);
  }, []);

  return { steps, isComplete, error, reset };
}
