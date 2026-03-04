'use client';

import { create } from 'zustand';
import { Message } from '@/types/api';
import { generateMessageId } from '@/lib/utils';

type ChatStatus = 'idle' | 'thinking' | 'streaming' | 'error';

interface ChatState {
  messages: Message[];
  streamingContent: string;
  status: ChatStatus;
  error: string | null;
  currentSessionId: number | null;

  addMessage: (message: Message) => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (chunk: string) => void;
  setStatus: (status: ChatStatus) => void;
  setError: (error: string | null) => void;
  completeStreaming: (finalContent?: string) => void;
  clearMessages: () => void;
  setCurrentSession: (sessionId: number | null) => void;
  setMessages: (messages: Message[]) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  streamingContent: '',
  status: 'idle',
  error: null,
  currentSessionId: null,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message],
  })),

  setStreamingContent: (content) => set({ streamingContent: content }),

  appendStreamingContent: (chunk) => set((state) => ({
    streamingContent: state.streamingContent + chunk,
  })),

  setStatus: (status) => set({ status }),

  setError: (error) => set({ error, status: error ? 'error' : 'idle' }),

  completeStreaming: (finalContent?: string) => {
    const { streamingContent } = get();
    // 如果提供了 finalContent，使用它；否则使用 streamingContent
    const content = finalContent || streamingContent;
    if (content) {
      set((state) => ({
        messages: [
          ...state.messages,
          {
            id: generateMessageId(),
            role: 'assistant',
            content: content,
            timestamp: Date.now(),
          },
        ],
        streamingContent: '',
        status: 'idle',
      }));
    }
  },

  clearMessages: () => set({ messages: [], streamingContent: '', status: 'idle', error: null }),

  setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),

  setMessages: (messages) => set({ messages }),
}));
