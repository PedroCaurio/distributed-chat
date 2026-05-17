"""Logs didáticos para apresentação — ative com DEMO_LOGS=1 no .env."""

from __future__ import annotations

import inspect
import logging
import os
import threading
from typing import Any

from common.log_fmt import log_lines, short_id

_CONFIGURED = False
_PREFIX = "[DEMO]"


def enabled() -> bool:
    return os.getenv("DEMO_LOGS", "").strip().lower() in ("1", "true", "yes", "on")


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True
    if enabled():
        fmt = "%(asctime)s %(message)s"
    else:
        fmt = "%(asctime)s %(levelname)s %(name)s | %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt, force=True)


def _caller(skip: int = 3) -> str:
    stack = inspect.stack()
    if skip < len(stack):
        frame = stack[skip]
        mod = frame.frame.f_globals.get("__name__", "?")
        return f"{mod}.{frame.function}"
    return "?"


def _resolve_fn(fields: dict[str, Any], *, explicit: str | None, skip: int) -> tuple[str, dict[str, Any]]:
    extra = dict(fields)
    where = explicit or extra.pop("fn", None) or extra.pop("codigo", None) or _caller(skip)
    return where, extra


def demo(logger: logging.Logger, message: str, *, fn: str | None = None, **fields: Any) -> None:
    if not enabled():
        return
    where, extra = _resolve_fn(fields, explicit=fn, skip=3)
    thread = threading.current_thread().name
    log_lines(
        logger,
        logging.INFO,
        _PREFIX,
        message,
        lines=[f"thread: {thread}", f"código: {where}"],
        fields=extra or None,
    )


def thread_start(logger: logging.Logger, label: str, **fields: Any) -> None:
    if not enabled():
        return
    t = threading.current_thread()
    where, extra = _resolve_fn(fields, explicit=None, skip=3)
    demo(
        logger,
        f"Thread «{t.name}» — {label}",
        fn=where,
        id=t.ident,
        **extra,
    )


def tcp_frame(
    logger: logging.Logger,
    direction: str,
    msg: dict[str, Any],
    **fields: Any,
) -> None:
    if not enabled():
        return
    typ = msg.get("type", "?")
    where, extra = _resolve_fn(fields, explicit=None, skip=3)
    payload: dict[str, Any] = {"tipo": typ, "direção": direction, "código": where}
    for key in ("username", "text", "session_id"):
        if key in msg and msg[key] not in (None, ""):
            val = msg[key]
            if key == "text" and isinstance(val, str):
                val = short_id(val, keep=40)
            payload[key] = val
    payload.update(extra)
    log_lines(
        logger,
        logging.INFO,
        _PREFIX,
        "Socket TCP",
        fields=payload,
    )
