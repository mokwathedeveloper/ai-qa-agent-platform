'use client';

import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  status: string;
  logs: string[];
  bugs?: any[];
  message: string;
}

export function useWebSocket(jobId: string | null) {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'Connecting' | 'Open' | 'Closed'>('Closed');
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = API_URL.replace('http', 'ws') + `/ws/${jobId}`;

    ws.current = new WebSocket(wsUrl);
    setConnectionStatus('Connecting');

    ws.current.onopen = () => {
      setConnectionStatus('Open');
    };

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setLastMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.current.onclose = () => {
      setConnectionStatus('Closed');
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('Closed');
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [jobId]);

  return { lastMessage, connectionStatus };
}