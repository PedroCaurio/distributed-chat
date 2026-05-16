"""Afinidade de sessão no Fly.io: rotas HTTP devem ir à VM que detém o TCP local."""

from __future__ import annotations

import os
from typing import Final

import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

COOKIE_NAME: Final[str] = "fly_machine_id"
AFFINITY_PREFIX: Final[str] = "proxy:affinity:"
AFFINITY_TTL_SECONDS: Final[int] = 86_400


def local_machine_id() -> str | None:
    mid = os.getenv("FLY_MACHINE_ID", "").strip()
    return mid or None


class AffinityStore:
    """Mapeia ``session_id`` do proxy → ID da máquina Fly (estado compartilhado)."""

    __slots__ = ("_client",)

    def __init__(self, redis_url: str) -> None:
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def bind(self, session_id: str, machine_id: str) -> None:
        self._client.setex(f"{AFFINITY_PREFIX}{session_id}", AFFINITY_TTL_SECONDS, machine_id)

    def resolve(self, session_id: str) -> str | None:
        value = self._client.get(f"{AFFINITY_PREFIX}{session_id}")
        return value if value else None


def _session_id_from_request(request: Request) -> str | None:
    header = request.headers.get("x-session-id", "").strip()
    if header:
        return header
    query = request.query_params.get("session", "").strip()
    return query or None


def _target_machine(request: Request, store: AffinityStore | None) -> str | None:
    cookie = request.cookies.get(COOKIE_NAME, "").strip()
    if cookie:
        return cookie
    if store is None:
        return None
    sid = _session_id_from_request(request)
    if sid:
        return store.resolve(sid)
    return None


class FlyAffinityMiddleware(BaseHTTPMiddleware):
    """
    Se a requisição pertence a outra VM, responde com ``fly-replay`` para reencaminhar.

    Necessário porque cada VM mantém conexões TCP do proxy em memória local.
    """

    def __init__(self, app, store: AffinityStore | None) -> None:
        super().__init__(app)
        self._store = store
        self._local = local_machine_id()

    async def dispatch(self, request: Request, call_next):
        if self._local and request.url.path not in {"/health"}:
            target = _target_machine(request, self._store)
            if target and target != self._local:
                return Response(
                    content="",
                    status_code=307,
                    headers={"fly-replay": f"instance={target}"},
                )
        return await call_next(request)


def affinity_cookie_value() -> str | None:
    return local_machine_id()


def set_affinity_cookie(response: Response, session_id: str, store: AffinityStore | None) -> None:
    """Grava cookie + Redis para pinar o navegador nesta VM."""
    machine = local_machine_id()
    if not machine:
        return
    response.set_cookie(
        key=COOKIE_NAME,
        value=machine,
        max_age=AFFINITY_TTL_SECONDS,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    if store is not None:
        store.bind(session_id, machine)
