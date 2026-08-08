'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { getApiBaseUrl, getWsBaseUrl } from '@/lib/api';

export interface SolverProgressState {
  isSolving: boolean;
  isComplete: boolean;
  runId: string | null;
  generation: number;
  fitness: number;
  hardViolations: number;
  softViolations: number;
  runtimeSeconds: number;
  message: string;
  history: Array<{ generation: number; hardViolations: number; fitness: number }>;
  error: string | null;
}

export function useSolver() {
  const [state, setState] = useState<SolverProgressState>({
    isSolving: false,
    isComplete: false,
    runId: null,
    generation: 0,
    fitness: -51000,
    hardViolations: 51,
    softViolations: 12,
    runtimeSeconds: 0,
    message: 'Solver Engine Standby',
    history: [],
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);

  const startSolver = async (algorithm: string = 'CP-SAT') => {
    setState((prev) => ({
      ...prev,
      isSolving: true,
      isComplete: false,
      error: null,
      message: 'Submitting optimization task to Celery backend...',
      history: [],
    }));

    try {
      const apiBase = getApiBaseUrl();
      const res = await axios.post(`${apiBase}/api/v1/solve`, { algorithm });
      const runId = res.data?.run_id || 'run_1';

      setState((prev) => ({
        ...prev,
        runId,
        message: `Task ${runId} queued. Connecting to real-time progress stream...`,
      }));

      const wsBase = getWsBaseUrl();
      const wsUrl = `${wsBase}/api/v1/solve/${runId}/stream`;
      const ws = new WebSocket(wsUrl);

      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'progress') {
            setState((prev) => ({
              ...prev,
              generation: data.generation,
              fitness: data.fitness,
              hardViolations: data.hard_violations,
              softViolations: data.soft_violations,
              runtimeSeconds: data.runtime_seconds,
              message: data.message,
              history: [
                ...prev.history,
                { generation: data.generation, hardViolations: data.hard_violations, fitness: data.fitness },
              ],
            }));
          } else if (data.type === 'complete') {
            setState((prev) => ({
              ...prev,
              isSolving: false,
              isComplete: true,
              hardViolations: data.hard_violations,
              softViolations: data.soft_violations,
              runtimeSeconds: data.runtime_seconds,
              message: data.message,
            }));
            ws.close();
          }
        } catch (err) {
          console.error('Failed to parse WebSocket solver message', err);
        }
      };

      ws.onerror = () => {
        setState((prev) => ({
          ...prev,
          isSolving: false,
          error: 'WebSocket connection failed. Verify Celery & Redis containers are running.',
          message: 'Solver stream disconnected.',
        }));
      };
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        isSolving: false,
        error: err?.response?.data?.detail || 'Failed to dispatch solver task.',
        message: 'Solver submission error.',
      }));
    }
  };

  useEffect(() => {
    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close(1000);
      }
    };
  }, []);

  return { state, startSolver };
}
