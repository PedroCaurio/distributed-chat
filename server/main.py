"""
Ponto de entrada unificado: API HTTP (100% web) + servidor TCP opcional em thread.

Deploy Fly.io: escale com ``fly scale count 2``; o load balancer HTTP distribui tráfego.
Estado e pub/sub no Redis garantem continuidade quando uma instância cai.
"""

from __future__ import annotations

import logging
import os
import signal
import socket
import threading
from typing import Any

import uvicorn

from common.protocol import MessageType, encode_line
from server.config import load_settings
from server.http_app import create_http_app
from server.http_state import AppState
from server.redis_service import start_pubsub_listener
from server.session import ClientSession

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _pubsub_handler(state: AppState):
    def _handler(payload: dict[str, Any]) -> None:
        typ = payload.get("type")
        if typ in {
            MessageType.CHAT.value,
            MessageType.USER_JOINED.value,
            MessageType.USER_LEFT.value,
        }:
            state.tcp_registry.broadcast_bytes(encode_line(payload))
            state.sse_hub.broadcast(payload)

    return _handler


def _run_tcp_server(state: AppState) -> None:
    settings = state.settings
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((settings.host, settings.port))
    sock.listen(128)
    logger.info("TCP escutando em %s:%s", settings.host, settings.port)

    while not state.stop_event.is_set():
        try:
            sock.settimeout(1.0)
            conn, addr = sock.accept()
        except TimeoutError:
            continue
        except OSError:
            break
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        ClientSession(
            conn,
            addr,
            core=state.core,
            backend=state.backend,
            registry=state.tcp_registry,
            settings=settings,
        ).start()

    try:
        sock.close()
    except OSError:
        pass


def run() -> None:
    settings = load_settings()
    state = AppState(settings)
    state.backend.ping()

    start_pubsub_listener(
        settings.redis_url,
        settings.pubsub_channel,
        _pubsub_handler(state),
        stop_event=state.stop_event,
    )

    if os.getenv("ENABLE_TCP_SERVER", "true").lower() in {"1", "true", "yes"}:
        threading.Thread(
            target=_run_tcp_server,
            args=(state,),
            name="tcp-server",
            daemon=True,
        ).start()

    http_port = int(os.getenv("PORT", os.getenv("HTTP_PORT", "10000")))
    app = create_http_app(state)

    def _stop(*_: Any) -> None:
        logger.info("Encerrando servidor...")
        state.stop_event.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    logger.info("HTTP escutando na porta %s", http_port)
    uvicorn.run(app, host="0.0.0.0", port=http_port, log_level="info")


def main() -> None:
    _configure_logging()
    run()


if __name__ == "__main__":
    main()
