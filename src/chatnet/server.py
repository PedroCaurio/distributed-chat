"""
server.py — Servidor de Chat TCP
=================================
Stack: socket + threading da stdlib. Zero dependências além do redis-py.

Arquitetura:
  - Aceita conexões TCP de clientes (o proxy HTTP, não o browser diretamente)
  - Instancia uma thread por conexão (requisito acadêmico)
  - Usa NDJSON sobre TCP como protocolo (sem WebSocket)
  - Publica eventos no Redis para broadcast entre instâncias
  - Escuta o pub/sub Redis para receber eventos de outras instâncias
  - Expõe GET /health e GET /ping via HTTP simples (keep-alive do cron)

Variáveis de ambiente:
  REDIS_URL   — ex.: redis://localhost:6379  (obrigatório)
  HOST        — padrão 0.0.0.0
  PORT        — padrão 5000
"""

import json
import logging
import os
import socket
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

from .protocol import decode, encode
from .redis_backend import RedisBackend

# ── Configuração ──────────────────────────────────────────────────────────────
HOST      = os.environ.get("HOST", "0.0.0.0")
# No Fly, PORT=8080 é HTTP; o TCP do chat usa SERVER_PORT (ex.: 9000).
PORT      = int(
    os.environ.get("SERVER_PORT", os.environ.get("CHAT_SERVER_PORT", os.environ.get("PORT", 5000)))
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [SERVER] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("server")

# ── Estado global ─────────────────────────────────────────────────────────────
# Registro de callbacks de envio: {session_id: send_fn}
# Usado pelo subscriber Redis para entregar mensagens localmente.
_senders: dict[str, callable] = {}
_senders_lock = threading.Lock()

backend = RedisBackend(REDIS_URL)
stop_event = threading.Event()
# Evita duplicar evento quando já fizemos broadcast local antes do publish.
LOCAL_ORIGIN = os.getenv("FLY_MACHINE_ID") or os.getenv("HOSTNAME", "local")


# ── Broadcast local ────────────────────────────────────────────────────────────

def _broadcast_local(frame: bytes, exclude_session: str | None = None) -> None:
    """Entrega um frame NDJSON para todos os clientes TCP conectados nesta instância."""
    with _senders_lock:
        targets = [(sid, fn) for sid, fn in _senders.items() if sid != exclude_session]
    for sid, send in targets:
        try:
            send(frame)
        except OSError:
            pass  # sessão morta — cleanup ocorre no handler


# ── Handler do pub/sub Redis ──────────────────────────────────────────────────

def _publish_event(event: dict) -> None:
    """Broadcast imediato nesta VM + pub/sub para as demais."""
    typ = event.get("type")
    if typ not in {"chat", "user_joined", "user_left"}:
        return
    _broadcast_local(encode(event))
    backend.publish({**event, "_origin": LOCAL_ORIGIN})


def _on_redis_message(payload: dict) -> None:
    """Entrega eventos publicados por outras VMs (ignora eco da própria VM)."""
    if payload.get("_origin") == LOCAL_ORIGIN:
        return
    typ = payload.get("type")
    if typ in {"chat", "user_joined", "user_left"}:
        clean = {k: v for k, v in payload.items() if k != "_origin"}
        _broadcast_local(encode(clean))


# ── Sessão TCP (thread por conexão) ───────────────────────────────────────────

class ClientSession(threading.Thread):
    """
    Thread dedicada ao atendimento de um cliente TCP.
    Uma instância por conexão — satisfaz o requisito acadêmico.
    """

    def __init__(self, conn: socket.socket, addr: tuple) -> None:
        """Args: conn — socket aceito; addr — (host, port) do peer."""
        super().__init__(name=f"tcp-{addr}", daemon=True)
        self._conn    = conn
        self._addr    = addr
        self._sid: str | None = None        # session_id após login
        self._lock    = threading.Lock()    # protege _send_raw em concorrência
        self._closed  = threading.Event()

    def _send_raw(self, frame: bytes) -> None:
        """Envia bytes NDJSON já codificados (lock para threads do pub/sub)."""
        with self._lock:
            self._conn.sendall(frame)

    def _send(self, **kwargs) -> None:
        """Codifica dict com protocol.encode e envia ao cliente TCP."""
        try:
            self._send_raw(encode(kwargs))
        except OSError:
            pass

    def run(self) -> None:
        """Loop principal da thread: lê NDJSON, trata login/mensagens, faz cleanup."""
        log.info("[+] Conexão TCP de %s", self._addr)

        # Registra callback de envio no dicionário global (necessário para o pub/sub)
        # O session_id ainda não existe; usamos endereço como chave temporária
        tmp_key = str(self._addr)
        with _senders_lock:
            _senders[tmp_key] = self._send_raw

        reader = self._conn.makefile("rb")  # leitura linha a linha (bloqueia até \n)
        try:
            for raw_line in reader:
                if self._closed.is_set() or not raw_line:
                    break

                try:
                    msg = decode(raw_line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self._send(type="error", message="frame JSON inválido")
                    continue

                typ = msg.get("type")

                # ── Antes do login: só aceita login e ping ─────────────────
                if self._sid is None:
                    if typ == "ping":
                        self._send(type="pong", ts=time.time())
                        continue

                    if typ != "login":
                        self._send(type="error", message="envie login primeiro")
                        continue

                    username = str(msg.get("username", "")).strip()[:32]
                    if not username:
                        self._send(type="error", message="username inválido")
                        continue

                    client_id = str(msg.get("client_id", "")).strip()[:64]
                    since = float(msg.get("since", 0) or 0)
                    rejoin = False

                    session_id = uuid.uuid4().hex
                    if client_id:
                        prev = backend.get_client(client_id)
                        if prev and prev["username"] == username:
                            rejoin = True
                        if not backend.reclaim_for_client(client_id, username, session_id):
                            self._send(type="error", message="username já está em uso")
                            continue
                    elif not backend.claim_username(username, session_id):
                        self._send(type="error", message="username já está em uso")
                        continue

                    self._sid = session_id
                    with _senders_lock:
                        del _senders[tmp_key]
                        _senders[session_id] = self._send_raw

                    history = (
                        backend.get_history_since(since)
                        if since > 0
                        else backend.get_history()
                    )
                    users = backend.get_online_users()

                    self._send(
                        type="welcome",
                        session_id=session_id,
                        username=username,
                        history=history,
                        users=users,
                        rejoined=rejoin,
                    )

                    if not rejoin:
                        _publish_event({
                            "type": "user_joined",
                            "username": username,
                            "ts": time.time(),
                            "users": backend.get_online_users(),
                        })
                    log.info("[✔] '%s' %s. Session: %s", username, "retomou" if rejoin else "logou", session_id[:8])
                    continue

                # ── Após login ─────────────────────────────────────────────
                if typ == "message":
                    text = str(msg.get("text", "")).strip()[:500]
                    if not text:
                        continue

                    username = backend.get_username(self._sid)
                    if not username:
                        self._send(type="error", message="sessão expirada — faça login novamente")
                        break

                    entry = {
                        "type": "chat",
                        "id":   uuid.uuid4().hex,
                        "username": username,
                        "text": text,
                        "ts":   time.time(),
                    }
                    backend.append_history(entry)
                    _publish_event(entry)
                    log.info("[%s]: %s", username, text)

                elif typ == "logout":
                    self._closed.set()
                    break

                elif typ == "ping":
                    backend.refresh_session(self._sid)
                    self._send(type="pong", ts=time.time())

                elif typ == "history_since":
                    since = float(msg.get("since", 0) or 0)
                    items = backend.get_history_since(since)
                    self._send(type="history", items=items)

                else:
                    self._send(type="error", message=f"tipo desconhecido: {typ!r}")

        except OSError as exc:
            log.info("Socket encerrado (%s): %s", self._addr, exc)
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

    def _cleanup(self) -> None:
        """Remove sender global e publica user_left se havia login."""
        key = self._sid or str(self._addr)
        with _senders_lock:
            _senders.pop(key, None)

        if self._sid:
            username = backend.remove_session(self._sid)
            if username:
                _publish_event({
                    "type": "user_left",
                    "username": username,
                    "ts": time.time(),
                    "users": backend.get_online_users(),
                })
                log.info("[✖] '%s' desconectou.", username)


# ── HTTP simples para health/ping ─────────────────────────────────────────────

class HealthHandler(BaseHTTPRequestHandler):
    """Responde /health e /ping para keep-alive e monitoramento."""

    def do_GET(self):
        """Responde OK em qualquer GET (health interno na porta TCP+1)."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass  # silencia logs de acesso HTTP


def _run_health_server(port: int) -> None:
    """Sobe HTTP minimal na porta PORT+1 para probes."""
    srv = HTTPServer(("0.0.0.0", port), HealthHandler)
    srv.serve_forever()


# ── Loop principal ─────────────────────────────────────────────────────────────

def main() -> None:
    """Ponto de entrada: Redis, pub/sub, health HTTP e accept loop TCP."""
    log.info("Conectando ao Redis em %s...", REDIS_URL)
    backend.ping()
    log.info("Redis OK.")

    # Thread do subscriber Redis (recebe eventos de outras instâncias)
    backend.start_subscriber(_on_redis_message, stop_event)

    # HTTP de saúde em porta separada (+1)
    health_port = PORT + 1
    threading.Thread(
        target=_run_health_server,
        args=(health_port,),
        name="health-http",
        daemon=True,
    ).start()
    log.info("Health check em http://0.0.0.0:%d/health", health_port)

    # Servidor TCP principal
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(128)
    log.info("Servidor TCP escutando em %s:%d", HOST, PORT)

    while not stop_event.is_set():
        try:
            srv.settimeout(1.0)
            conn, addr = srv.accept()
        except TimeoutError:
            continue
        except OSError:
            break
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        ClientSession(conn, addr).start()  # thread por conexão

    srv.close()
    log.info("Servidor encerrado.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Interrompido pelo usuário.")
        stop_event.set()
