"""
protocol.py — Protocolo NDJSON sobre TCP
=========================================
Serializa mensagens do chat como uma linha JSON UTF-8 terminada em \\n.
Usado entre proxy.py (cliente TCP) e server.py (servidor).

Tipos principais:
  Proxy → Servidor: login, message, ping, logout, history_since
  Servidor → Proxy: welcome, chat, user_joined, user_left, error, pong, history
"""

from __future__ import annotations

import json

NEWLINE = b"\n"


def encode(payload: dict) -> bytes:
    """
    Serializa um dicionário como frame NDJSON (inclui o \\n final).

    Args:
        payload: Campos do frame (ex.: type, username, text).

    Returns:
        Bytes prontos para sendall no socket.
    """
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode() + NEWLINE


def decode(line: bytes) -> dict:
    """
    Desserializa uma linha NDJSON recebida do socket.

    Args:
        line: Uma linha sem o \\n ou com ele.

    Returns:
        Objeto dict; {} se a linha estiver vazia.
    """
    stripped = line.rstrip(NEWLINE)
    if not stripped:
        return {}
    return json.loads(stripped.decode("utf-8"))
