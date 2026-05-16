"""Estado compartilhado do processo servidor (TCP + Redis pub/sub)."""

from __future__ import annotations

import threading

from server.chat_core import ChatCore
from server.config import ServerSettings
from server.redis_service import RedisChatBackend
from server.registry import ClientRegistry


class ServerState:
    """Dependências do servidor de chat (sem HTTP público)."""

    __slots__ = ("settings", "backend", "core", "tcp_registry", "stop_event")

    def __init__(self, settings: ServerSettings) -> None:
        self.settings = settings
        self.backend = RedisChatBackend(settings.redis_url, history_max=settings.history_max)
        self.core = ChatCore(self.backend, settings)
        self.tcp_registry = ClientRegistry()
        self.stop_event = threading.Event()
