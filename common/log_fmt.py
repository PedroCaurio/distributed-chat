"""Formatação legível para logs DEMO / TRACE (várias linhas curtas)."""

from __future__ import annotations

import logging
from typing import Any

_INDENT = "  "


def short_id(value: str, *, keep: int = 8) -> str:
    text = (value or "").strip()
    if not text or text == "-":
        return "-"
    if len(text) <= keep + 1:
        return text
    return f"{text[:keep]}…"


def format_fields(fields: dict[str, Any], *, max_value_len: int = 48) -> list[str]:
    lines: list[str] = []
    for key, raw in fields.items():
        val = raw
        if isinstance(val, str) and len(val) > max_value_len:
            val = val[: max_value_len - 1] + "…"
        lines.append(f"{_INDENT}{key}: {val}")
    return lines


def log_lines(
    logger: logging.Logger,
    level: int,
    prefix: str,
    headline: str,
    *,
    lines: list[str] | None = None,
    fields: dict[str, Any] | None = None,
) -> None:
    """Uma entrada de log em bloco (cabeçalho + linhas indentadas)."""
    body = [f"{prefix} {headline}"]
    if lines:
        body.extend(f"{_INDENT}{line}" for line in lines)
    if fields:
        body.extend(format_fields(fields))
    logger.log(level, "\n".join(body))
