"""Inicia o servidor HTTP embutido do cliente (proxy para o navegador)."""

from __future__ import annotations

import logging

import uvicorn

from client.app import create_app
from client.config import load_settings
from common.demo_log import configure_logging, demo, enabled as demo_enabled


def run() -> None:
    settings = load_settings()
    app = create_app(settings)
    log = logging.getLogger(__name__)
    log.info(
        "Cliente HTTP em %s:%s → TCP %s:%s",
        settings.http_host,
        settings.http_port,
        settings.server_host,
        settings.server_port,
    )
    if demo_enabled():
        demo(
            log,
            "Modo DEMO ativo no cliente/proxy — veja threads socket-recv-* abaixo",
            fn="client.main.run",
        )
    uvicorn.run(app, host=settings.http_host, port=settings.http_port, log_level="info")


def main() -> None:
    configure_logging()
    run()


if __name__ == "__main__":
    main()
