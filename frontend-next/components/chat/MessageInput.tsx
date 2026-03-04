'use client';

import { useState } from 'react';
import { useChatStore } from '@/store/chatStore';

interface MessageInputProps {
  onSend: (content: string) => void;
  inputRef?: React.RefObject<HTMLTextAreaElement>;
  onCommand?: (command: string) => void;
}

export function MessageInput({ onSend, inputRef, onCommand }: MessageInputProps) {
  const [input, setInput] = useState('');
  const status = useChatStore((state) => state.status);
  const addMessage = useChatStore((state) => state.addMessage);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || status !== 'idle') return;

    // 检查是否是命令
    if (input.trim().startsWith('/')) {
      if (onCommand) {
        onCommand(input.trim());
        setInput('');
        return;
      }
    }

    // Add user message to chat
    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    });

    // Send to WebSocket
    onSend(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
      <div className="flex gap-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行, / 开头输入命令)"
          className="flex-1 resize-none border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 rounded-lg px-4 py-3 focus:ring-2 focus:ring-primary focus:border-transparent outline-none placeholder:text-gray-400 dark:placeholder:text-gray-500"
          rows={3}
          disabled={status !== 'idle'}
        />
        <button
          type="submit"
          disabled={!input.trim() || status !== 'idle'}
          className="px-6 py-3 bg-primary hover:bg-primary-dark text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </form>
  );
}
