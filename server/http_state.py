"""Estado compartilhado entre rotas HTTP, pub/sub e TCP."""

from __future__ import annotations

import threading

from server.chat_core import ChatCore
from server.config import ServerSettings
from server.redis_service import RedisChatBackend
from server.registry import ClientRegistry
from server.sse_hub import SseHub


class AppState:
    """Container de dependências do processo servidor."""

    __slots__ = ("settings", "backend", "core", "tcp_registry", "sse_hub", "stop_event")

    def __init__(self, settings: ServerSettings) -> None:
        self.settings = settings
        self.backend = RedisChatBackend(settings.redis_url, history_max=settings.history_max)
        self.core = ChatCore(self.backend, settings)
        self.tcp_registry = ClientRegistry()
        self.sse_hub = SseHub()
        self.stop_event = threading.Event()
