"""
Servidor de chat TCP: uma thread por conexão, fan-out via Redis pub/sub.

Replicação: duas instâncias Fly compartilham Redis; se uma VM cai, a outra
continua atendendo novas conexões TCP dos clientes (proxy).
"""

from __future__ import annotations

import logging
import signal
import socket
import threading
from typing import Any

from common.demo_log import configure_logging, demo, enabled as demo_enabled
from common.protocol import MessageType, encode_line
from server.config import load_settings
from server.redis_service import start_pubsub_listener
from server.session import ClientSession
from server.state import ServerState

logger = logging.getLogger(__name__)


def _pubsub_handler(state: ServerState):
    def _handler(payload: dict[str, Any]) -> None:
        typ = payload.get("type")
        if typ in {
            MessageType.CHAT.value,
            MessageType.USER_JOINED.value,
            MessageType.USER_LEFT.value,
        }:
            demo(
                logger,
                f"Redis pub/sub → broadcast TCP para clientes conectados",
                fn="server.main._pubsub_handler",
                event_type=typ,
            )
            state.tcp_registry.broadcast_bytes(encode_line(payload))

    return _handler


def _run_tcp_server(state: ServerState) -> None:
    settings = state.settings
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((settings.host, settings.port))
    sock.listen(128)
    logger.info("Servidor TCP escutando em %s:%s", settings.host, settings.port)
    if demo_enabled():
        demo(
            logger,
            "Modo DEMO ativo no servidor — logs mostram threads, TCP e funções",
            fn="server.main._run_tcp_server",
        )

    while not state.stop_event.is_set():
        try:
            sock.settimeout(1.0)
            conn, addr = sock.accept()
        except TimeoutError:
            continue
        except OSError:
            break
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        demo(
            logger,
            "Nova conexão TCP — disparando ClientSession (1 thread por conexão)",
            fn="server.main._run_tcp_server",
            peer=f"{addr[0]}:{addr[1]}",
        )
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


def start_server(state: ServerState | None = None) -> ServerState:
    """Inicia pub/sub e thread do listener TCP; retorna o estado compartilhado."""
    srv = state or ServerState(load_settings())
    srv.backend.ping()

    start_pubsub_listener(
        srv.settings.redis_url,
        srv.settings.pubsub_channel,
        _pubsub_handler(srv),
        stop_event=srv.stop_event,
    )

    threading.Thread(
        target=_run_tcp_server,
        args=(srv,),
        name="tcp-server",
        daemon=True,
    ).start()
    return srv


def run() -> None:
    """Bloqueia até SIGINT/SIGTERM (modo só-servidor em dev)."""
    srv = start_server()

    def _stop(*_: Any) -> None:
        logger.info("Encerrando servidor TCP...")
        srv.stop_event.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    srv.stop_event.wait()


def main() -> None:
    configure_logging()
    run()


if __name__ == "__main__":
    main()
