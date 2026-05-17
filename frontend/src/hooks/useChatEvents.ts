import { useEffect, useRef } from 'react';
import { demoLog } from '../lib/demoLog';
import { getTraceTabId, traceLog } from '../lib/traceLog';
import {
  fetchHistorySince,
  getApiBaseUrl,
  isSessionAlive,
  type HistoryFetchResult,
} from '../services/chatService';
import type { SsePayload } from '../utils/chatMappers';

type UseChatEventsOptions = {
  enabled: boolean;
  sessionId: string;
  onEvent: (payload: SsePayload) => void;
  onCatchUp: (payloads: SsePayload[]) => void;
  onReconnected?: () => void;
  onSessionInvalid?: () => void;
};

const MAX_RECONNECT_ATTEMPTS = 3;

export function useChatEvents({
  enabled,
  sessionId,
  onEvent,
  onCatchUp,
  onReconnected,
  onSessionInvalid,
}: UseChatEventsOptions): void {
  const lastTsRef = useRef(0);
  const effectGenRef = useRef(0);
  const onEventRef = useRef(onEvent);
  const onCatchUpRef = useRef(onCatchUp);
  const onReconnectedRef = useRef(onReconnected);
  const onSessionInvalidRef = useRef(onSessionInvalid);

  onEventRef.current = onEvent;
  onCatchUpRef.current = onCatchUp;
  onReconnectedRef.current = onReconnected;
  onSessionInvalidRef.current = onSessionInvalid;

  useEffect(() => {
    const gen = ++effectGenRef.current;

    if (!enabled || !sessionId) {
      traceLog('useChatEvents: efeito inativo', { enabled, sessionId: sessionId || '-' });
      return;
    }

    traceLog('useChatEvents: efeito INICIADO', {
      gen,
      sessionId: sessionId.slice(0, 12),
      tab: getTraceTabId(),
    });

    let source: EventSource | null = null;
    let disposed = false;
    let reconnectTimer: number | undefined;
    let reconnectAttempts = 0;

    const stopReconnectLoop = (reason: string, extra?: Record<string, unknown>) => {
      if (disposed) {
        traceLog('stopReconnect ignorado (já disposed)', { reason, gen });
        return;
      }
      disposed = true;
      traceLog('stopReconnect', { reason, gen, ...extra });
      demoLog('useChatEvents', reason);
      source?.close();
      source = null;
      if (reconnectTimer !== undefined) {
        window.clearTimeout(reconnectTimer);
        reconnectTimer = undefined;
      }
      onSessionInvalidRef.current?.();
    };

    const handleHistoryResult = (result: HistoryFetchResult): boolean => {
      if (result.unauthorized) {
        stopReconnectLoop('401 em /history — parar loop', { gen });
        return false;
      }
      if (result.messages.length > 0) {
        onCatchUpRef.current(
          result.messages.map((m) => ({
            type: 'chat',
            username: m.username,
            text: m.text,
            ts: m.ts,
            id: m.id,
          })),
        );
        const maxTs = Math.max(...result.messages.map((m) => m.ts));
        lastTsRef.current = Math.max(lastTsRef.current, maxTs);
      }
      return true;
    };

    const connect = async () => {
      if (disposed) {
        traceLog('connect abortado (disposed)', { gen });
        return;
      }

      traceLog('connect: checando heartbeat antes do SSE', {
        gen,
        attempt: reconnectAttempts + 1,
      });

      const alive = await isSessionAlive(sessionId);
      if (disposed) {
        return;
      }

      traceLog('connect: resultado heartbeat', { gen, alive });

      if (!alive) {
        stopReconnectLoop('heartbeat falhou — sessão ausente no servidor', { gen });
        return;
      }

      const base = getApiBaseUrl();
      const url = `${base}/events?session=${encodeURIComponent(sessionId)}`;
      traceLog('connect: abrindo EventSource', { gen, url });
      demoLog('useChatEvents.connect', 'EventSource GET /events', {
        attempt: reconnectAttempts + 1,
      });

      source = new EventSource(url, { withCredentials: true });

      source.onopen = () => {
        traceLog('EventSource onopen', { gen, readyState: source?.readyState });
      };

      source.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as SsePayload;
          if (payload.type === 'error') {
            stopReconnectLoop(`SSE payload error: ${payload.message}`, { gen });
            return;
          }
          demoLog('useChatEvents.onmessage', `SSE type=${payload.type}`, payload);
          reconnectAttempts = 0;
          if (typeof payload.ts === 'number') {
            lastTsRef.current = Math.max(lastTsRef.current, payload.ts);
          }
          onEventRef.current(payload);
        } catch {
          traceLog('onmessage: JSON inválido', { gen, raw: event.data?.slice(0, 80) });
        }
      };

      source.onerror = () => {
        const readyState = source?.readyState;
        traceLog('EventSource onerror', {
          gen,
          readyState,
          disposed,
          reconnectAttempts,
        });
        source?.close();
        source = null;
        if (disposed) {
          return;
        }

        void (async () => {
          traceLog('onerror: buscando /history', { gen, lastTs: lastTsRef.current });
          const result = await fetchHistorySince(lastTsRef.current, sessionId);
          if (disposed) {
            return;
          }
          if (!handleHistoryResult(result)) {
            return;
          }

          reconnectAttempts += 1;
          traceLog('onerror: vai reconectar', { gen, reconnectAttempts });

          if (reconnectAttempts > MAX_RECONNECT_ATTEMPTS) {
            stopReconnectLoop('limite de reconexões', { gen, reconnectAttempts });
            return;
          }

          onReconnectedRef.current?.();
          const delayMs = Math.min(2000 * reconnectAttempts, 10_000);
          reconnectTimer = window.setTimeout(() => {
            traceLog('timeout reconectar disparado', { gen, delayMs });
            void connect();
          }, delayMs);
        })();
      };
    };

    void connect();

    return () => {
      traceLog('useChatEvents: efeito CLEANUP', { gen, sessionId: sessionId.slice(0, 12) });
      disposed = true;
      source?.close();
      if (reconnectTimer !== undefined) {
        window.clearTimeout(reconnectTimer);
      }
    };
  }, [enabled, sessionId]);
}
