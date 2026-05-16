import { useEffect } from 'react';
import { getApiBaseUrl } from '../services/chatService';
import type { SsePayload } from '../utils/chatMappers';

export function useChatEvents(enabled: boolean, onEvent: (payload: SsePayload) => void): void {
  useEffect(() => {
    if (!enabled) {
      return;
    }

    const source = new EventSource(`${getApiBaseUrl()}/events`);

    source.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as SsePayload;
        onEvent(payload);
      } catch {
        // frame inválido — ignorar
      }
    };

    source.onerror = () => {
      // O navegador tenta reconectar automaticamente; não encerramos aqui.
    };

    return () => {
      source.close();
    };
  }, [enabled, onEvent]);
}
