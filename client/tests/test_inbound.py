"""Testes do demux de entrada TCP."""

from client.inbound import InboundDemux
from common.protocol import MessageType


def test_login_rpc_routes_welcome() -> None:
    demux = InboundDemux()
    demux.arm_rpc("login")
    demux.push({"type": MessageType.WELCOME.value, "username": "ana"})
    resp = demux.wait_rpc("login", timeout_s=1.0)
    assert resp["username"] == "ana"


def test_chat_fan_out_to_all_sse_subscribers() -> None:
    demux = InboundDemux()
    q1 = demux.subscribe()
    q2 = demux.subscribe()
    demux.push({"type": MessageType.CHAT.value, "text": "oi", "id": "1"})
    assert q1.get(timeout=1.0)["text"] == "oi"
    assert q2.get(timeout=1.0)["text"] == "oi"


def test_history_rpc() -> None:
    demux = InboundDemux()
    demux.arm_rpc("history")
    demux.push({"type": MessageType.HISTORY.value, "messages": [{"id": "1"}]})
    resp = demux.wait_rpc("history", timeout_s=1.0)
    assert len(resp["messages"]) == 1
