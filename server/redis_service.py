"""Integração com Redis: histórico, sessões web e pub/sub."""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from typing import Any, Final

import redis

logger = logging.getLogger(__name__)

HISTORY_KEY: Final[str] = "chat:history"
SESSION_PREFIX: Final[str] = "chat:session:"
USER_PREFIX: Final[str] = "chat:user:"
SESSION_TTL_SECONDS: Final[int] = 300


class RedisChatBackend:
    """Operações de estado compartilhado entre instâncias do servidor."""

    __slots__ = ("_client", "_history_max")

    def __init__(self, url: str, *, history_max: int) -> None:
        self._client: redis.Redis = redis.Redis.from_url(url, decode_responses=True)
        self._history_max = history_max

    def ping(self) -> None:
        self._client.ping()

    def save_session(self, session_id: str, username: str) -> None:
        self._client.setex(f"{SESSION_PREFIX}{session_id}", SESSION_TTL_SECONDS, username)

    def get_session_username(self, session_id: str) -> str | None:
        value = self._client.get(f"{SESSION_PREFIX}{session_id}")
        return value if value else None

    def refresh_session(self, session_id: str) -> bool:
        key = f"{SESSION_PREFIX}{session_id}"
        if not self._client.exists(key):
            return False
        self._client.expire(key, SESSION_TTL_SECONDS)
        username = self._client.get(key)
        if username:
            self._client.expire(f"{USER_PREFIX}{username}", SESSION_TTL_SECONDS)
        return True

    def pop_session(self, session_id: str) -> str | None:
        key = f"{SESSION_PREFIX}{session_id}"
        username = self._client.get(key)
        if not username:
            return None
        pipe = self._client.pipeline()
        pipe.delete(key)
        pipe.delete(f"{USER_PREFIX}{username}")
        pipe.execute()
        return username

    def claim_username(self, username: str, session_id: str) -> bool:
        """
        Reserva username para a sessão.

        Permite reconexão da mesma sessão ou tomada de posse se a sessão anterior expirou.
        """
        user_key = f"{USER_PREFIX}{username}"
        existing = self._client.get(user_key)
        if existing is None:
            pipe = self._client.pipeline()
            pipe.setex(user_key, SESSION_TTL_SECONDS, session_id)
            pipe.setex(f"{SESSION_PREFIX}{session_id}", SESSION_TTL_SECONDS, username)
            pipe.execute()
            return True
        if existing == session_id:
            self.refresh_session(session_id)
            return True
        if not self._client.exists(f"{SESSION_PREFIX}{existing}"):
            pipe = self._client.pipeline()
            pipe.delete(f"{SESSION_PREFIX}{existing}")
            pipe.setex(user_key, SESSION_TTL_SECONDS, session_id)
            pipe.setex(f"{SESSION_PREFIX}{session_id}", SESSION_TTL_SECONDS, username)
            pipe.execute()
            return True
        return False

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

    def get_history_since(self, since_ts: float, *, limit: int = 200) -> list[dict[str, Any]]:
        """Mensagens de chat com ``ts`` estritamente maior que ``since_ts``."""
        all_items = self.get_history(limit=limit)
        return [m for m in all_items if float(m.get("ts", 0)) > since_ts]

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
    """Thread dedicada que escuta pub/sub Redis (replicação entre instâncias)."""

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
