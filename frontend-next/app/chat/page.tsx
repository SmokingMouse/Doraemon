'use client';

import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function ChatPage() {
  const { sendMessage } = useWebSocket();

  return (
    <>
      <MessageList />
      <MessageInput onSend={sendMessage} />
    </>
  );
}
