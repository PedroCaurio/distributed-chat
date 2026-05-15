"""API HTTP local (FastAPI) exposta ao front-end."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

import anyio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from client.config import ProxySettings, load_settings
from client.runtime import ProxyRuntime

logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=32)


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


def create_app(settings: ProxySettings | None = None) -> FastAPI:
    cfg = settings or load_settings()
    runtime = ProxyRuntime(cfg)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await anyio.to_thread.run_sync(runtime.connect)
        try:
            yield
        finally:
            await anyio.to_thread.run_sync(runtime.close)

    app = FastAPI(title="Chat Proxy", version="0.1.0", lifespan=lifespan)

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
        return {"status": "ok", "connected": runtime.is_connected(), "user": runtime.username}

    @app.post("/login")
    def login(req: LoginRequest) -> JSONResponse:
        try:
            payload = runtime.login(req.username)
        except TimeoutError:
            raise HTTPException(status_code=504, detail="timeout ao autenticar no servidor")
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if payload.get("type") == "error":
            return JSONResponse(status_code=401, content=payload)
        return JSONResponse(status_code=200, content=payload)

    @app.post("/messages")
    def post_message(req: SendMessageRequest) -> dict[str, str]:
        try:
            runtime.send_chat(req.text)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"status": "enqueued"}

    def _sse_generator() -> Iterator[str]:
        q = runtime.sse_queue()
        while True:
            msg = q.get()
            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

    @app.get("/events")
    def events() -> StreamingResponse:
        return StreamingResponse(_sse_generator(), media_type="text/event-stream")

    return app


def build_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return create_app()
