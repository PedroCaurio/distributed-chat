import type { ChatMessage, UserProfile } from '../types';
import { getInitials, historyEntryToMessage, type HistoryEntry } from '../utils/chatMappers';

const API_BASE = (import.meta.env.VITE_PROXY_URL ?? '/api').replace(/\/$/, '');

type WelcomeResponse = {
  type: 'welcome';
  client_id: string;
  username: string;
  history: HistoryEntry[];
};

type ErrorResponse = {
  type: 'error';
  message: string;
};

export type JoinChatResult = {
  user: UserProfile;
  messages: ChatMessage[];
};

async function parseJson<T>(response: Response): Promise<T> {
  return (await response.json()) as T;
}

export async function joinChat(username: string): Promise<JoinChatResult> {
  const response = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: username.trim() }),
  });

  const payload = await parseJson<WelcomeResponse | ErrorResponse>(response);

  if (!response.ok || payload.type === 'error') {
    const message =
      payload.type === 'error' ? payload.message : 'Não foi possível entrar no chat.';
    throw new Error(message);
  }

  const trimmedUsername = payload.username;
  const user: UserProfile = {
    id: payload.client_id,
    username: trimmedUsername,
    initials: getInitials(trimmedUsername),
    status: 'online',
  };

  const messages = payload.history.map((entry) =>
    historyEntryToMessage(entry, trimmedUsername),
  );

  return { user, messages };
}

export async function sendMessage(content: string): Promise<void> {
  const response = await fetch(`${API_BASE}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: content.trim() }),
  });

  if (!response.ok) {
    let detail = 'Não foi possível enviar a mensagem.';
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
}

export async function checkProxyHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export function getApiBaseUrl(): string {
  return API_BASE;
}
