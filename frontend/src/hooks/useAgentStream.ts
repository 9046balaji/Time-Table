import { useEffect, useState, useRef } from 'react';
import { getWsBaseUrl } from '@/lib/api';

export interface StreamEvent {
  type: string;
  session_id: number;
  data: any;
  timestamp?: string;
}

export function useAgentStream(sessionId?: number) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const wsUrl = `${getWsBaseUrl()}/api/v1/agent/stream/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (evt) => {
      try {
        const parsed = JSON.parse(evt.data);
        setEvents((prev) => [parsed, ...prev]);
      } catch (err) {
        console.error('Failed to parse WebSocket message', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = (err) => {
      console.error('Agent WebSocket error', err);
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [sessionId]);

  const sendPing = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send('ping');
    }
  };

  return { events, isConnected, sendPing };
}
