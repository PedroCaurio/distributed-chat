"""
Protocolo de aplicação: mensagens JSON delimitadas por newline (NDJSON sobre TCP).

Cada *frame* é uma linha UTF-8 terminada em ``\\n`` contendo um único objeto JSON.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Final


NEWLINE: Final[bytes] = b"\n"


class MessageType(str, Enum):
    """Tipos lógicos trocados no socket (campo ``type`` do JSON)."""

    LOGIN = "login"
    MESSAGE = "message"
    WELCOME = "welcome"
    CHAT = "chat"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    ERROR = "error"
    HISTORY = "history"
    HISTORY_SINCE = "history_since"
    PING = "ping"
    PONG = "pong"


def encode_line(payload: dict[str, Any]) -> bytes:
    """Serializa um dict como uma linha NDJSON (inclui o newline final)."""
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return raw.encode("utf-8") + NEWLINE


def decode_line(line: bytes) -> dict[str, Any]:
    """
    Desserializa uma linha NDJSON.

    Raises:
        UnicodeDecodeError: conteúdo não é UTF-8 válido.
        json.JSONDecodeError: linha não é JSON válido.
    """
    stripped = line.rstrip(NEWLINE)
    if not stripped:
        return {}
    return json.loads(stripped.decode("utf-8"))
