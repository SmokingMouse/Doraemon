'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useChatStore } from '@/store/chatStore';
import { getSessions, createSession, getMessages, Session } from '@/lib/api';

export function Sidebar() {
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);
  const { clearMessages, setCurrentSession, setMessages, currentSessionId } = useChatStore();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);

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
    <div className="w-64 bg-gray-800 text-white flex flex-col">
      <div className="p-4 border-b border-gray-700">
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
              <button
                key={session.id}
                onClick={() => handleSwitchSession(session.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  currentSessionId === session.id
                    ? 'bg-gray-700 border border-primary'
                    : 'bg-gray-750 hover:bg-gray-700'
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="text-sm font-medium truncate">
                    Session #{session.id}
                  </span>
                  <span className="text-xs text-gray-400">{session.message_count}</span>
                </div>
                <div className="text-xs text-gray-400">{formatDate(session.last_active)}</div>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="p-4 border-t border-gray-700">
        <button
          onClick={handleLogout}
          className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
        >
          Logout
        </button>
      </div>
    </div>
  );
}
