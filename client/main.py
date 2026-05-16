"""Inicia o servidor HTTP embutido do cliente (proxy para o navegador)."""

from __future__ import annotations

import logging

import uvicorn

from client.app import create_app
from client.config import load_settings


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def run() -> None:
    settings = load_settings()
    app = create_app(settings)
    logging.getLogger(__name__).info(
        "Cliente HTTP em %s:%s → TCP %s:%s",
        settings.http_host,
        settings.http_port,
        settings.server_host,
        settings.server_port,
    )
    uvicorn.run(app, host=settings.http_host, port=settings.http_port, log_level="info")


def main() -> None:
    _configure_logging()
    run()


if __name__ == "__main__":
    main()
