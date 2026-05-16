import type { ChatMessage } from '../types';

export const GLOBAL_CONVERSATION_ID = 'global';

export type HistoryEntry = {
  username: string;
  text: string;
  ts: number;
  id: string;
};

export type SsePayload = {
  type: string;
  username?: string;
  text?: string;
  ts?: number;
  id?: string;
  message?: string;
};

export function getInitials(username: string): string {
  return (
    username
      .split(/[\s._-]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('') || 'U'
  );
}

export function formatSentAt(ts: number): string {
  return new Date(ts * 1000).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function historyEntryToMessage(entry: HistoryEntry, currentUsername: string): ChatMessage {
  return socketChatToMessage(
    {
      username: entry.username,
      text: entry.text,
      ts: entry.ts,
      id: entry.id,
    },
    currentUsername,
  );
}

export function socketChatToMessage(
  payload: Required<Pick<SsePayload, 'username' | 'text' | 'ts' | 'id'>>,
  currentUsername: string,
): ChatMessage {
  const authorName = payload.username;
  return {
    id: payload.id,
    conversationId: GLOBAL_CONVERSATION_ID,
    authorId: authorName,
    authorName,
    authorInitials: getInitials(authorName),
    content: payload.text,
    sentAt: formatSentAt(payload.ts),
    direction: authorName === currentUsername ? 'outgoing' : 'incoming',
  };
}

export function presenceToSystemMessage(
  payload: SsePayload,
  kind: 'user_joined' | 'user_left',
): ChatMessage | null {
  if (!payload.username || payload.ts === undefined) {
    return null;
  }

  const verb = kind === 'user_joined' ? 'entrou' : 'saiu';
  return {
    id: `${kind}-${payload.username}-${payload.ts}`,
    conversationId: GLOBAL_CONVERSATION_ID,
    authorId: 'system',
    authorName: 'Sistema',
    authorInitials: 'SYS',
    content: `${payload.username} ${verb} na sala.`,
    sentAt: formatSentAt(payload.ts),
    direction: 'incoming',
  };
}
