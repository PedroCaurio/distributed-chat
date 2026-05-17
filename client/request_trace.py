"""Contexto HTTP para diagnosticar loop /events + /history 401."""

from __future__ import annotations

import uuid

from starlette.requests import Request

from client.affinity import COOKIE_NAME, AffinityStore, local_machine_id
from client.runtime import ProxyRuntime
from common.log_fmt import short_id
from common.trace_log import trace_loop


def trace_session_http(
    request: Request,
    runtime: ProxyRuntime,
    *,
    label: str,
    session_id: str,
    affinity_store: AffinityStore | None,
    status: int,
    reason: str,
) -> str:
    req_id = uuid.uuid4().hex[:8]
    local = local_machine_id() or "-"
    cookie_vm = request.cookies.get(COOKIE_NAME, "").strip() or "-"
    redis_vm = "-"
    if affinity_store is not None and session_id:
        redis_vm = affinity_store.resolve(session_id) or "-"

    sess = runtime.get_session(session_id)
    known = runtime.sessions_debug()
    known_txt = ", ".join(known) if known else "(nenhuma)"

    trace_loop(
        reason.replace("_", " "),
        path=label,
        session_id=session_id,
        status=status,
        req_id=req_id,
        local_vm=local,
        cookie_vm=cookie_vm,
        redis_vm=redis_vm,
        header_session=request.headers.get("x-session-id", "").strip() or "-",
        query_session=short_id(request.query_params.get("session", "") or "-", keep=12),
        fly_force=request.headers.get("fly-force-instance-id", "").strip() or "-",
        trace_tab=request.headers.get("x-trace-tab", "").strip() or "-",
        session_na_vm="sim" if sess is None else "não",
        ativas=runtime.active_session_count,
        conhecidas=known_txt,
    )
    return req_id
