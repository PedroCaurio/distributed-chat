"""Configuração do proxy (servidor de chat remoto + HTTP local)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class ProxySettings:
    """Parâmetros de execução do processo proxy."""

    server_host: str
    server_port: int
    http_host: str
    http_port: int
    cors_origins: tuple[str, ...]


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        msg = f"Variável de ambiente obrigatória ausente ou vazia: {name}"
        raise ValueError(msg)
    return value


def _parse_cors(raw: str) -> tuple[str, ...]:
    items = [p.strip() for p in raw.split(",") if p.strip()]
    return tuple(items)


def load_settings() -> ProxySettings:
    """
    Lê variáveis de ambiente.

    Obrigatório:
        CHAT_SERVER_HOST
        CHAT_SERVER_PORT

    Opcionais:
        PROXY_HTTP_HOST (default 127.0.0.1)
        PROXY_HTTP_PORT (default 5000)
        PROXY_CORS_ORIGINS (lista separada por vírgulas; vazio = sem CORS extra)
    """
    server_host = _require_env("CHAT_SERVER_HOST")
    server_port = int(_require_env("CHAT_SERVER_PORT"))
    http_host = os.getenv("PROXY_HTTP_HOST", "127.0.0.1").strip()
    http_port = int(os.getenv("PROXY_HTTP_PORT", "5000"))
    cors_raw = os.getenv("PROXY_CORS_ORIGINS", "").strip()
    cors = _parse_cors(cors_raw) if cors_raw else ()
    return ProxySettings(
        server_host=server_host,
        server_port=server_port,
        http_host=http_host,
        http_port=http_port,
        cors_origins=cors,
    )
