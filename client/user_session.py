"""Sessão de um usuário no proxy: TCP + thread de recv + fila SSE."""

from __future__ import annotations

from dataclasses import dataclass

from client.inbound import InboundDemux
from client.socket_bridge import SocketBridge


@dataclass(slots=True)
class UserSession:
    """Uma conexão TCP autenticada exposta ao navegador via HTTP."""

    proxy_session_id: str
    username: str
    server_session_id: str
    demux: InboundDemux
    bridge: SocketBridge
