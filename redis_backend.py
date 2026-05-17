"""
redis_backend.py — Estado compartilhado no Redis (Upstash)
=========================================================
Sessões de usuário, histórico de mensagens, client_id do navegador,
heartbeat de VMs Fly e canal pub/sub para broadcast entre instâncias.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Callable

import redis

log = logging.getLogger(__name__)

HISTORY_KEY = "chat:history"
SESSION_PREFIX = "chat:session:"
USER_PREFIX = "chat:user:"
CLIENT_PREFIX = "chat:client:"
MACHINE_PREFIX = "fly:machine:"
SESSION_TTL = 300
HISTORY_MAX = 100
PUBSUB_CHANNEL = "chat:events"
MACHINE_TTL = 45


class RedisBackend:
    """Acesso thread-safe ao Redis para o servidor e o proxy."""

    def __init__(self, url: str, client: redis.Redis | None = None) -> None:
        """
        Args:
            url: REDIS_URL (redis:// ou rediss://).
            client: Cliente injetado (testes com fakeredis).
        """
        self._url = url
        self._r = client if client is not None else redis.Redis.from_url(url, decode_responses=True)

    def ping(self) -> None:
        """Verifica conectividade na subida do servidor."""
        self._r.ping()

    # ── Sessões ───────────────────────────────────────────────────────────────

    def claim_username(self, username: str, session_id: str) -> bool:
        """Reserva apelido para uma sessão TCP; False se já em uso."""
        user_key = f"{USER_PREFIX}{username}"
        existing = self._r.get(user_key)

        if existing is None:
            self._bind_session(username, session_id)
            return True

        if existing == session_id:
            self.refresh_session(session_id)
            return True

        if not self._r.exists(f"{SESSION_PREFIX}{existing}"):
            self.drop_session_keys(existing)
            self._bind_session(username, session_id)
            return True

        return False

    def _bind_session(self, username: str, session_id: str) -> None:
        """Grava pares username ↔ session_id com TTL."""
        pipe = self._r.pipeline()
        pipe.setex(f"{USER_PREFIX}{username}", SESSION_TTL, session_id)
        pipe.setex(f"{SESSION_PREFIX}{session_id}", SESSION_TTL, username)
        pipe.execute()

    def get_username(self, session_id: str) -> str | None:
        """Retorna apelido vinculado à sessão TCP, ou None."""
        return self._r.get(f"{SESSION_PREFIX}{session_id}")

    def refresh_session(self, session_id: str) -> bool:
        """Renova TTL da sessão e do apelido (heartbeat)."""
        key = f"{SESSION_PREFIX}{session_id}"
        username = self._r.get(key)
        if not username:
            return False
        self._r.expire(key, SESSION_TTL)
        self._r.expire(f"{USER_PREFIX}{username}", SESSION_TTL)
        client_id = self._r.get(f"{SESSION_PREFIX}{session_id}:client")
        if client_id:
            self._r.expire(f"{CLIENT_PREFIX}{client_id}", SESSION_TTL)
        return True

    def remove_session(self, session_id: str) -> str | None:
        """Remove sessão e retorna o username desconectado, se houver."""
        return self.drop_session_keys(session_id)

    def drop_session_keys(self, session_id: str) -> str | None:
        """Remove sessão TCP, username e vínculo do navegador (client_id)."""
        key = f"{SESSION_PREFIX}{session_id}"
        username = self._r.get(key)
        client_id = self._r.get(f"{SESSION_PREFIX}{session_id}:client")
        pipe = self._r.pipeline()
        pipe.delete(key)
        pipe.delete(f"{SESSION_PREFIX}{session_id}:client")
        if username:
            pipe.delete(f"{USER_PREFIX}{username}")
        if client_id:
            pipe.delete(f"{CLIENT_PREFIX}{client_id}")
        pipe.execute()
        return username

    def get_online_users(self) -> list[str]:
        """Lista apelidos com sessão ativa no Redis."""
        keys = self._r.keys(f"{USER_PREFIX}*")
        return sorted(k.removeprefix(USER_PREFIX) for k in keys)

    # ── Cliente estável (navegador) ─────────────────────────────────────────────

    def bind_client(self, client_id: str, session_id: str, username: str) -> None:
        """Associa identificador estável do navegador à sessão TCP."""
        payload = json.dumps(
            {"session_id": session_id, "username": username},
            ensure_ascii=False,
        )
        pipe = self._r.pipeline()
        pipe.setex(f"{CLIENT_PREFIX}{client_id}", SESSION_TTL, payload)
        pipe.setex(f"{SESSION_PREFIX}{session_id}:client", SESSION_TTL, client_id)
        pipe.execute()

    def get_client(self, client_id: str) -> dict[str, str] | None:
        """Lê vínculo client_id → session_id/username."""
        raw = self._r.get(f"{CLIENT_PREFIX}{client_id}")
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if isinstance(data, dict) and data.get("session_id") and data.get("username"):
            return {
                "session_id": str(data["session_id"]),
                "username": str(data["username"]),
            }
        return None

    def reclaim_for_client(
        self,
        client_id: str,
        username: str,
        new_session_id: str,
    ) -> bool:
        """
        Libera vínculos antigos deste client_id e registra nova sessão TCP.
        Permite trocar de apelido no mesmo navegador (reload).
        """
        info = self.get_client(client_id)
        if info:
            self.drop_session_keys(info["session_id"])

        existing_sid = self._r.get(f"{USER_PREFIX}{username}")
        if existing_sid and existing_sid != new_session_id:
            other_client = self._r.get(f"{SESSION_PREFIX}{existing_sid}:client")
            if self._r.exists(f"{SESSION_PREFIX}{existing_sid}"):
                if other_client and other_client != client_id:
                    return False
            self.drop_session_keys(existing_sid)

        if not self.claim_username(username, new_session_id):
            return False
        self.bind_client(client_id, new_session_id, username)
        return True

    # ── Histórico ─────────────────────────────────────────────────────────────

    def append_history(self, entry: dict) -> None:
        """Insere mensagem no topo da lista circular de histórico."""
        pipe = self._r.pipeline()
        pipe.lpush(HISTORY_KEY, json.dumps(entry, ensure_ascii=False))
        pipe.ltrim(HISTORY_KEY, 0, HISTORY_MAX - 1)
        pipe.execute()

    def get_history(self) -> list[dict]:
        """Retorna até HISTORY_MAX mensagens em ordem cronológica."""
        return self._parse_history(self._r.lrange(HISTORY_KEY, 0, HISTORY_MAX - 1))

    def get_history_since(self, since: float) -> list[dict]:
        """Filtra mensagens com ts > since (recuperação após failover)."""
        items = self.get_history()
        if since <= 0:
            return items
        return [m for m in items if float(m.get("ts", 0)) > since]

    def _parse_history(self, raw: list[str]) -> list[dict]:
        """Converte strings JSON da lista Redis em dicts."""
        result: list[dict] = []
        for item in reversed(raw):
            try:
                result.append(json.loads(item))
            except json.JSONDecodeError:
                pass
        return result

    # ── VMs Fly (heartbeat) ───────────────────────────────────────────────────

    def touch_machine(self, machine_id: str) -> None:
        """Atualiza heartbeat da VM Fly para detecção de falha."""
        self._r.setex(f"{MACHINE_PREFIX}{machine_id}", MACHINE_TTL, "1")

    def is_machine_alive(self, machine_id: str) -> bool:
        """True se a VM enviou heartbeat recentemente."""
        return bool(self._r.exists(f"{MACHINE_PREFIX}{machine_id}"))

    # ── Pub/Sub ───────────────────────────────────────────────────────────────

    def publish(self, payload: dict) -> None:
        """Publica evento no canal chat:events (outras VMs)."""
        self._r.publish(PUBSUB_CHANNEL, json.dumps(payload, ensure_ascii=False))

    def start_subscriber(
        self,
        on_message: Callable[[dict], None],
        stop_event: threading.Event,
    ) -> threading.Thread:
        """
        Inicia thread daemon que escuta pub/sub e chama on_message(payload).

        Returns:
            Thread já iniciada.
        """
        url = self._url

        def _run() -> None:
            client = redis.Redis.from_url(url, decode_responses=True)
            pubsub = client.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(PUBSUB_CHANNEL)
            log.info("[Redis] Inscrito no canal %s", PUBSUB_CHANNEL)
            try:
                for msg in pubsub.listen():
                    if stop_event.is_set():
                        break
                    if not isinstance(msg, dict) or msg.get("type") != "message":
                        continue
                    data = msg.get("data")
                    if not isinstance(data, str):
                        continue
                    try:
                        payload = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        on_message(payload)
            finally:
                pubsub.close()
                client.close()

        t = threading.Thread(target=_run, name="redis-pubsub", daemon=True)
        t.start()
        return t
