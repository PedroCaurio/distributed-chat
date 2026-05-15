from __future__ import annotations

from common.protocol import MessageType

from client.inbound import InboundDemux


def test_login_routes_welcome_to_waiter() -> None:
    d = InboundDemux()
    d.arm_login_wait()
    d.push({"type": MessageType.WELCOME.value, "username": "u1"})
    msg = d.wait_login_response(timeout_s=1.0)
    assert msg["type"] == MessageType.WELCOME.value


def test_chat_goes_to_sse_when_not_armed() -> None:
    d = InboundDemux()
    d.push({"type": MessageType.CHAT.value, "username": "a", "text": "hi"})
    msg = d.sse_iter().get(timeout=1.0)
    assert msg["text"] == "hi"
