"""Sessão TCP: uma thread por conexão, loop de leitura NDJSON."""

from __future__ import annotations

import logging
import socket
import threading
import time
import uuid
from typing import TYPE_CHECKING, Any

from common.protocol import MessageType, decode_line, encode_line

if TYPE_CHECKING:
    from server.config import ServerSettings
    from server.redis_service import RedisChatBackend
    from server.registry import ClientRegistry

logger = logging.getLogger(__name__)


def _now_ts() -> float:
    return time.time()


def _validate_username(raw: str) -> str | None:
    username = raw.strip()
    if not username or len(username) > 32:
        return None
    return username


def _validate_text(raw: str) -> str | None:
    text = raw.strip()
    if not text or len(text) > 4000:
        return None
    return text


class ClientSession(threading.Thread):
    """Thread de atendimento de um cliente conectado via TCP."""

    def __init__(
        self,
        conn: socket.socket,
        addr: tuple[str, int],
        *,
        backend: RedisChatBackend,
        registry: ClientRegistry,
        settings: ServerSettings,
    ) -> None:
        super().__init__(name=f"client-{addr}", daemon=True)
        self._conn = conn
        self._addr = addr
        self._backend = backend
        self._registry = registry
        self._settings = settings
        self._send_lock = threading.Lock()
        self._username: str | None = None
        self._client_id = uuid.uuid4().hex
        self._closed = threading.Event()
        self._sender: Any = None

    def _send_raw(self, frame: bytes) -> None:
        with self._send_lock:
            self._conn.sendall(frame)

    def _send_error(self, message: str) -> None:
        self._send_raw(
            encode_line({"type": MessageType.ERROR.value, "message": message})
        )

    def _handle_login(self, msg: dict[str, Any]) -> None:
        if self._username is not None:
            self._send_error("já autenticado")
            return
        username = _validate_username(str(msg.get("username", "")))
        if not username:
            self._send_error("username inválido (1–32 caracteres)")
            return
        if not self._backend.try_register_presence(username):
            self._send_error("username já está em uso")
            return
        self._username = username
        history = self._backend.get_history(limit=self._settings.history_max)
        self._send_raw(
            encode_line(
                {
                    "type": MessageType.WELCOME.value,
                    "client_id": self._client_id,
                    "username": self._username,
                    "history": history,
                }
            )
        )
        self._backend.publish(
            self._settings.pubsub_channel,
            {
                "type": MessageType.USER_JOINED.value,
                "username": self._username,
                "ts": _now_ts(),
            },
        )

    def _handle_message(self, msg: dict[str, Any]) -> None:
        if self._username is None:
            self._send_error("login obrigatório")
            return
        text = _validate_text(str(msg.get("text", "")))
        if not text:
            self._send_error("mensagem vazia ou longa demais")
            return
        entry = {
            "username": self._username,
            "text": text,
            "ts": _now_ts(),
            "id": uuid.uuid4().hex,
        }
        self._backend.append_history(
            {"username": entry["username"], "text": entry["text"], "ts": entry["ts"], "id": entry["id"]}
        )
        self._backend.publish(
            self._settings.pubsub_channel,
            {
                "type": MessageType.CHAT.value,
                "username": entry["username"],
                "text": entry["text"],
                "ts": entry["ts"],
                "id": entry["id"],
            },
        )

    def run(self) -> None:  # noqa: D102
        sender = self._send_raw
        self._sender = sender
        self._registry.add(sender)
        reader = self._conn.makefile("rb")
        try:
            logger.info("Cliente conectado de %s", self._addr)
            for raw_line in reader:
                if self._closed.is_set():
                    break
                if not raw_line:
                    break
                try:
                    msg = decode_line(raw_line)
                except (UnicodeDecodeError, ValueError, TypeError) as exc:
                    logger.info("Frame inválido de %s: %s", self._addr, exc)
                    self._send_error("frame JSON inválido")
                    continue
                typ = msg.get("type")
                if self._username is None:
                    if typ == MessageType.PING.value:
                        self._send_raw(
                            encode_line({"type": MessageType.PONG.value, "ts": _now_ts()}),
                        )
                        continue
                    if typ != MessageType.LOGIN.value:
                        self._send_error("envie login primeiro")
                        continue
                    try:
                        self._handle_login(msg)
                    except Exception:
                        logger.exception("Falha no login")
                        self._send_error("erro interno ao autenticar")
                    continue
                if typ == MessageType.MESSAGE.value:
                    try:
                        self._handle_message(msg)
                    except Exception:
                        logger.exception("Falha ao processar mensagem")
                        self._send_error("erro interno ao enviar mensagem")
                elif typ == MessageType.PING.value:
                    self._send_raw(encode_line({"type": MessageType.PONG.value, "ts": _now_ts()}))
                elif typ == MessageType.LOGIN.value:
                    self._send_error("já autenticado")
                else:
                    self._send_error(f"tipo desconhecido: {typ!r}")
        except OSError as exc:
            logger.info("Conexão encerrada (%s): %s", self._addr, exc)
        finally:
            self._cleanup()
            try:
                reader.close()
            except OSError:
                pass
            try:
                self._conn.close()
            except OSError:
                pass
            logger.info("Cliente desconectado de %s", self._addr)

    def _cleanup(self) -> None:
        if self._sender is not None:
            self._registry.remove(self._sender)
        username = self._username
        if username is None:
            return
        self._backend.release_presence(username)
        try:
            self._backend.publish(
                self._settings.pubsub_channel,
                {
                    "type": MessageType.USER_LEFT.value,
                    "username": username,
                    "ts": _now_ts(),
                },
            )
        except Exception:
            logger.exception("Falha ao publicar sa do usuário")

    def close(self) -> None:
        """Solicita encerramento cooperativo."""
        self._closed.set()
        try:
            self._conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
