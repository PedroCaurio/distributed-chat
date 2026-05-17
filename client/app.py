"""
API HTTP do cliente (proxy): expõe o chat ao navegador.

O React é servido pelo mesmo processo (servidor HTTP embutido).
Comunicação com o servidor de chat ocorre via sockets TCP + threads.
"""

from __future__ import annotations

import json
import logging
import os
import queue
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from common.demo_log import demo, enabled as demo_logs_enabled

from client.affinity import (
    AffinityStore,
    FlyAffinityMiddleware,
    affinity_cookie_value,
    local_machine_id,
    set_affinity_cookie,
)
from client.config import ProxySettings, load_settings
from client.request_trace import trace_session_http
from client.runtime import ProxyRuntime
from client.session_guard import reject_unknown_session

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=32)


class MessageBody(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


def create_app(settings: ProxySettings | None = None) -> FastAPI:
    cfg = settings or load_settings()
    affinity_store = AffinityStore(cfg.redis_url) if cfg.redis_url else None
    runtime = ProxyRuntime(cfg)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        runtime.close_all()

    app = FastAPI(
        title="Distributed Chat Client",
        version="2.0.0",
        description="Proxy HTTP → TCP (requisito cliente-servidor com threads)",
        lifespan=lifespan,
    )

    app.add_middleware(FlyAffinityMiddleware, store=affinity_store)

    if cfg.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cfg.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "role": "client",
            "instance": local_machine_id() or os.getenv("HOSTNAME", "local"),
            "active_sessions": runtime.active_session_count,
            "demo_logs": demo_logs_enabled(),
        }

    @app.post("/login")
    def login(body: LoginBody) -> JSONResponse:
        demo(
            logger,
            "HTTP POST /login — navegador entrou; proxy abrirá TCP",
            fn="client.app.login",
            username=body.username,
        )
        try:
            payload = runtime.login(body.username)
        except TimeoutError:
            raise HTTPException(status_code=504, detail="timeout ao autenticar no servidor")
        except OSError as exc:
            raise HTTPException(status_code=503, detail=f"servidor TCP indisponível: {exc}")
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if payload.get("type") == "error":
            return JSONResponse(status_code=401, content=payload)

        machine = affinity_cookie_value()
        if machine:
            payload["fly_instance_id"] = machine

        response = JSONResponse(status_code=200, content=payload)
        session_id = str(payload.get("session_id", ""))
        if session_id:
            set_affinity_cookie(response, session_id, affinity_store)
        return response

    @app.post("/logout")
    def logout(x_session_id: str | None = Header(default=None, alias="X-Session-Id")) -> dict[str, str]:
        if x_session_id:
            runtime.logout(x_session_id)
        return {"status": "ok"}

    @app.post("/messages")
    def post_message(
        body: MessageBody,
        x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    ) -> dict[str, str]:
        if not x_session_id:
            raise HTTPException(status_code=401, detail="X-Session-Id obrigatório")
        demo(
            logger,
            "HTTP POST /messages — repassando texto ao servidor via TCP",
            fn="client.app.post_message",
            text=body.text[:80],
        )
        try:
            runtime.send_chat(x_session_id, body.text)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"status": "enqueued"}

    @app.post("/heartbeat")
    def heartbeat(
        request: Request,
        x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    ) -> dict[str, bool]:
        sid = (x_session_id or "").strip()
        if not sid:
            raise HTTPException(status_code=401, detail="sessão inválida")
        if runtime.get_session(sid) is None:
            reject_unknown_session(
                request,
                runtime,
                label="POST /heartbeat",
                session_id=sid,
                affinity_store=affinity_store,
            )
        if not runtime.heartbeat(sid):
            raise HTTPException(status_code=401, detail="sessão inválida")
        trace_session_http(
            request,
            runtime,
            label="POST /heartbeat",
            session_id=sid,
            affinity_store=affinity_store,
            status=200,
            reason="heartbeat_ok",
        )
        return {"ok": True}

    @app.get("/history")
    def history_since(
        request: Request,
        since: float = Query(0),
        session: str | None = Query(default=None, min_length=8),
        x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    ) -> dict[str, Any]:
        sid = (x_session_id or session or "").strip()
        if not sid:
            trace_session_http(
                request,
                runtime,
                label="GET /history",
                session_id="?",
                affinity_store=affinity_store,
                status=401,
                reason="sem_session_id",
            )
            raise HTTPException(status_code=401, detail="sessão inválida")
        reject_unknown_session(
            request,
            runtime,
            label="GET /history",
            session_id=sid,
            affinity_store=affinity_store,
        )
        trace_session_http(
            request,
            runtime,
            label="GET /history",
            session_id=sid,
            affinity_store=affinity_store,
            status=200,
            reason="history_ok",
            since=since,
        )
        items = runtime.fetch_history_since(sid, since)
        return {"messages": items}

    def _sse_stream(session_id: str) -> Iterator[str]:
        demo(
            logger,
            "HTTP GET /events — SSE aberto; fila alimentada pela thread socket-recv",
            fn="client.app._sse_stream",
            session_id=session_id[:8] + "…",
        )
        event_queue = runtime.subscribe_sse(session_id)
        try:
            while True:
                try:
                    payload = event_queue.get(timeout=25)
                except queue.Empty:
                    yield ": keepalive\n\n"
                    runtime.heartbeat(session_id)
                    continue
                typ = payload.get("type")
                if typ in {"chat", "user_joined", "user_left"}:
                    demo(
                        logger,
                        f"SSE → navegador evento type={typ!r}",
                        fn="client.app._sse_stream",
                    )
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except GeneratorExit:
            return
        finally:
            runtime.unsubscribe_sse(session_id, event_queue)

    @app.get("/events")
    def events(request: Request, session: str = Query(..., min_length=8)) -> StreamingResponse:
        reject_unknown_session(
            request,
            runtime,
            label="GET /events",
            session_id=session,
            affinity_store=affinity_store,
        )
        trace_session_http(
            request,
            runtime,
            label="GET /events",
            session_id=session,
            affinity_store=affinity_store,
            status=200,
            reason="sse_aberto",
        )
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
        index_path = STATIC_DIR / "index.html"

        @app.get("/")
        def spa_index() -> FileResponse:
            return FileResponse(
                index_path,
                media_type="text/html",
                headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
            )

        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


def build_app() -> FastAPI:
    return create_app()
