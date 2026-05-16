"""
API HTTP pública do chat (100% web).

Cada stream SSE bloqueia em ``Queue.get`` (recepção síncrona por conexão),
atendendo o requisito de thread de escuta no caminho do cliente navegador.
"""

from __future__ import annotations

import json
import logging
import os
import queue
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from common.protocol import MessageType

if TYPE_CHECKING:
    from server.http_state import AppState

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=32)


class MessageBody(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


def create_http_app(state: AppState) -> FastAPI:
    app = FastAPI(title="Distributed Chat API", version="2.0.0")

    cors_raw = os.getenv("CORS_ORIGINS", "").strip()
    if cors_raw:
        origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "instance": os.getenv("FLY_MACHINE_ID", os.getenv("HOSTNAME", "local")),
        }

    @app.post("/login")
    def login(body: LoginBody) -> JSONResponse:
        result = state.core.login(body.username)
        if isinstance(result, str):
            return JSONResponse(status_code=401, content={"type": "error", "message": result})
        return JSONResponse(
            status_code=200,
            content={
                "type": "welcome",
                "session_id": result.session_id,
                "client_id": result.client_id,
                "username": result.username,
                "history": result.history,
            },
        )

    @app.post("/logout")
    def logout(x_session_id: str | None = Header(default=None, alias="X-Session-Id")) -> dict[str, str]:
        if x_session_id:
            state.core.logout(x_session_id)
        return {"status": "ok"}

    @app.post("/messages")
    def post_message(
        body: MessageBody,
        x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    ) -> dict[str, str]:
        if not x_session_id:
            raise HTTPException(status_code=401, detail="X-Session-Id obrigatório")
        state.core.refresh_session(x_session_id)
        result = state.core.send_message(x_session_id, body.text)
        if isinstance(result, str):
            raise HTTPException(status_code=400, detail=result)
        return {"status": "enqueued"}

    @app.post("/heartbeat")
    def heartbeat(x_session_id: str | None = Header(default=None, alias="X-Session-Id")) -> dict[str, bool]:
        if not x_session_id or not state.core.refresh_session(x_session_id):
            raise HTTPException(status_code=401, detail="sessão inválida")
        return {"ok": True}

    @app.get("/history")
    def history_since(
        since: float = Query(0, description="Timestamp mínimo (exclusivo)"),
        x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    ) -> dict[str, Any]:
        if not x_session_id or not state.backend.get_session_username(x_session_id):
            raise HTTPException(status_code=401, detail="sessão inválida")
        items = state.backend.get_history_since(since, limit=state.settings.history_max)
        return {"messages": items}

    def _sse_stream(session_id: str) -> Iterator[str]:
        if not state.backend.get_session_username(session_id):
            yield f'data: {json.dumps({"type": "error", "message": "sessão inválida"})}\n\n'
            return

        event_queue = state.sse_hub.subscribe()
        try:
            state.core.refresh_session(session_id)
            while not state.stop_event.is_set():
                try:
                    payload = event_queue.get(timeout=25)
                except queue.Empty:
                    yield ": keepalive\n\n"
                    state.core.refresh_session(session_id)
                    continue
                typ = payload.get("type")
                if typ in {
                    MessageType.CHAT.value,
                    MessageType.USER_JOINED.value,
                    MessageType.USER_LEFT.value,
                }:
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        finally:
            state.sse_hub.unsubscribe(event_queue)

    @app.get("/events")
    def events(session: str = Query(..., min_length=8)) -> StreamingResponse:
        return StreamingResponse(
            _sse_stream(session),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app
