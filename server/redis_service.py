"""Integração com Redis: histórico, presença e pub/sub."""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from typing import Any, Final

import redis

logger = logging.getLogger(__name__)

HISTORY_KEY: Final[str] = "chat:history"
PRESENCE_KEY: Final[str] = "chat:online"


class RedisChatBackend:
    """Operações de estado compartilhado entre instâncias do servidor."""

    __slots__ = ("_client", "_history_max")

    def __init__(self, url: str, *, history_max: int) -> None:
        self._client: redis.Redis = redis.Redis.from_url(url, decode_responses=True)
        self._history_max = history_max

    def ping(self) -> None:
        self._client.ping()

    def try_register_presence(self, username: str) -> bool:
        """Retorna False se o usuário já estiver marcado como online."""
        added = int(self._client.sadd(PRESENCE_KEY, username))
        return added == 1

    def release_presence(self, username: str) -> None:
        self._client.srem(PRESENCE_KEY, username)

    def append_history(self, entry: dict[str, Any]) -> None:
        payload = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
        pipe = self._client.pipeline()
        pipe.lpush(HISTORY_KEY, payload)
        pipe.ltrim(HISTORY_KEY, 0, self._history_max - 1)
        pipe.execute()

    def get_history(self, *, limit: int) -> list[dict[str, Any]]:
        raw_items = self._client.lrange(HISTORY_KEY, 0, limit - 1)
        out: list[dict[str, Any]] = []
        for raw in reversed(raw_items):
            try:
                out.append(json.loads(raw))
            except json.JSONDecodeError:
                logger.warning("Item de histórico inválido no Redis; ignorando.")
        return out

    def publish(self, channel: str, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        self._client.publish(channel, body)


def start_pubsub_listener(
    url: str,
    channel: str,
    on_message: Callable[[dict[str, Any]], None],
    *,
    stop_event: threading.Event,
) -> threading.Thread:
    """
    Thread que escuta pub/sub e chama ``on_message`` com dict já parseado.

    Usa conexão dedicada (requisito do cliente Redis).
    """

    def _run() -> None:
        client = redis.Redis.from_url(url, decode_responses=True)
        pubsub = client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(channel)
        try:
            for msg in pubsub.listen():
                if stop_event.is_set():
                    break
                if not isinstance(msg, dict):
                    continue
                if msg.get("type") != "message":
                    continue
                data = msg.get("data")
                if not isinstance(data, str):
                    continue
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning("Payload pub/sub inválido; ignorando.")
                    continue
                if isinstance(payload, dict):
                    on_message(payload)
        finally:
            try:
                pubsub.close()
            finally:
                client.close()

    thread = threading.Thread(target=_run, name="redis-pubsub", daemon=True)
    thread.start()
    return thread
