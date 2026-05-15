"""Registro thread-safe de clientes conectados para broadcast local."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Final

Sender = Callable[[bytes], None]


class ClientRegistry:
    """
    Mantém callbacks de envio por cliente (uma conexão TCP).

    Usado para entregar mensagens recebidas via Redis pub/sub a todos os sockets
    locais desta instância.
    """

    __slots__ = ("_lock", "_senders")

    def __init__(self) -> None:
        self._lock: Final[threading.Lock] = threading.Lock()
        self._senders: set[Sender] = set()

    def add(self, sender: Sender) -> None:
        with self._lock:
            self._senders.add(sender)

    def remove(self, sender: Sender) -> None:
        with self._lock:
            self._senders.discard(sender)

    def broadcast_bytes(self, frame: bytes, exclude: Sender | None = None) -> None:
        """Envia um frame NDJSON já serializado para todos os registrados."""
        with self._lock:
            targets = [s for s in self._senders if s is not exclude]
        for send in targets:
            try:
                send(frame)
            except OSError:
                # Conexão morta; a sessão fará cleanup em breve
                continue
