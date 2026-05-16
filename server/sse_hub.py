"""Hub local de assinantes SSE (uma fila por conexão de navegador)."""

from __future__ import annotations

import queue
import threading
from typing import Any, Final


class SseHub:
    """
    Distribui eventos pub/sub para filas locais de clientes web conectados.

    Cada conexão SSE possui uma thread de envio alimentada por ``queue.Queue``.
    """

    __slots__ = ("_lock", "_queues")

    def __init__(self) -> None:
        self._lock: Final[threading.Lock] = threading.Lock()
        self._queues: set[queue.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> queue.Queue[dict[str, Any]]:
        q: queue.Queue[dict[str, Any]] = queue.Queue()
        with self._lock:
            self._queues.add(q)
        return q

    def unsubscribe(self, q: queue.Queue[dict[str, Any]]) -> None:
        with self._lock:
            self._queues.discard(q)

    def broadcast(self, payload: dict[str, Any]) -> None:
        with self._lock:
            targets = list(self._queues)
        for q in targets:
            try:
                q.put_nowait(payload)
            except queue.Full:
                continue
