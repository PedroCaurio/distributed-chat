"""Demultiplexação de mensagens vindas do socket (login síncrono vs. fluxo SSE)."""

from __future__ import annotations

import queue
import threading
from typing import Any, Final

from common.protocol import MessageType


class InboundDemux:
    """
    A thread de recepção envia todo payload parseado para cá.

    Durante o handshake de login, respostas ``welcome``/``error`` são entregues de
    forma síncrona; demais mensagens seguem para a fila consumida pelo SSE.
    """

    __slots__ = (
        "_in_lock",
        "_sse_queue",
        "_login_event",
        "_login_response",
    )

    def __init__(self) -> None:
        self._in_lock: Final[threading.Lock] = threading.Lock()
        self._sse_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._login_event: threading.Event | None = None
        self._login_response: dict[str, Any] | None = None

    def arm_login_wait(self) -> None:
        """Deve ser chamado *antes* de enviar o frame de login pelo socket."""
        with self._in_lock:
            self._login_event = threading.Event()
            self._login_response = None

    def disarm_login_wait(self) -> None:
        with self._in_lock:
            self._login_event = None
            self._login_response = None

    def wait_login_response(self, timeout_s: float) -> dict[str, Any]:
        with self._in_lock:
            evt = self._login_event
        if evt is None:
            msg = "arm_login_wait não foi chamado"
            raise RuntimeError(msg)
        if not evt.wait(timeout_s):
            msg = "timeout aguardando welcome/error do servidor"
            raise TimeoutError(msg)
        with self._in_lock:
            resp = self._login_response
        if resp is None:
            msg = "resposta de login ausente"
            raise RuntimeError(msg)
        return resp

    def push(self, msg: dict[str, Any]) -> None:
        typ = msg.get("type")
        with self._in_lock:
            evt = self._login_event
            if evt is not None and typ in {MessageType.WELCOME.value, MessageType.ERROR.value}:
                self._login_response = msg
                evt.set()
                return
        self._sse_queue.put(msg)

    def sse_iter(self) -> queue.Queue[dict[str, Any]]:
        return self._sse_queue
