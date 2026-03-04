'use client';

import { AuthGuard } from '@/components/auth/AuthGuard';
import { Sidebar } from '@/components/layout/Sidebar';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden bg-gray-50 dark:bg-gray-900">
          {children}
        </div>
      </div>
    </AuthGuard>
  );
}
