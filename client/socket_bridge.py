"""Conexão TCP com thread dedicada a ``recv`` (requisito acadêmico)."""

from __future__ import annotations

import logging
import socket
import threading
from typing import TYPE_CHECKING

from common.protocol import MessageType, decode_line, encode_line

if TYPE_CHECKING:
    from client.inbound import InboundDemux

logger = logging.getLogger(__name__)


class SocketBridge:
    """
    Ponte para o servidor de chat.

    - ``send_*`` é chamado pelas rotas HTTP (thread principal / pool FastAPI).
    - ``_recv_loop`` roda em thread própria e apenas faz leitura + despacho ao demux.
    """

    __slots__ = (
        "_host",
        "_port",
        "_conn",
        "_send_lock",
        "_demux",
        "_reader_thread",
        "_closed",
    )

    def __init__(self, host: str, port: int, demux: InboundDemux) -> None:
        self._host = host
        self._port = port
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._send_lock = threading.Lock()
        self._demux = demux
        self._reader_thread = threading.Thread(target=self._recv_loop, name="socket-recv", daemon=True)
        self._closed = threading.Event()

    def connect(self) -> None:
        self._conn.connect((self._host, self._port))
        self._conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._reader_thread.start()

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
        self._send_raw(
            encode_line({"type": MessageType.LOGIN.value, "username": username}),
        )

    def send_message(self, text: str) -> None:
        self._send_raw(
            encode_line({"type": MessageType.MESSAGE.value, "text": text}),
        )

    def _recv_loop(self) -> None:
        try:
            fp = self._conn.makefile("rb")
            try:
                for raw in fp:
                    if self._closed.is_set():
                        break
                    if not raw:
                        break
                    try:
                        msg = decode_line(raw)
                    except (UnicodeDecodeError, ValueError, TypeError) as exc:
                        logger.info("Frame inválido (proxy): %s", exc)
                        continue
                    self._demux.push(msg)
            finally:
                try:
                    fp.close()
                except OSError:
                    pass
        except OSError as exc:
            logger.info("Socket encerrado: %s", exc)
        finally:
            self._closed.set()
