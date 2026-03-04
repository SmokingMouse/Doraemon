'use client';

import { useEffect, useRef } from 'react';
import { useChatStore } from '@/store/chatStore';
import { MessageItem } from './MessageItem';
import { StreamingMessage } from './StreamingMessage';

export function MessageList() {
  const messages = useChatStore((state) => state.messages);
  const streamingContent = useChatStore((state) => state.streamingContent);
  const status = useChatStore((state) => state.status);
  const containerRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (containerRef.current) {
      const timer = setTimeout(() => {
        if (containerRef.current) {
          containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [messages, streamingContent]);

  // 阻止滚动事件冒泡到外层
  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    const container = containerRef.current;
    if (!container) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const isAtTop = scrollTop === 0;
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - 1;

    // 如果在顶部向上滚动，或在底部向下滚动，阻止事件冒泡
    if ((isAtTop && e.deltaY < 0) || (isAtBottom && e.deltaY > 0)) {
      e.preventDefault();
      e.stopPropagation();
    }
  };

  return (
    <div
      className="h-full w-full overflow-y-auto overflow-x-hidden p-6"
      ref={containerRef}
      onWheel={handleWheel}
    >
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
    </div>
  );
}
