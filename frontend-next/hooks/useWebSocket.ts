'use client';

import { useEffect, useRef } from 'react';
import { WebSocketManager } from '@/lib/websocket';
import { useAuthStore } from '@/store/authStore';
import { useChatStore } from '@/store/chatStore';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8765/ws';

export function useWebSocket() {
  const wsRef = useRef<WebSocketManager | null>(null);
  const token = useAuthStore((state) => state.token);
  const currentSessionId = useChatStore((state) => state.currentSessionId);
  const {
    appendStreamingContent,
    setStatus,
    setError,
    completeStreaming,
  } = useChatStore();

  useEffect(() => {
    if (!token) return;

    const ws = new WebSocketManager(WS_URL, token, {
      onAuthSuccess: () => {
        console.log('WebSocket authenticated');
      },
      onChunk: (content) => {
        appendStreamingContent(content);
      },
      onStatus: (status) => {
        if (status === 'thinking') {
          setStatus('thinking');
        } else if (status === 'streaming') {
          setStatus('streaming');
        }
      },
      onComplete: (content) => {
        completeStreaming(content);
      },
      onError: (message) => {
        setError(message);
      },
    });

    ws.connect();
    wsRef.current = ws;

    return () => {
      ws.disconnect();
    };
  }, [token, appendStreamingContent, setStatus, setError, completeStreaming]);

  const sendMessage = (content: string) => {
    if (wsRef.current) {
      wsRef.current.sendMessage(content, currentSessionId);
    }
  };

  return { sendMessage };
}
