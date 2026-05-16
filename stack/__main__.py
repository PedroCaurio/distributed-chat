"""
Ponto de entrada de produção: servidor TCP + cliente HTTP no mesmo container.

Fly.io expõe a porta HTTP do cliente (8080); o servidor TCP escuta em 9000 local.
"""

from __future__ import annotations

import logging
import time

from server.main import _configure_logging, start_server


def main() -> None:
    _configure_logging()
    logging.getLogger(__name__).info("Iniciando stack servidor TCP + cliente HTTP...")
    start_server()
    time.sleep(0.3)
    from client.main import run

    run()


if __name__ == "__main__":
    main()
