"""Fan-out Redis → demux SSE."""

import queue

from proxy import InboundDemux, ProxySession, TCPSession, _fanout_redis_event, _sessions, _sessions_lock


def test_fanout_redis_delivers_chat() -> None:
    demux = InboundDemux()
    tcp = TCPSession(demux, label="u")
    proxy_id = "test-proxy-id"
    with _sessions_lock:
        _sessions[proxy_id] = ProxySession(username="u", demux=demux, tcp=tcp)
    try:
        q = demux.subscribe()
        _fanout_redis_event(
            {
                "type": "chat",
                "id": "1",
                "username": "u",
                "text": "oi",
                "ts": 1.0,
                "_origin": "vm-a",
            }
        )
        ev = q.get_nowait()
        assert ev["text"] == "oi"
        assert "_origin" not in ev
    finally:
        with _sessions_lock:
            _sessions.pop(proxy_id, None)
