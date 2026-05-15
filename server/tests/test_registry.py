from __future__ import annotations

from server.registry import ClientRegistry


def test_registry_broadcast_skips_exclude() -> None:
    reg = ClientRegistry()
    out_a: list[bytes] = []
    out_b: list[bytes] = []

    def a(frame: bytes) -> None:
        out_a.append(frame)

    def b(frame: bytes) -> None:
        out_b.append(frame)

    reg.add(a)
    reg.add(b)
    reg.broadcast_bytes(b"x\n", exclude=a)
    assert out_a == []
    assert out_b == [b"x\n"]
