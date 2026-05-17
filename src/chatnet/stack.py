"""
stack.py — Ponto de entrada em produção (Fly.io / Docker)
=========================================================
Sobe o servidor TCP e o proxy HTTP no mesmo processo do container.

  - server → porta SERVER_PORT (padrão 9000), thread por conexão TCP
  - proxy  → porta PORT (padrão 8080), HTTP para o navegador

Uso: python -m chatnet
"""

from __future__ import annotations

import threading
import time


def main() -> None:
    """Inicia o servidor TCP em thread daemon e o proxy HTTP no thread principal."""
    from . import proxy, server

    threading.Thread(target=server.main, name="tcp-server", daemon=True).start()
    time.sleep(0.5)
    proxy.main()
