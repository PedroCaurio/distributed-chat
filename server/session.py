"""Sessão TCP: uma thread por conexão (compatível com clientes socket nativos)."""

from __future__ import annotations

import logging
import socket
import threading
from typing import TYPE_CHECKING, Any

from common.protocol import MessageType, decode_line, encode_line
from server.chat_core import now_ts

if TYPE_CHECKING:
    from server.chat_core import ChatCore
    from server.config import ServerSettings
    from server.redis_service import RedisChatBackend
    from server.registry import ClientRegistry

logger = logging.getLogger(__name__)


class ClientSession(threading.Thread):
    """Thread de atendimento de um cliente conectado via TCP."""

    def __init__(
        self,
        conn: socket.socket,
        addr: tuple[str, int],
        *,
        core: ChatCore,
        backend: RedisChatBackend,
        registry: ClientRegistry,
        settings: ServerSettings,
    ) -> None:
        super().__init__(name=f"tcp-{addr}", daemon=True)
        self._conn = conn
        self._addr = addr
        self._core = core
        self._backend = backend
        self._registry = registry
        self._settings = settings
        self._send_lock = threading.Lock()
        self._session_id: str | None = None
        self._closed = threading.Event()
        self._sender: Any = None

    def _send_raw(self, frame: bytes) -> None:
        with self._send_lock:
            self._conn.sendall(frame)

    def _send_error(self, message: str) -> None:
        self._send_raw(encode_line({"type": MessageType.ERROR.value, "message": message}))

    def run(self) -> None:
        sender = self._send_raw
        self._sender = sender
        self._registry.add(sender)
        reader = self._conn.makefile("rb")
        try:
            logger.info("TCP conectado de %s", self._addr)
            for raw_line in reader:
                if self._closed.is_set() or not raw_line:
                    break
                try:
                    msg = decode_line(raw_line)
                except (UnicodeDecodeError, ValueError, TypeError):
                    self._send_error("frame JSON inválido")
                    continue

                typ = msg.get("type")
                if self._session_id is None:
                    if typ == MessageType.PING.value:
                        self._send_raw(encode_line({"type": MessageType.PONG.value, "ts": now_ts()}))
                        continue
                    if typ != MessageType.LOGIN.value:
                        self._send_error("envie login primeiro")
                        continue
                    result = self._core.login(str(msg.get("username", "")))
                    if isinstance(result, str):
                        self._send_error(result)
                        continue
                    self._session_id = result.session_id
                    self._send_raw(
                        encode_line(
                            {
                                "type": MessageType.WELCOME.value,
                                "session_id": result.session_id,
                                "client_id": result.client_id,
                                "username": result.username,
                                "history": result.history,
                            },
                        ),
                    )
                    continue

                if typ == MessageType.MESSAGE.value:
                    out = self._core.send_message(self._session_id, str(msg.get("text", "")))
                    if isinstance(out, str):
                        self._send_error(out)
                elif typ == MessageType.HISTORY_SINCE.value:
                    since = float(msg.get("since", 0))
                    items = self._backend.get_history_since(
                        since,
                        limit=self._settings.history_max,
                    )
                    self._send_raw(
                        encode_line({"type": MessageType.HISTORY.value, "messages": items}),
                    )
                elif typ == MessageType.PING.value:
                    self._send_raw(encode_line({"type": MessageType.PONG.value, "ts": now_ts()}))
                    self._core.refresh_session(self._session_id)
                elif typ == MessageType.LOGIN.value:
                    self._send_error("já autenticado")
                else:
                    self._send_error(f"tipo desconhecido: {typ!r}")
        except OSError as exc:
            logger.info("TCP encerrado (%s): %s", self._addr, exc)
        finally:
            self._cleanup()
            try:
                reader.close()
            except OSError:
                pass
            try:
                self._conn.close()
            except OSError:
                pass

    def _cleanup(self) -> None:
        if self._sender is not None:
            self._registry.remove(self._sender)
        if self._session_id:
            self._core.logout(self._session_id)

    def close(self) -> None:
        self._closed.set()
        try:
            self._conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
