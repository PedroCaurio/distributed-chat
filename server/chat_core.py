"""Lógica de negócio do chat compartilhada entre TCP e HTTP."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from server.config import ServerSettings
from server.redis_service import RedisChatBackend


def now_ts() -> float:
    return time.time()


def validate_username(raw: str) -> str | None:
    username = raw.strip()
    if not username or len(username) > 32:
        return None
    return username


def validate_text(raw: str) -> str | None:
    text = raw.strip()
    if not text or len(text) > 4000:
        return None
    return text


@dataclass(frozen=True, slots=True)
class LoginResult:
    session_id: str
    client_id: str
    username: str
    history: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class MessageResult:
    username: str
    text: str
    ts: float
    id: str


class ChatCore:
    """Operações de login e mensagens centralizadas."""

    __slots__ = ("_backend", "_settings")

    def __init__(self, backend: RedisChatBackend, settings: ServerSettings) -> None:
        self._backend = backend
        self._settings = settings

    def login(self, username: str) -> LoginResult | str:
        """
        Autentica usuário e cria sessão em Redis.

        Returns:
            LoginResult em sucesso ou mensagem de erro.
        """
        uname = validate_username(username)
        if not uname:
            return "username inválido (1–32 caracteres)"

        session_id = uuid.uuid4().hex
        if not self._backend.claim_username(uname, session_id):
            return "username já está em uso"

        history = self._backend.get_history(limit=self._settings.history_max)
        self._backend.publish(
            self._settings.pubsub_channel,
            {"type": "user_joined", "username": uname, "ts": now_ts()},
        )
        return LoginResult(
            session_id=session_id,
            client_id=session_id,
            username=uname,
            history=history,
        )

    def send_message(self, session_id: str, text: str) -> MessageResult | str:
        username = self._backend.get_session_username(session_id)
        if not username:
            return "sessão inválida ou expirada; faça login novamente"

        body = validate_text(text)
        if not body:
            return "mensagem vazia ou longa demais"

        entry = MessageResult(
            username=username,
            text=body,
            ts=now_ts(),
            id=uuid.uuid4().hex,
        )
        stored = {
            "username": entry.username,
            "text": entry.text,
            "ts": entry.ts,
            "id": entry.id,
        }
        self._backend.append_history(stored)
        self._backend.publish(
            self._settings.pubsub_channel,
            {"type": "chat", **stored},
        )
        return entry

    def logout(self, session_id: str) -> None:
        username = self._backend.pop_session(session_id)
        if username:
            self._backend.publish(
                self._settings.pubsub_channel,
                {"type": "user_left", "username": username, "ts": now_ts()},
            )

    def refresh_session(self, session_id: str) -> bool:
        return self._backend.refresh_session(session_id)
