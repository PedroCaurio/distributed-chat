import type { ChatMessage, UserProfile } from '../types';
import {
  clearStoredSessionId,
  getStoredSessionId,
  setStoredSessionId,
} from '../lib/sessionStorage';
import { getInitials, historyEntryToMessage, type HistoryEntry } from '../utils/chatMappers';

const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '');

function apiUrl(path: string): string {
  const base = API_BASE || '';
  return `${base}${path}`;
}

function authHeaders(sessionId: string | null): HeadersInit {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (sessionId) {
    headers['X-Session-Id'] = sessionId;
  }
  return headers;
}

type WelcomeResponse = {
  type: 'welcome';
  session_id: string;
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
  sessionId: string;
};

async function parseJson<T>(response: Response): Promise<T> {
  return (await response.json()) as T;
}

export function getApiBaseUrl(): string {
  return API_BASE;
}

export function getSessionId(): string | null {
  return getStoredSessionId();
}

export async function joinChat(username: string): Promise<JoinChatResult> {
  const response = await fetch(apiUrl('/login'), {
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

  setStoredSessionId(payload.session_id);
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

  return { user, messages, sessionId: payload.session_id };
}

export async function sendMessage(content: string, sessionId: string): Promise<void> {
  const response = await fetch(apiUrl('/messages'), {
    method: 'POST',
    headers: authHeaders(sessionId),
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

export async function sendHeartbeat(sessionId: string): Promise<void> {
  await fetch(apiUrl('/heartbeat'), {
    method: 'POST',
    headers: authHeaders(sessionId),
  });
}

export async function fetchHistorySince(
  since: number,
  sessionId: string,
): Promise<HistoryEntry[]> {
  const response = await fetch(apiUrl(`/history?since=${since}`), {
    headers: authHeaders(sessionId),
  });
  if (!response.ok) {
    return [];
  }
  const body = (await response.json()) as { messages: HistoryEntry[] };
  return body.messages ?? [];
}

export async function logout(sessionId: string): Promise<void> {
  await fetch(apiUrl('/logout'), {
    method: 'POST',
    headers: authHeaders(sessionId),
  });
  clearStoredSessionId();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(apiUrl('/health'));
    return response.ok;
  } catch {
    return false;
  }
}
