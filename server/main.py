"""
Ponto de entrada do servidor de chat.

Aceita conexões TCP, cria uma thread por cliente e inicia um listener Redis pub/sub
para replicar eventos entre instâncias (tolerância a falhas / horizontal scale).
"""

from __future__ import annotations

import logging
import signal
import socket
import threading
from typing import Any

from common.protocol import MessageType, encode_line

from server.config import ServerSettings, load_settings
from server.redis_service import RedisChatBackend, start_pubsub_listener
from server.registry import ClientRegistry
from server.session import ClientSession

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _make_pubsub_handler(registry: ClientRegistry):
    """Encapsula broadcast local a partir de payloads vindos do Redis."""

    def _handler(payload: dict[str, Any]) -> None:
        typ = payload.get("type")
        if typ in {
            MessageType.CHAT.value,
            MessageType.USER_JOINED.value,
            MessageType.USER_LEFT.value,
        }:
            registry.broadcast_bytes(encode_line(payload))

    return _handler


def serve(settings: ServerSettings) -> None:
    backend = RedisChatBackend(
        settings.redis_url,
        history_max=settings.history_max,
    )
    backend.ping()

    registry = ClientRegistry()
    stop_event = threading.Event()
    start_pubsub_listener(
        settings.redis_url,
        settings.pubsub_channel,
        _make_pubsub_handler(registry),
        stop_event=stop_event,
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((settings.host, settings.port))
    sock.listen(128)
    logger.info("Servidor escutando em %s:%s", settings.host, settings.port)

    def _stop(*_: Any) -> None:
        logger.info("Sinal de encerramento recebido")
        stop_event.set()
        try:
            sock.close()
        except OSError:
            pass

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    try:
        while True:
            try:
                conn, addr = sock.accept()
            except OSError:
                break
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            ClientSession(
                conn,
                addr,
                backend=backend,
                registry=registry,
                settings=settings,
            ).start()
    finally:
        stop_event.set()
        try:
            sock.close()
        except OSError:
            pass


def main() -> None:
    _configure_logging()
    settings = load_settings()
    serve(settings)


if __name__ == "__main__":
    main()
