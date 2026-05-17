"""Rejeita sessões inválidas e interrompe loop de polling do cliente."""

from __future__ import annotations

from fastapi import HTTPException
from starlette.requests import Request

from client.affinity import AffinityStore
from client.request_trace import trace_session_http
from client.runtime import ProxyRuntime
from common.trace_log import is_session_blocked, record_invalid_session


def reject_unknown_session(
    request: Request,
    runtime: ProxyRuntime,
    *,
    label: str,
    session_id: str,
    affinity_store: AffinityStore | None,
) -> None:
    """401 na primeira falha; 410 após várias (para o cliente antigo parar)."""
    sid = session_id.strip()
    if is_session_blocked(sid):
        trace_session_http(
            request,
            runtime,
            label=label,
            session_id=sid,
            affinity_store=affinity_store,
            status=410,
            reason="sessao_bloqueada_loop",
        )
        raise HTTPException(
            status_code=410,
            detail="sessão expirada; pare de reconectar e faça login novamente",
            headers={"Retry-After": "300", "X-Session-Gone": "1"},
        )

    if runtime.get_session(sid) is not None:
        return

    newly_blocked = record_invalid_session(sid)
    trace_session_http(
        request,
        runtime,
        label=label,
        session_id=sid,
        affinity_store=affinity_store,
        status=401,
        reason="sessao_ausente_nesta_vm" + (";bloqueio_ativado" if newly_blocked else ""),
    )
    raise HTTPException(status_code=401, detail="sessão inválida")
