"""InboundDemux: RPC de login não compete com filas SSE."""

import queue

from proxy import InboundDemux


def test_login_rpc_does_not_fan_out() -> None:
    demux = InboundDemux()
    sse = demux.subscribe()
    demux.arm_rpc("login")
    demux.push({"type": "welcome", "username": "alice"})
    assert demux.wait_rpc("login", timeout_s=1.0)["username"] == "alice"
    assert sse.empty()


def test_chat_fans_out_to_sse() -> None:
    demux = InboundDemux()
    sse = demux.subscribe()
    demux.push({"type": "chat", "text": "oi", "username": "alice"})
    assert sse.get_nowait()["text"] == "oi"
