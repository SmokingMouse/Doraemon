'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useChatStore } from '@/store/chatStore';
import { getSessions, createSession, getMessages, deleteSession, Session } from '@/lib/api';
import { ThemeToggle } from '@/components/ThemeToggle';

export function Sidebar() {
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);
  const { clearMessages, setCurrentSession, setMessages, currentSessionId } = useChatStore();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // 加载会话列表
  const loadSessions = async () => {
    try {
      const data = await getSessions();
      setSessions(data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleNewChat = async () => {
    setLoading(true);
    try {
      const { session_id } = await createSession();
      setCurrentSession(session_id);
      clearMessages();
      await loadSessions();
    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSwitchSession = async (sessionId: number) => {
    if (sessionId === currentSessionId) return;

    setLoading(true);
    try {
      const messages = await getMessages(sessionId);
      setCurrentSession(sessionId);
      setMessages(
        messages.map((m) => ({
          id: String(m.created_at),
          role: m.role,
          content: m.content,
          timestamp: m.created_at,
        }))
      );
    } catch (error) {
      console.error('Failed to switch session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSession = async (sessionId: number, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm('确定要删除这个会话吗？')) return;

    setDeletingId(sessionId);
    try {
      console.log('Deleting session:', sessionId);
      await deleteSession(sessionId);
      console.log('Session deleted successfully');

      // 如果删除的是当前会话，清空消息
      if (sessionId === currentSessionId) {
        clearMessages();
        setCurrentSession(null);
      }

      await loadSessions();
    } catch (error) {
      console.error('Failed to delete session:', error);
      alert(`删除失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="w-64 bg-gray-800 dark:bg-gray-900 text-white flex flex-col">
      <div className="p-4 border-b border-gray-700 dark:border-gray-800">
        <h1 className="text-xl font-bold">Doraemon Chat</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <button
          onClick={handleNewChat}
          disabled={loading}
          className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-2 px-4 rounded-lg transition-colors mb-4 disabled:opacity-50"
        >
          {loading ? 'Creating...' : '+ New Chat'}
        </button>

        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-gray-400 mb-2">Recent Sessions</h2>
          {sessions.length === 0 ? (
            <p className="text-sm text-gray-500">No sessions yet</p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`relative group rounded-lg transition-colors ${
                  currentSessionId === session.id
                    ? 'bg-gray-700 dark:bg-gray-800 border border-primary'
                    : 'bg-gray-750 dark:bg-gray-850 hover:bg-gray-700 dark:hover:bg-gray-800'
                }`}
              >
                <button
                  onClick={() => handleSwitchSession(session.id)}
                  className="w-full text-left p-3"
                  disabled={deletingId === session.id}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-medium truncate pr-8">
                      Session #{session.id}
                    </span>
                    <span className="text-xs text-gray-400">{session.message_count}</span>
                  </div>
                  <div className="text-xs text-gray-400">{formatDate(session.last_active)}</div>
                </button>

                <button
                  onClick={(e) => handleDeleteSession(session.id, e)}
                  disabled={deletingId === session.id}
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-red-600 rounded transition-all disabled:opacity-50"
                  title="删除会话"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="p-4 border-t border-gray-700 dark:border-gray-800 space-y-2">
        <ThemeToggle />
        <button
          onClick={handleLogout}
          className="w-full bg-gray-700 dark:bg-gray-800 hover:bg-gray-600 dark:hover:bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
        >
          Logout
        </button>
      </div>
    </div>
  );
}
