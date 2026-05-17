"""Conexão TCP com thread dedicada a ``recv`` (requisito acadêmico)."""

from __future__ import annotations

import logging
import socket
import threading
from typing import TYPE_CHECKING

from common.demo_log import demo, tcp_frame, thread_start
from common.protocol import MessageType, decode_line, encode_line

if TYPE_CHECKING:
    from client.inbound import InboundDemux

logger = logging.getLogger(__name__)


class SocketBridge:
    """
    Ponte TCP para o servidor de chat.

    ``send_*`` é chamado pelas rotas HTTP; ``_recv_loop`` roda em thread própria.
    """

    __slots__ = (
        "_host",
        "_port",
        "_conn",
        "_send_lock",
        "_demux",
        "_reader_thread",
        "_closed",
        "_username",
    )

    def __init__(
        self,
        host: str,
        port: int,
        demux: InboundDemux,
        *,
        username: str,
    ) -> None:
        self._host = host
        self._port = port
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._send_lock = threading.Lock()
        self._demux = demux
        self._username = username
        self._reader_thread = threading.Thread(
            target=self._recv_loop,
            name=f"socket-recv-{username}",
            daemon=True,
        )
        self._closed = threading.Event()

    def connect(self) -> None:
        self._conn.connect((self._host, self._port))
        self._conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._reader_thread.start()
        demo(
            logger,
            f"Thread de recepção disparada: {self._reader_thread.name!r} (requisito do enunciado)",
            fn="client.socket_bridge.SocketBridge.connect",
            username=self._username,
        )
        logger.info("TCP conectado a %s:%s (%s)", self._host, self._port, self._username)

    def is_closed(self) -> bool:
        return self._closed.is_set()

    def close(self) -> None:
        self._closed.set()
        try:
            self._conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self._conn.close()
        except OSError:
            pass

    def _send_raw(self, frame: bytes) -> None:
        with self._send_lock:
            self._conn.sendall(frame)

    def send_ping(self) -> None:
        self._send_raw(encode_line({"type": MessageType.PING.value}))

    def send_login(self, username: str) -> None:
        frame = {"type": MessageType.LOGIN.value, "username": username}
        self._send_raw(encode_line(frame))
        tcp_frame(logger, "→ enviado", frame, fn="client.socket_bridge.SocketBridge.send_login")

    def send_message(self, text: str) -> None:
        frame = {"type": MessageType.MESSAGE.value, "text": text}
        self._send_raw(encode_line(frame))
        tcp_frame(logger, "→ enviado", frame, fn="client.socket_bridge.SocketBridge.send_message")

    def send_history_since(self, since: float) -> None:
        frame = {"type": MessageType.HISTORY_SINCE.value, "since": since}
        self._send_raw(encode_line(frame))
        tcp_frame(logger, "→ enviado", frame, fn="client.socket_bridge.SocketBridge.send_history_since")

    def _recv_loop(self) -> None:
        thread_start(
            logger,
            "SocketBridge._recv_loop — só recebe frames TCP (HTTP fica em outra thread)",
            username=self._username,
        )
        try:
            fp = self._conn.makefile("rb")
            try:
                for raw in fp:
                    if self._closed.is_set() or not raw:
                        break
                    try:
                        msg = decode_line(raw)
                    except (UnicodeDecodeError, ValueError, TypeError) as exc:
                        logger.info("Frame inválido (%s): %s", self._username, exc)
                        continue
                    tcp_frame(logger, "← recebido", msg, fn="client.socket_bridge.SocketBridge._recv_loop")
                    self._demux.push(msg)
            finally:
                try:
                    fp.close()
                except OSError:
                    pass
        except OSError as exc:
            logger.info("Socket encerrado (%s): %s", self._username, exc)
        finally:
            self._closed.set()
