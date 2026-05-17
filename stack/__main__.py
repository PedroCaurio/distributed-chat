"""
Produção (Fly/Docker): servidor TCP + cliente HTTP no mesmo processo.

HTTP :8080 (navegador) · TCP :9000 (chat, apenas dentro do container).
Para testar no PC use LOCAL_run.ps1.
"""

from __future__ import annotations

import logging
import time

from common.demo_log import configure_logging
from server.main import start_server


def main() -> None:
    configure_logging()
    logging.getLogger(__name__).info("Iniciando stack servidor TCP + cliente HTTP...")
    start_server()
    time.sleep(0.3)
    from client.main import run

    run()


if __name__ == "__main__":
    main()
