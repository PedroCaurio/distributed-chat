import { useCallback, useRef, useState } from 'react';
import { demoLog } from './lib/demoLog';
import ChatScreen from './components/ChatScreen';
import IdentityScreen from './components/IdentityScreen';
import { useChatEvents } from './hooks/useChatEvents';
import { clearStoredSessionId } from './lib/sessionStorage';
import { joinChat, logout } from './services/chatService';
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

function applySsePayload(
  payload: SsePayload,
  currentUsername: string,
  prev: ChatMessage[],
): ChatMessage[] {
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
    return appendUniqueMessage(prev, message);
  }

  if (payload.type === 'user_joined' || payload.type === 'user_left') {
    const systemMessage = presenceToSystemMessage(payload, payload.type);
    if (systemMessage) {
      return appendUniqueMessage(prev, systemMessage);
    }
  }

  return prev;
}

export default function App() {
  const [session, setSession] = useState<AppSession>({ status: 'anonymous' });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [connectionNotice, setConnectionNotice] = useState('');
  const sessionInvalidHandled = useRef(false);

  const handleSseEvent = useCallback(
    (payload: SsePayload) => {
      if (session.status !== 'authenticated') {
        return;
      }
      demoLog('App.handleSseEvent', 'Atualizando lista de mensagens na tela', {
        type: payload.type,
      });
      setMessages((prev) => applySsePayload(payload, session.user.username, prev));
    },
    [session],
  );

  const handleCatchUp = useCallback(
    (payloads: SsePayload[]) => {
      if (session.status !== 'authenticated') {
        return;
      }
      setMessages((prev) => {
        let next = prev;
        for (const payload of payloads) {
          next = applySsePayload(payload, session.user.username, next);
        }
        return next;
      });
    },
    [session],
  );

  const handleReconnected = useCallback(() => {
    setConnectionNotice('Conexão restabelecida — você permanece no chat.');
  }, []);

  const handleDismissNotice = useCallback(() => {
    setConnectionNotice('');
  }, []);

  const handleSessionInvalid = useCallback(() => {
    if (sessionInvalidHandled.current) {
      return;
    }
    sessionInvalidHandled.current = true;
    clearStoredSessionId();
    if (session.status === 'authenticated') {
      void logout(session.sessionId);
    }
    setSession({ status: 'anonymous' });
    setMessages([]);
    setConnectionNotice('Sessão expirada ou inválida. Entre novamente com seu username.');
  }, [session]);

  useChatEvents({
    enabled: session.status === 'authenticated',
    sessionId: session.status === 'authenticated' ? session.sessionId : '',
    onEvent: handleSseEvent,
    onCatchUp: handleCatchUp,
    onReconnected: handleReconnected,
    onSessionInvalid: handleSessionInvalid,
  });

  async function handleLogin(username: string) {
    const { user, messages: historyMessages, sessionId } = await joinChat(username);
    sessionInvalidHandled.current = false;
    setMessages(historyMessages);
    setConnectionNotice('');
    setSession({ status: 'authenticated', user, sessionId });
  }

  if (session.status === 'authenticated') {
    return (
      <ChatScreen
        currentUser={session.user}
        sessionId={session.sessionId}
        messages={messages}
        conversationId={GLOBAL_CONVERSATION_ID}
        connectionNotice={connectionNotice}
        onDismissNotice={handleDismissNotice}
      />
    );
  }

  return (
    <IdentityScreen onLogin={handleLogin} notice={connectionNotice} onDismissNotice={handleDismissNotice} />
  );
}
