"""Carrega configuração do servidor a partir do ambiente (.env via python-dotenv)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class ServerSettings:
    """Parâmetros de execução do processo servidor."""

    redis_url: str
    host: str
    port: int
    history_max: int
    pubsub_channel: str
    tcp_read_buffer: int


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        msg = f"Variável de ambiente obrigatória ausente ou vazia: {name}"
        raise ValueError(msg)
    return value


def load_settings() -> ServerSettings:
    """
    Lê variáveis de ambiente.

    Obrigatório:
        REDIS_URL: URL de conexão Redis (TLS ou não, conforme provedor).

    Opcionais:
        CHAT_HOST (default 0.0.0.0)
        CHAT_PORT (default 9000)
        HISTORY_MAX (default 500)
        PUBSUB_CHANNEL (default chat:broadcast)
        TCP_READ_BUFFER (default 65536)
    """
    redis_url = _require_env("REDIS_URL")
    host = os.getenv("CHAT_HOST", "0.0.0.0").strip()
    port = int(os.getenv("CHAT_PORT", "9000"))
    history_max = int(os.getenv("HISTORY_MAX", "500"))
    pubsub = os.getenv("PUBSUB_CHANNEL", "chat:broadcast").strip()
    tcp_buf = int(os.getenv("TCP_READ_BUFFER", "65536"))
    return ServerSettings(
        redis_url=redis_url,
        host=host,
        port=port,
        history_max=history_max,
        pubsub_channel=pubsub,
        tcp_read_buffer=tcp_buf,
    )
