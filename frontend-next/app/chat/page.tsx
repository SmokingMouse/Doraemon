'use client';

import { useState, useRef } from 'react';
import { useTheme } from 'next-themes';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { ShortcutsDialog } from '@/components/ShortcutsDialog';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useChatStore } from '@/store/chatStore';
import { createSession } from '@/lib/api';

export default function ChatPage() {
  const { sendMessage } = useWebSocket();
  const { theme, setTheme } = useTheme();
  const { clearMessages, setCurrentSession } = useChatStore();
  const [showShortcuts, setShowShortcuts] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleNewChat = async () => {
    try {
      const { session_id } = await createSession();
      setCurrentSession(session_id);
      clearMessages();
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleFocusInput = () => {
    inputRef.current?.focus();
  };

  const handleToggleDarkMode = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  useKeyboardShortcuts([
    {
      key: 'k',
      ctrl: true,
      action: handleNewChat,
      description: 'New chat',
    },
    {
      key: '/',
      ctrl: true,
      action: handleFocusInput,
      description: 'Focus input',
    },
    {
      key: 'd',
      ctrl: true,
      action: handleToggleDarkMode,
      description: 'Toggle dark mode',
    },
    {
      key: '?',
      shift: true,
      action: () => setShowShortcuts(true),
      description: 'Show shortcuts',
    },
  ]);

  return (
    <>
      <MessageList />
      <MessageInput onSend={sendMessage} inputRef={inputRef} />
      <ShortcutsDialog isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
    </>
  );
}
