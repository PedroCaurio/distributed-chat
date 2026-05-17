"""Demultiplexação de mensagens TCP: handshake/RPC síncrono vs. fan-out SSE."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any, Final

logger = logging.getLogger(__name__)

from common.demo_log import demo
from common.protocol import MessageType


class InboundDemux:
    """
    A thread de recepção envia frames parseados para cá.

    Cada conexão SSE HTTP chama ``subscribe()`` e recebe uma fila própria;
    ``push`` replica o evento para todas as filas (evita competição entre
    consumidores na mesma ``queue.Queue``).
    """

    __slots__ = (
        "_in_lock",
        "_subscribers",
        "_rpc_event",
        "_rpc_kind",
        "_rpc_response",
    )

    def __init__(self) -> None:
        self._in_lock: Final[threading.Lock] = threading.Lock()
        self._subscribers: set[queue.Queue[dict[str, Any]]] = set()
        self._rpc_event: threading.Event | None = None
        self._rpc_kind: str | None = None
        self._rpc_response: dict[str, Any] | None = None

    def subscribe(self) -> queue.Queue[dict[str, Any]]:
        """Nova fila para uma conexão SSE (uma por ``GET /events``)."""
        q: queue.Queue[dict[str, Any]] = queue.Queue()
        with self._in_lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: queue.Queue[dict[str, Any]]) -> None:
        with self._in_lock:
            self._subscribers.discard(q)

    def arm_rpc(self, kind: str) -> None:
        """Deve ser chamado antes de enviar o frame que dispara a resposta."""
        with self._in_lock:
            self._rpc_kind = kind
            self._rpc_event = threading.Event()
            self._rpc_response = None

    def disarm_rpc(self) -> None:
        with self._in_lock:
            self._rpc_kind = None
            self._rpc_event = None
            self._rpc_response = None

    def wait_rpc(self, kind: str, *, timeout_s: float) -> dict[str, Any]:
        with self._in_lock:
            if self._rpc_kind != kind or self._rpc_event is None:
                msg = f"arm_rpc({kind!r}) não foi chamado"
                raise RuntimeError(msg)
            evt = self._rpc_event
        if not evt.wait(timeout_s):
            msg = f"timeout aguardando resposta RPC ({kind})"
            raise TimeoutError(msg)
        with self._in_lock:
            resp = self._rpc_response
        if resp is None:
            msg = "resposta RPC ausente"
            raise RuntimeError(msg)
        return resp

    def push(self, msg: dict[str, Any]) -> None:
        typ = msg.get("type")
        with self._in_lock:
            kind = self._rpc_kind
            evt = self._rpc_event
            if evt is not None and kind == "login" and typ in {
                MessageType.WELCOME.value,
                MessageType.ERROR.value,
            }:
                self._rpc_response = msg
                evt.set()
                return
            if evt is not None and kind == "history" and typ == MessageType.HISTORY.value:
                self._rpc_response = msg
                evt.set()
                return
            if typ in {MessageType.PONG.value, MessageType.PING.value}:
                return
            targets = list(self._subscribers)

        demo(
            logger,
            f"InboundDemux.push — repassa evento SSE type={typ!r} para {len(targets)} listener(s)",
            fn="client.inbound.InboundDemux.push",
        )
        for q in targets:
            try:
                q.put_nowait(msg)
            except queue.Full:
                continue
