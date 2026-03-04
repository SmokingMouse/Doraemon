'use client';

import { useEffect, useRef } from 'react';
import { useChatStore } from '@/store/chatStore';
import { MessageItem } from './MessageItem';
import { StreamingMessage } from './StreamingMessage';

export function MessageList() {
  const messages = useChatStore((state) => state.messages);
  const streamingContent = useChatStore((state) => state.streamingContent);
  const status = useChatStore((state) => state.status);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // 只在有新消息或 streaming 内容时滚动
    if (messages.length > 0 || streamingContent) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages.length, streamingContent]);

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto p-6">
      {messages.length === 0 && !streamingContent && (
        <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500">
          <p>Start a conversation...</p>
        </div>
      )}

      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}

      {status === 'thinking' && (
        <div className="flex justify-start mb-4">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-3 text-gray-500 dark:text-gray-400">
            Thinking...
          </div>
        </div>
      )}

      {streamingContent && <StreamingMessage content={streamingContent} />}

      <div ref={messagesEndRef} />
    </div>
  );
}
