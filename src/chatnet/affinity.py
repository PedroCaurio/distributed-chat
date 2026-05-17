"""
affinity.py — Afinidade de sessão no Fly.io
============================================
Garante que requisições HTTP do mesmo usuário cheguem à VM que mantém
a conexão TCP local (proxy). Usa cookie fly_machine_id + Redis + fly-replay.
"""

from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler
from typing import TYPE_CHECKING

import redis

if TYPE_CHECKING:
    from .redis_backend import RedisBackend

COOKIE_NAME = "fly_machine_id"
AFFINITY_PREFIX = "proxy:affinity:"
AFFINITY_TTL_SECONDS = 86_400
SKIP_REPLAY = frozenset({"/health", "/ping", "/resume"})


def local_machine_id() -> str | None:
    """Retorna FLY_MACHINE_ID da VM atual, ou None em ambiente local."""
    mid = os.getenv("FLY_MACHINE_ID", "").strip()
    return mid or None


class AffinityStore:
    """Mapeia session_id do proxy → ID da máquina Fly (estado no Redis)."""

    def __init__(self, redis_url: str) -> None:
        """Conecta ao Redis usando a URL do Upstash/Fly secret."""
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def bind(self, session_id: str, machine_id: str) -> None:
        """Associa uma sessão HTTP à VM que fez o login."""
        self._client.setex(f"{AFFINITY_PREFIX}{session_id}", AFFINITY_TTL_SECONDS, machine_id)

    def resolve(self, session_id: str) -> str | None:
        """Consulta em qual VM a sessão deve ser atendida."""
        value = self._client.get(f"{AFFINITY_PREFIX}{session_id}")
        return value if value else None

    def clear(self, session_id: str) -> None:
        """Remove afinidade (ex.: após logout ou VM morta)."""
        self._client.delete(f"{AFFINITY_PREFIX}{session_id}")

    def is_machine_alive(self, machine_id: str) -> bool:
        """Verifica heartbeat recente da VM no Redis."""
        return bool(self._client.exists(f"fly:machine:{machine_id}"))


def _session_id_from_handler(handler: BaseHTTPRequestHandler) -> str | None:
    """Extrai session_id do header X-Session-Id ou da query string."""
    header = handler.headers.get("X-Session-Id", "").strip()
    if header:
        return header
    path = handler.path
    if "session=" in path:
        return path.split("session=")[-1].split("&")[0].strip()
    if "sid=" in path:
        return path.split("sid=")[-1].split("&")[0].strip()
    return None


def _target_machine(handler: BaseHTTPRequestHandler, store: AffinityStore | None) -> str | None:
    """Determina a VM destino via cookie ou Redis."""
    cookie = handler.headers.get("Cookie", "")
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith(f"{COOKIE_NAME}="):
            return part.split("=", 1)[1].strip()
    if store is None:
        return None
    sid = _session_id_from_handler(handler)
    if sid:
        return store.resolve(sid)
    return None


def maybe_replay(handler: BaseHTTPRequestHandler, store: AffinityStore | None) -> bool:
    """
    Se a requisição pertence a outra VM, responde 307 com fly-replay.

    Returns:
        True se enviou replay (handler não deve continuar); False caso contrário.
    """
    local = local_machine_id()
    path = handler.path.split("?")[0]
    if not local or path in SKIP_REPLAY:
        return False
    target = _target_machine(handler, store)
    if not target or target == local:
        return False
    if store is not None and not store.is_machine_alive(target):
        sid = _session_id_from_handler(handler)
        if sid:
            store.clear(sid)
        return False
    handler.send_response(307)
    handler.send_header("fly-replay", f"instance={target}")
    handler.end_headers()
    return True


def affinity_extra_headers(session_id: str, store: AffinityStore | None) -> list[tuple[str, str]]:
    """
    Cabeçalhos de resposta no login: Set-Cookie + bind no Redis.

    Returns:
        Lista [(header, valor)] para anexar à resposta JSON.
    """
    machine = local_machine_id()
    if not machine:
        return []
    secure = os.getenv("FLY_MACHINE_ID", "").strip() != ""
    cookie = (
        f"{COOKIE_NAME}={machine}; Max-Age={AFFINITY_TTL_SECONDS}; Path=/; "
        f"HttpOnly; SameSite=Lax"
    )
    if secure:
        cookie += "; Secure"
    if store is not None:
        store.bind(session_id, machine)
    return [("Set-Cookie", cookie)]
