from protocol import decode, encode


def test_encode_decode_roundtrip() -> None:
    payload = {"type": "ping", "ts": 1.23}
    line = encode(payload)
    assert line.endswith(b"\n")
    assert decode(line) == payload


def test_decode_strips_newline() -> None:
    raw = b'{"ok":true}\r\n'
    assert decode(raw) == {"ok": True}
