"""Configuração do cliente (proxy HTTP + TCP para o servidor)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class ProxySettings:
    """Parâmetros do processo cliente."""

    redis_url: str | None
    server_host: str
    server_port: int
    http_host: str
    http_port: int
    cors_origins: tuple[str, ...]
    login_timeout_s: float
    rpc_timeout_s: float


def _parse_cors(raw: str) -> tuple[str, ...]:
    return tuple(p.strip() for p in raw.split(",") if p.strip())


def load_settings() -> ProxySettings:
    """
    Variáveis de ambiente:

    CHAT_SERVER_HOST (default 127.0.0.1)
    CHAT_SERVER_PORT (default 9000)
    PROXY_HTTP_HOST (default 0.0.0.0)
    PORT ou PROXY_HTTP_PORT (default 8080)
    PROXY_CORS_ORIGINS (opcional, separado por vírgulas)
    """
    server_host = os.getenv("CHAT_SERVER_HOST", "127.0.0.1").strip()
    server_port = int(os.getenv("CHAT_SERVER_PORT", "9000"))
    http_host = os.getenv("PROXY_HTTP_HOST", "0.0.0.0").strip()
    http_port = int(os.getenv("PORT", os.getenv("PROXY_HTTP_PORT", "8080")))
    cors_raw = os.getenv("PROXY_CORS_ORIGINS", "").strip()
    cors = _parse_cors(cors_raw) if cors_raw else ()
    login_timeout = float(os.getenv("PROXY_LOGIN_TIMEOUT", "15"))
    rpc_timeout = float(os.getenv("PROXY_RPC_TIMEOUT", "10"))
    redis_url = os.getenv("REDIS_URL", "").strip() or None
    return ProxySettings(
        redis_url=redis_url,
        server_host=server_host,
        server_port=server_port,
        http_host=http_host,
        http_port=http_port,
        cors_origins=cors,
        login_timeout_s=login_timeout,
        rpc_timeout_s=rpc_timeout,
    )
