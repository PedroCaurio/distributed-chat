"""
proxy.py — Proxy HTTP → TCP
============================
Bridges the browser (HTTP/SSE) to the TCP chat server.

Browser                     Proxy                    TCP Server
──────                      ─────                    ──────────
POST /login          →      login via TCP       →    authenticate
POST /message        →      message via TCP     →    broadcast
GET  /events (SSE)   ←      recv thread         ←    event stream
GET  /               ←      serves index.html

Thread dedicada à recepção: cada sessão tem uma TCPSession._recv_thread
que fica bloqueada lendo o socket TCP — satisfaz o requisito acadêmico.

Variáveis de ambiente:
  SERVER_HOST  — host do servidor TCP (padrão: localhost)
  SERVER_PORT  — porta do servidor TCP (padrão: 5000)
  PROXY_PORT   — porta HTTP deste proxy (padrão: 8080)
"""

import json
import logging
import os
import queue
import socket
import threading
import time
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTPServer que atende cada requisicao em uma thread separada.
    Necessario para que POST /message nao bloqueie enquanto GET /events
    esta ativo — SSE mantem a conexao aberta indefinidamente."""
    daemon_threads = True
from pathlib import Path

from affinity import AffinityStore, affinity_extra_headers, local_machine_id, maybe_replay
from protocol import decode, encode
from redis_backend import RedisBackend

# ── Configuração ──────────────────────────────────────────────────────────────
SERVER_HOST = os.environ.get("SERVER_HOST", os.environ.get("CHAT_SERVER_HOST", "localhost"))
SERVER_PORT = int(os.environ.get("SERVER_PORT", os.environ.get("CHAT_SERVER_PORT", 5000)))
PROXY_PORT  = int(os.environ.get("PROXY_PORT", os.environ.get("PORT", 8080)))
REDIS_URL   = os.environ.get("REDIS_URL", "")
_affinity_store: AffinityStore | None = AffinityStore(REDIS_URL) if REDIS_URL else None
_redis: RedisBackend | None = RedisBackend(REDIS_URL) if REDIS_URL else None

FRONTEND_HTML = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [PROXY ] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("proxy")


# ── Demux TCP (igual ao distributed-chat: login/RPC ≠ SSE) ─────────────────────

class InboundDemux:
    """
    Demultiplexador: thread recv envia frames aqui.

    Login usa RPC síncrono (arm_rpc/wait_rpc); SSE usa filas subscribe/push.
    """

    def __init__(self) -> None:
        """Inicializa filas de assinantes SSE e estado RPC."""
        self._lock = threading.Lock()
        self._subscribers: set[queue.Queue] = set()
        self._rpc_kind: str | None = None
        self._rpc_event: threading.Event | None = None
        self._rpc_response: dict | None = None

    def subscribe(self) -> queue.Queue:
        """Cria fila para uma conexão GET /events (SSE)."""
        q: queue.Queue = queue.Queue()
        with self._lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        """Remove fila ao encerrar SSE."""
        with self._lock:
            self._subscribers.discard(q)

    def arm_rpc(self, kind: str) -> None:
        """Prepara espera por resposta única (ex.: welcome no login)."""
        with self._lock:
            self._rpc_kind = kind
            self._rpc_event = threading.Event()
            self._rpc_response = None

    def disarm_rpc(self) -> None:
        """Cancela modo RPC após login ou timeout."""
        with self._lock:
            self._rpc_kind = None
            self._rpc_event = None
            self._rpc_response = None

    def wait_rpc(self, kind: str, *, timeout_s: float) -> dict:
        """Bloqueia até resposta RPC ou TimeoutError."""
        with self._lock:
            if self._rpc_kind != kind or self._rpc_event is None:
                raise RuntimeError(f"arm_rpc({kind!r}) não foi chamado")
            evt = self._rpc_event
        if not evt.wait(timeout_s):
            raise TimeoutError(f"timeout aguardando {kind}")
        with self._lock:
            resp = self._rpc_response
        if resp is None:
            raise RuntimeError("resposta RPC ausente")
        return resp

    def push(self, msg: dict) -> None:
        """Distribui frame TCP às filas SSE ou completa RPC de login."""
        typ = msg.get("type")
        with self._lock:
            kind = self._rpc_kind
            evt = self._rpc_event
            if evt is not None and kind == "login" and typ in {"welcome", "error"}:
                self._rpc_response = msg
                evt.set()
                return
            if typ in {"pong", "ping", "history"}:
                return
            targets = list(self._subscribers)

        for q in targets:
            try:
                q.put_nowait(msg)
            except queue.Full:
                pass


class TCPSession:
    """Conexão TCP com o servidor + thread recv dedicada (requisito acadêmico)."""

    def __init__(self, demux: InboundDemux, *, label: str) -> None:
        """Args: demux — onde push() envia frames; label — nome para logs/threads."""
        self._demux = demux
        self._label = label
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._lock = threading.Lock()
        self._closed = threading.Event()
        self._recv_thread = threading.Thread(
            target=self._recv_loop,
            name=f"recv-{label}",
            daemon=True,
        )

    def connect(self) -> None:
        """Conecta ao servidor TCP e inicia thread _recv_loop."""
        self._conn.connect((SERVER_HOST, SERVER_PORT))
        self._conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._recv_thread.start()
        log.info("TCP conectado (%s)", self._label)

    def send(self, **kwargs) -> None:
        """Envia frame NDJSON ao servidor (login, message, ping…)."""
        with self._lock:
            self._conn.sendall(encode(kwargs))

    def close(self) -> None:
        """Encerra socket e sinaliza thread recv."""
        self._closed.set()
        try:
            self._conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self._conn.close()
        except OSError:
            pass

    def is_closed(self) -> bool:
        """True se a conexão TCP foi encerrada."""
        return self._closed.is_set()

    def _recv_loop(self) -> None:
        """Lê NDJSON com recv() — makefile + send() em threads distintas perde frames."""
        buf = b""
        try:
            while not self._closed.is_set():
                try:
                    chunk = self._conn.recv(4096)
                except OSError:
                    break
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = decode(line)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                    if msg:
                        self._demux.push(msg)
        finally:
            self._closed.set()


@dataclass
class ProxySession:
    """Sessão de um navegador: apelido + demux + ponte TCP."""

    username: str
    demux: InboundDemux
    tcp: TCPSession


_sessions: dict[str, ProxySession] = {}
_sessions_lock = threading.Lock()
_proxy_stop = threading.Event()


def _get_session(proxy_id: str) -> ProxySession | None:
    with _sessions_lock:
        return _sessions.get(proxy_id)


def _remove_session(proxy_id: str) -> None:
    with _sessions_lock:
        sess = _sessions.pop(proxy_id, None)
    if sess:
        sess.tcp.close()


def _login(
    username: str,
    client_id: str,
    since: float = 0.0,
) -> tuple[str | None, dict]:
    """Abre TCP, autentica e registra sessão proxy (id devolvido ao navegador)."""
    proxy_id = uuid.uuid4().hex
    demux = InboundDemux()
    tcp = TCPSession(demux, label=username)
    try:
        tcp.connect()
    except OSError as exc:
        return None, {"error": f"servidor indisponível: {exc}"}

    demux.arm_rpc("login")
    try:
        tcp.send(type="login", username=username, client_id=client_id, since=since)
        response = demux.wait_rpc("login", timeout_s=10.0)
    except TimeoutError:
        tcp.close()
        return None, {"error": "timeout no login"}
    finally:
        demux.disarm_rpc()

    if response.get("type") == "error":
        tcp.close()
        return None, {"error": response.get("message", "erro no login")}

    uname = str(response.get("username", username))
    with _sessions_lock:
        _sessions[proxy_id] = ProxySession(username=uname, demux=demux, tcp=tcp)
    return proxy_id, response


def _query_session_id(path: str) -> str | None:
    if "session=" in path:
        return path.split("session=")[-1].split("&")[0].strip()
    if "sid=" in path:
        return path.split("sid=")[-1].split("&")[0].strip()
    return None


def _machine_heartbeat_loop() -> None:
    while True:
        mid = local_machine_id()
        if mid and _redis is not None:
            _redis.touch_machine(mid)
        time.sleep(12)


def _fanout_redis_event(payload: dict) -> None:
    """
    Repassa eventos Redis para todas as sessões locais (SSE).

    O servidor ignora eco Redis na mesma VM (_origin); o proxy precisa
    ouvir o canal para tempo real no Fly quando o eco TCP falha.
    """
    typ = payload.get("type")
    if typ not in {"chat", "user_joined", "user_left"}:
        return
    clean = {k: v for k, v in payload.items() if k != "_origin"}
    with _sessions_lock:
        targets = list(_sessions.values())
    for sess in targets:
        sess.demux.push(clean)


# ── Handler HTTP ──────────────────────────────────────────────────────────────

class ProxyHandler(BaseHTTPRequestHandler):
    """
    Servidor HTTP embutido (requisito do enunciado).

    Rotas: /, /login, /resume, /message, /events (SSE), /logout, /health.
    """

    protocol_version = "HTTP/1.1"

    # ── Roteamento ────────────────────────────────────────────────────────────

    def do_GET(self):
        if maybe_replay(self, _affinity_store):
            return
        if self.path in ("/", "/index.html"):
            self._serve_html()
        elif self.path.startswith("/events"):
            self._handle_events()
        elif self.path.startswith("/users"):
            self._handle_users()
        elif self.path.startswith("/history"):
            self._handle_history()
        elif self.path in ("/health", "/ping"):
            self._handle_health()
        else:
            self._write_json(404, {"error": "Not Found"})

    def do_POST(self):
        if maybe_replay(self, _affinity_store):
            return
        if self.path == "/login":
            self._handle_login()
        elif self.path == "/resume":
            self._handle_resume()
        elif self.path == "/message":
            self._handle_message()
        elif self.path == "/heartbeat":
            self._handle_heartbeat()
        elif self.path == "/logout":
            self._handle_logout()
        else:
            self._write_json(404, {"error": "Not Found"})

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _serve_html(self):
        body = FRONTEND_HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.end_headers()
        self._write(body)

    def _handle_login(self):
        body = self._read_json()
        if body is None:
            return
        username = str(body.get("username", "")).strip()[:32]
        client_id = str(body.get("client_id", "")).strip()[:64]
        if not username:
            return self._write_json(400, {"error": "username inválido"})

        old = self.headers.get("X-Session-Id", "").strip()
        if old:
            _remove_session(old)

        proxy_id, response = _login(username, client_id)
        if proxy_id is None:
            err = response.get("error", "erro no login")
            code = 504 if "timeout" in err else 503 if "indisponível" in err else 401
            return self._write_json(code, {"error": err})
        log.info("Login OK: '%s' (proxy %s)", username, proxy_id[:8])
        self._write_session_ok(proxy_id, username, response)

    def _handle_resume(self):
        body = self._read_json()
        if body is None:
            return
        username = str(body.get("username", "")).strip()[:32]
        client_id = str(body.get("client_id", "")).strip()[:64]
        since = float(body.get("since", 0) or 0)
        if not username:
            return self._write_json(400, {"error": "username obrigatório"})

        old = self.headers.get("X-Session-Id", "").strip()
        if old:
            _remove_session(old)

        proxy_id, response = _login(username, client_id, since=since)
        if proxy_id is None:
            err = response.get("error", "falha ao retomar")
            code = 504 if "timeout" in err else 503 if "indisponível" in err else 401
            return self._write_json(code, {"error": err})

        log.info("Resume OK: '%s' (proxy %s)", username, proxy_id[:8])
        self._write_session_ok(proxy_id, username, response)

    def _write_session_ok(self, proxy_id: str, username: str, response: dict) -> None:
        extra = affinity_extra_headers(proxy_id, _affinity_store)
        self._write_json(
            200,
            {
                "session_id": proxy_id,
                "username": response.get("username", username),
                "history": response.get("history", []),
                "users": response.get("users", []),
                "rejoined": bool(response.get("rejoined")),
            },
            extra_headers=extra,
        )

    def _handle_message(self):
        proxy_id = self._get_sid()
        if not proxy_id:
            return
        body = self._read_json()
        if body is None:
            return
        text = str(body.get("text", "")).strip()[:500]
        if not text:
            return self._write_json(400, {"error": "mensagem vazia"})

        sess = _get_session(proxy_id)
        if sess is None or sess.tcp.is_closed():
            return self._write_json(401, {"error": "sessão inválida — faça login novamente"})

        try:
            sess.tcp.send(type="message", text=text)
        except OSError:
            return self._write_json(503, {"error": "tcp indisponível"})
        self._write_json(200, {"ok": True})

    def _handle_heartbeat(self):
        proxy_id = self._get_sid()
        if not proxy_id:
            return

        sess = _get_session(proxy_id)
        if sess is None or sess.tcp.is_closed():
            return self._write_json(401, {"error": "sessão inválida"})

        try:
            sess.tcp.send(type="ping")
        except OSError:
            return self._write_json(503, {"error": "tcp indisponível"})
        self._write_json(200, {"ok": True})

    def _handle_history(self) -> None:
        if _redis is None:
            return self._write_json(503, {"error": "redis indisponível"})
        since = 0.0
        if "since=" in self.path:
            try:
                since = float(self.path.split("since=")[-1].split("&")[0])
            except ValueError:
                since = 0.0
        items = _redis.get_history_since(since)
        self._write_json(200, {"items": items})

    def _handle_events(self):
        """SSE — fila alimentada pela thread TCP recv (mesmo padrão do distributed-chat)."""
        proxy_id = _query_session_id(self.path)
        if not proxy_id:
            return self._write_json(400, {"error": "session obrigatório"})

        sess = _get_session(proxy_id)
        if sess is None or sess.tcp.is_closed():
            return self._write_json(401, {"error": "sessão inválida"})

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        # Evita buffering do edge Fly/nginx antes do primeiro evento
        self._write(b": " + b" " * 2048 + b"\n\n")

        event_q = sess.demux.subscribe()
        try:
            while True:
                try:
                    event = event_q.get(timeout=15)
                except queue.Empty:
                    self._write(b": keepalive\n\n")
                    try:
                        sess.tcp.send(type="ping")
                    except OSError:
                        break
                    continue

                typ = event.get("type")
                if typ in {"chat", "user_joined", "user_left"}:
                    data = json.dumps(event, ensure_ascii=False)
                    self._write(f"data: {data}\n\n".encode())

        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            sess.demux.unsubscribe(event_q)

    def _handle_users(self):
        sid = self._get_sid()
        if not sid:
            return
        if _redis is None:
            return self._write_json(503, {"error": "redis indisponível"})
        self._write_json(200, {"users": _redis.get_online_users()})

    def _handle_health(self) -> None:
        with _sessions_lock:
            count = len(_sessions)
        body = json.dumps(
            {
                "status": "ok",
                "role": "proxy",
                "instance": local_machine_id() or "local",
                "active_sessions": count,
            },
            ensure_ascii=False,
        ).encode()
        self._send_headers(200, "application/json", len(body))
        self._write(body)

    def _handle_logout(self):
        proxy_id = self._get_sid()
        if proxy_id:
            sess = _get_session(proxy_id)
            if sess and not sess.tcp.is_closed():
                try:
                    sess.tcp.send(type="logout")
                except OSError:
                    pass
            _remove_session(proxy_id)
            if _affinity_store is not None:
                _affinity_store.clear(proxy_id)
            log.info("Logout: sessão %s", proxy_id[:8])
        self._write_json(200, {"ok": True})

    # ── Primitivas de I/O ─────────────────────────────────────────────────────

    def _send_headers(
        self,
        code: int,
        content_type: str,
        length: int,
        extra_headers: list[tuple[str, str]] | None = None,
    ) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Access-Control-Allow-Origin", "*")
        if extra_headers:
            for key, value in extra_headers:
                self.send_header(key, value)
        self.end_headers()

    def _write(self, data: bytes) -> None:
        """Escreve bytes no socket — ignora BrokenPipe silenciosamente."""
        try:
            self.wfile.write(data)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass  # cliente fechou a conexão antes da resposta — normal em HTTP

    def _write_json(
        self,
        code: int,
        data: dict,
        extra_headers: list[tuple[str, str]] | None = None,
    ) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self._send_headers(code, "application/json", len(body), extra_headers=extra_headers)
        self._write(body)

    def _write_text(self, text: str) -> None:
        body = text.encode()
        self._send_headers(200, "text/plain", len(body))
        self._write(body)

    def _read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            self._write_json(400, {"error": "corpo vazio"})
            return None
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self._write_json(400, {"error": "JSON inválido"})
            return None

    def _get_sid(self) -> str | None:
        sid = self.headers.get("X-Session-Id")
        if not sid:
            self._write_json(401, {"error": "X-Session-Id obrigatório"})
        return sid

    def log_message(self, fmt, *args):
        """Silencia logs de acesso HTTP no stdout (erros já aparecem via logging)."""
        pass

    def log_error(self, fmt, *args):
        """Silencia BrokenPipe e outros erros de conexão comuns."""
        msg = fmt % args
        # BrokenPipe é comportamento normal — browser fecha conexão cedo
        if "BrokenPipe" in msg or "ConnectionReset" in msg or "32" in msg:
            return
        log.warning("HTTP error: %s", msg)


# ── Ponto de entrada ──────────────────────────────────────────────────────────

def main() -> None:
    """Inicia subscriber Redis (SSE), heartbeat Fly e ThreadingHTTPServer."""
    log.info("Proxy HTTP escutando em http://0.0.0.0:%d", PROXY_PORT)
    log.info("Conectando ao servidor TCP em %s:%d", SERVER_HOST, SERVER_PORT)
    if _redis is not None:
        _redis.start_subscriber(_fanout_redis_event, _proxy_stop)
        log.info("Proxy inscrito no Redis pub/sub (SSE em tempo real)")
        if local_machine_id():
            threading.Thread(target=_machine_heartbeat_loop, name="fly-heartbeat", daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", PROXY_PORT), ProxyHandler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        log.info("Proxy encerrado.")


if __name__ == "__main__":
    main()
