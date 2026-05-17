"""Rastreamento e bloqueio de loop SSE/sessão inválida."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from typing import Any

from common.demo_log import enabled
from common.log_fmt import log_lines, short_id

logger = logging.getLogger("trace.loop")

_PREFIX = "[TRACE]"
_hits: dict[str, list[float]] = defaultdict(list)
_blocked_until: dict[str, float] = {}

_BLOCK_AFTER_HITS = 4
_BLOCK_SECONDS = 300.0
_HIT_WINDOW_S = 30.0


def _prune(session_id: str) -> list[float]:
    now = time.time()
    kept = [t for t in _hits[session_id] if now - t <= _HIT_WINDOW_S]
    _hits[session_id] = kept
    return kept


def is_session_blocked(session_id: str) -> bool:
    sid = session_id.strip()
    if not sid:
        return False
    until = _blocked_until.get(sid)
    if until is None:
        return False
    if time.time() > until:
        _blocked_until.pop(sid, None)
        _hits.pop(sid, None)
        return False
    return True


def record_invalid_session(session_id: str) -> bool:
    sid = session_id.strip()
    if not sid or sid == "?":
        return False
    hits = _prune(sid)
    hits.append(time.time())
    _hits[sid] = hits
    if len(hits) >= _BLOCK_AFTER_HITS:
        _blocked_until[sid] = time.time() + _BLOCK_SECONDS
        return True
    return False


def _hint(trace_tab: str, hit_count: int, blocked: bool) -> str | None:
    if trace_tab in ("", "-"):
        return "Provável JS em cache — feche abas e use Ctrl+Shift+R"
    if blocked:
        return "Sessão bloqueada 5 min — pare de pollar e faça login de novo"
    if hit_count >= _BLOCK_AFTER_HITS:
        return "Muitas tentativas com a mesma sessão inválida"
    return None


def trace_loop(
    event: str,
    *,
    path: str,
    session_id: str | None = None,
    status: int | None = None,
    **fields: Any,
) -> None:
    if not enabled():
        return

    req_id = str(fields.pop("req_id", uuid.uuid4().hex[:8]))
    sid = (session_id or "").strip() or "(sem sessão)"
    hit_count = len(_prune(sid)) if sid != "(sem sessão)" else 0
    blocked = is_session_blocked(sid) if sid != "(sem sessão)" else False
    trace_tab = str(fields.pop("trace_tab", "-"))

    status_txt = str(status) if status is not None else "?"
    headline = f"{event} — {path} → {status_txt}"

    summary = [
        f"sessão: {short_id(sid, keep=12)}",
        f"req: {req_id}",
        f"tentativas({_HIT_WINDOW_S:.0f}s): {hit_count}",
    ]
    if blocked:
        summary.append("bloqueada")

    vm_fields: dict[str, Any] = {}
    for key in ("local_vm", "cookie_vm", "redis_vm"):
        if key in fields:
            vm_fields[key.replace("_", " ")] = short_id(str(fields.pop(key)), keep=12)
    sess_fields: dict[str, Any] = {}
    for key in (
        "session_na_vm",
        "ativas",
        "conhecidas",
        "header_session",
        "query_session",
        "fly_force",
    ):
        if key in fields:
            val = fields.pop(key)
            if key == "header_session":
                val = short_id(str(val), keep=12)
            sess_fields[key.replace("_", " ")] = val
    if trace_tab != "-":
        sess_fields["aba navegador"] = trace_tab

    extra_lines: list[str] = [summary[0] + " | " + " | ".join(summary[1:])]
    hint = _hint(trace_tab, hit_count, blocked)
    if hint:
        extra_lines.append(f"→ {hint}")

    level = logging.WARNING if hit_count >= _BLOCK_AFTER_HITS or status in {401, 410} else logging.INFO

    log_lines(
        logger,
        level,
        _PREFIX,
        headline,
        lines=extra_lines,
        fields={**vm_fields, **sess_fields, **fields} or None,
    )
