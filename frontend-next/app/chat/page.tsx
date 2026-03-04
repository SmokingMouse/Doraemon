'use client';

import { useState, useRef } from 'react';
import { useTheme } from 'next-themes';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { ShortcutsDialog } from '@/components/ShortcutsDialog';
import { CommandPalette } from '@/components/CommandPalette';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useChatStore } from '@/store/chatStore';
import { createSession, getSessions } from '@/lib/api';
import { generateMessageId } from '@/lib/utils';

export default function ChatPage() {
  const { sendMessage } = useWebSocket();
  const { theme, setTheme } = useTheme();
  const { clearMessages, setCurrentSession, addMessage } = useChatStore();
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleNewChat = async () => {
    try {
      const { session_id } = await createSession();
      setCurrentSession(session_id);
      clearMessages();
      addMessage({
        id: generateMessageId(),
        role: 'assistant',
        content: '✨ 新会话已创建！现在你可以开始一个全新的对话了。',
        timestamp: Date.now(),
      });
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleClearContext = () => {
    clearMessages();
    addMessage({
      id: generateMessageId(),
      role: 'assistant',
      content: '🧹 上下文已清空！当前会话的对话历史已保存，但 Claude 不再记得之前的对话内容。',
      timestamp: Date.now(),
    });
  };

  const handleShowSessions = async () => {
    try {
      const sessions = await getSessions();
      const sessionList = sessions
        .map((s, i) => `${i + 1}. Session #${s.id} - ${s.message_count} 条消息`)
        .join('\n');
      addMessage({
        id: generateMessageId(),
        role: 'assistant',
        content: `📋 会话列表：\n\n${sessionList}\n\n点击侧边栏的会话可以切换。`,
        timestamp: Date.now(),
      });
    } catch (error) {
      console.error('Failed to get sessions:', error);
    }
  };

  const handleCommand = async (command: string) => {
    switch (command) {
      case '/new':
        await handleNewChat();
        break;
      case '/clear':
        handleClearContext();
        break;
      case '/sessions':
        await handleShowSessions();
        break;
      case '/thinking':
        addMessage({
          id: generateMessageId(),
          role: 'assistant',
          content: '💭 思考过程显示功能将在后续版本中实现。',
          timestamp: Date.now(),
        });
        break;
      case '/stats':
        addMessage({
          id: generateMessageId(),
          role: 'assistant',
          content: '📊 统计功能将在后续版本中实现。',
          timestamp: Date.now(),
        });
        break;
      default:
        addMessage({
          id: generateMessageId(),
          role: 'assistant',
          content: `❌ 未知命令: ${command}\n\n可用命令：/new, /clear, /sessions, /thinking, /stats`,
          timestamp: Date.now(),
        });
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
      key: 'p',
      ctrl: true,
      action: () => setShowCommands(true),
      description: 'Command palette',
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
      <MessageInput onSend={sendMessage} inputRef={inputRef} onCommand={handleCommand} />
      <ShortcutsDialog isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
      <CommandPalette
        isOpen={showCommands}
        onClose={() => setShowCommands(false)}
        onCommand={handleCommand}
      />
    </>
  );
}
