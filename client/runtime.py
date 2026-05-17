"""Proxy multiusuário: uma conexão TCP (e thread recv) por sessão de navegador."""

from __future__ import annotations

import logging
import queue
import threading
import uuid
from typing import Any

from common.demo_log import demo
from common.protocol import MessageType

from client.config import ProxySettings
from client.inbound import InboundDemux
from client.socket_bridge import SocketBridge
from client.user_session import UserSession

logger = logging.getLogger(__name__)


class ProxyRuntime:
    """
    Gerencia várias sessões simultâneas.

    Cada login abre socket TCP próprio e inicia thread ``socket-recv-<user>``.
    """

    __slots__ = ("_settings", "_lock", "_sessions")

    def __init__(self, settings: ProxySettings) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._sessions: dict[str, UserSession] = {}

    def close_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for sess in sessions:
            sess.bridge.close()

    @property
    def active_session_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def get_session(self, proxy_session_id: str) -> UserSession | None:
        with self._lock:
            return self._sessions.get(proxy_session_id)

    def sessions_debug(self) -> list[str]:
        """Resumo das sessões na memória desta VM (para [TRACE-LOOP])."""
        with self._lock:
            return [
                f"{sid[:8]}…({sess.username})"
                for sid, sess in self._sessions.items()
            ]

    def login(self, username: str) -> dict[str, Any]:
        demo(
            logger,
            "ProxyRuntime.login — abre socket TCP + thread recv para o navegador",
            fn="client.runtime.ProxyRuntime.login",
            username=username,
        )
        proxy_sid = uuid.uuid4().hex
        demux = InboundDemux()
        bridge = SocketBridge(
            self._settings.server_host,
            self._settings.server_port,
            demux,
            username=username,
        )
        bridge.connect()

        demux.arm_rpc("login")
        try:
            bridge.send_login(username)
            resp = demux.wait_rpc("login", timeout_s=self._settings.login_timeout_s)
        finally:
            demux.disarm_rpc()

        if resp.get("type") == MessageType.ERROR.value:
            bridge.close()
            return resp

        if resp.get("type") != MessageType.WELCOME.value:
            bridge.close()
            msg = f"Resposta inesperada no login: {resp.get('type')!r}"
            raise RuntimeError(msg)

        uname = str(resp.get("username", username))
        server_sid = str(resp.get("session_id", proxy_sid))
        sess = UserSession(
            proxy_session_id=proxy_sid,
            username=uname,
            server_session_id=server_sid,
            demux=demux,
            bridge=bridge,
        )
        with self._lock:
            self._sessions[proxy_sid] = sess

        return {
            "type": MessageType.WELCOME.value,
            "session_id": proxy_sid,
            "client_id": resp.get("client_id", server_sid),
            "username": uname,
            "history": resp.get("history", []),
        }

    def logout(self, proxy_session_id: str) -> None:
        sess = self._pop_session(proxy_session_id)
        if sess:
            sess.bridge.close()

    def send_chat(self, proxy_session_id: str, text: str) -> None:
        demo(
            logger,
            "ProxyRuntime.send_chat — HTTP já recebeu; agora envia no TCP",
            fn="client.runtime.ProxyRuntime.send_chat",
            text=text,
        )
        sess = self._require_session(proxy_session_id)
        if sess.bridge.is_closed():
            msg = "Conexão TCP encerrada; faça login novamente"
            raise RuntimeError(msg)
        sess.bridge.send_message(text)

    def heartbeat(self, proxy_session_id: str) -> bool:
        sess = self.get_session(proxy_session_id)
        if sess is None or sess.bridge.is_closed():
            return False
        sess.bridge.send_ping()
        return True

    def fetch_history_since(self, proxy_session_id: str, since: float) -> list[dict[str, Any]]:
        sess = self._require_session(proxy_session_id)
        if sess.bridge.is_closed():
            return []
        demux = sess.demux
        demux.arm_rpc("history")
        try:
            sess.bridge.send_history_since(since)
            resp = demux.wait_rpc("history", timeout_s=self._settings.rpc_timeout_s)
        except TimeoutError:
            return []
        finally:
            demux.disarm_rpc()
        if resp.get("type") != MessageType.HISTORY.value:
            return []
        messages = resp.get("messages")
        return messages if isinstance(messages, list) else []

    def subscribe_sse(self, proxy_session_id: str) -> queue.Queue[dict[str, Any]]:
        sess = self._require_session(proxy_session_id)
        return sess.demux.subscribe()

    def unsubscribe_sse(
        self,
        proxy_session_id: str,
        event_queue: queue.Queue[dict[str, Any]],
    ) -> None:
        sess = self.get_session(proxy_session_id)
        if sess is not None:
            sess.demux.unsubscribe(event_queue)

    def _require_session(self, proxy_session_id: str) -> UserSession:
        sess = self.get_session(proxy_session_id)
        if sess is None:
            msg = "sessão inválida ou expirada"
            raise RuntimeError(msg)
        return sess

    def _pop_session(self, proxy_session_id: str) -> UserSession | None:
        with self._lock:
            return self._sessions.pop(proxy_session_id, None)
