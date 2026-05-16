"""Estado compartilhado do proxy: bridge TCP + handshake de login."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any

from common.protocol import MessageType

from client.config import ProxySettings
from client.inbound import InboundDemux
from client.socket_bridge import SocketBridge

logger = logging.getLogger(__name__)


class ProxyRuntime:
    """
    Um processo proxy atende tipicamente **um** usuário do chat.

    (Uma conexão TCP com o servidor; várias abas podem consumir o mesmo SSE.)
    """

    __slots__ = ("_settings", "_demux", "_bridge", "_user_lock", "_username")

    def __init__(self, settings: ProxySettings) -> None:
        self._settings = settings
        self._demux = InboundDemux()
        self._bridge = SocketBridge(settings.server_host, settings.server_port, self._demux)
        self._user_lock = threading.Lock()
        self._username: str | None = None

    def connect(self) -> None:
        logger.info(
            "Conectando ao servidor de chat em %s:%s",
            self._settings.server_host,
            self._settings.server_port,
        )
        self._bridge.connect()

    def close(self) -> None:
        self._bridge.close()

    @property
    def username(self) -> str | None:
        return self._username

    def is_connected(self) -> bool:
        return not self._bridge.is_closed()

    def sse_queue(self) -> queue.Queue[dict[str, Any]]:
        """Fila consumida pelo endpoint SSE (eventos após o handshake)."""
        return self._demux.sse_iter()

    def login(self, username: str, *, timeout_s: float = 15.0) -> dict[str, Any]:
        with self._user_lock:
            if self._username is not None:
                msg = "Este proxy já autenticou um usuário; reinicie o processo para trocar."
                raise RuntimeError(msg)

        self._demux.arm_login_wait()
        try:
            self._bridge.send_login(username)
            resp = self._demux.wait_login_response(timeout_s)
        finally:
            self._demux.disarm_login_wait()

        if resp.get("type") == MessageType.ERROR.value:
            return resp

        if resp.get("type") != MessageType.WELCOME.value:
            msg = f"Resposta inesperada no login: {resp.get('type')!r}"
            raise RuntimeError(msg)

        uname = str(resp.get("username", username))
        with self._user_lock:
            self._username = uname
        return resp

    def send_chat(self, text: str) -> None:
        with self._user_lock:
            if self._username is None:
                msg = "Login obrigatório"
                raise RuntimeError(msg)
        self._bridge.send_message(text)
