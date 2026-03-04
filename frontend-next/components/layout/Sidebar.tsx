'use client';

import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useChatStore } from '@/store/chatStore';

export function Sidebar() {
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);
  const clearMessages = useChatStore((state) => state.clearMessages);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleNewChat = () => {
    clearMessages();
  };

  return (
    <div className="w-64 bg-gray-800 text-white flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-xl font-bold">Doraemon Chat</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <button
          onClick={handleNewChat}
          className="w-full bg-primary hover:bg-primary-dark text-white font-semibold py-2 px-4 rounded-lg transition-colors mb-4"
        >
          + New Chat
        </button>

        <div className="text-sm text-gray-400">
          <p>Session management coming soon...</p>
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
