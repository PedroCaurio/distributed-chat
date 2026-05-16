import { useCallback, useState } from 'react';
import ChatScreen from './components/ChatScreen';
import IdentityScreen from './components/IdentityScreen';
import { useChatEvents } from './hooks/useChatEvents';
import { joinChat } from './services/chatService';
import type { AppSession, ChatMessage } from './types';
import {
  GLOBAL_CONVERSATION_ID,
  presenceToSystemMessage,
  socketChatToMessage,
  type SsePayload,
} from './utils/chatMappers';

function appendUniqueMessage(messages: ChatMessage[], next: ChatMessage): ChatMessage[] {
  if (messages.some((item) => item.id === next.id)) {
    return messages;
  }
  return [...messages, next];
}

export default function App() {
  const [session, setSession] = useState<AppSession>({ status: 'anonymous' });
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const handleSseEvent = useCallback(
    (payload: SsePayload) => {
      if (session.status !== 'authenticated') {
        return;
      }

      const currentUsername = session.user.username;

      if (payload.type === 'chat' && payload.username && payload.text && payload.ts && payload.id) {
        const message = socketChatToMessage(
          {
            username: payload.username,
            text: payload.text,
            ts: payload.ts,
            id: payload.id,
          },
          currentUsername,
        );
        setMessages((prev) => appendUniqueMessage(prev, message));
        return;
      }

      if (payload.type === 'user_joined' || payload.type === 'user_left') {
        const systemMessage = presenceToSystemMessage(payload, payload.type);
        if (systemMessage) {
          setMessages((prev) => appendUniqueMessage(prev, systemMessage));
        }
      }
    },
    [session],
  );

  useChatEvents(session.status === 'authenticated', handleSseEvent);

  async function handleLogin(username: string) {
    const { user, messages: historyMessages } = await joinChat(username);
    setMessages(historyMessages);
    setSession({ status: 'authenticated', user });
  }

  if (session.status === 'authenticated') {
    return <ChatScreen currentUser={session.user} messages={messages} conversationId={GLOBAL_CONVERSATION_ID} />;
  }

  return <IdentityScreen onLogin={handleLogin} />;
}
