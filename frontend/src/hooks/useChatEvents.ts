import { useEffect, useRef } from 'react';
import { fetchHistorySince, getApiBaseUrl, sendHeartbeat } from '../services/chatService';
import type { SsePayload } from '../utils/chatMappers';

type UseChatEventsOptions = {
  enabled: boolean;
  sessionId: string;
  onEvent: (payload: SsePayload) => void;
  onCatchUp: (payloads: SsePayload[]) => void;
  onReconnected?: () => void;
};

export function useChatEvents({
  enabled,
  sessionId,
  onEvent,
  onCatchUp,
  onReconnected,
}: UseChatEventsOptions): void {
  const lastTsRef = useRef(0);
  const onEventRef = useRef(onEvent);
  const onCatchUpRef = useRef(onCatchUp);
  const onReconnectedRef = useRef(onReconnected);

  onEventRef.current = onEvent;
  onCatchUpRef.current = onCatchUp;
  onReconnectedRef.current = onReconnected;

  useEffect(() => {
    if (!enabled || !sessionId) {
      return;
    }

    let source: EventSource | null = null;
    let disposed = false;
    let heartbeatTimer: number | undefined;
    let reconnectTimer: number | undefined;

    const syncMissed = async () => {
      const missed = await fetchHistorySince(lastTsRef.current, sessionId);
      if (missed.length > 0) {
        onCatchUpRef.current(
          missed.map((m) => ({
            type: 'chat',
            username: m.username,
            text: m.text,
            ts: m.ts,
            id: m.id,
          })),
        );
        const maxTs = Math.max(...missed.map((m) => m.ts));
        lastTsRef.current = Math.max(lastTsRef.current, maxTs);
      }
    };

    const connect = () => {
      if (disposed) {
        return;
      }
      const base = getApiBaseUrl();
      const url = `${base}/events?session=${encodeURIComponent(sessionId)}`;
      source = new EventSource(url, { withCredentials: true });

      source.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as SsePayload;
          if (typeof payload.ts === 'number') {
            lastTsRef.current = Math.max(lastTsRef.current, payload.ts);
          }
          onEventRef.current(payload);
        } catch {
          // frame inválido
        }
      };

      source.onerror = () => {
        source?.close();
        source = null;
        if (disposed) {
          return;
        }
        void syncMissed().then(() => {
          onReconnectedRef.current?.();
          reconnectTimer = window.setTimeout(connect, 1500);
        });
      };
    };

    connect();

    heartbeatTimer = window.setInterval(() => {
      void sendHeartbeat(sessionId);
    }, 60_000);

    return () => {
      disposed = true;
      source?.close();
      if (heartbeatTimer) {
        window.clearInterval(heartbeatTimer);
      }
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
    };
  }, [enabled, sessionId]);
}
