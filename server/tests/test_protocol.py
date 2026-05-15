from common.protocol import MessageType, decode_line, encode_line


def test_encode_decode_roundtrip() -> None:
    payload = {"type": MessageType.PING.value, "ts": 1.23}
    line = encode_line(payload)
    assert line.endswith(b"\n")
    assert decode_line(line) == payload


def test_decode_strips_newline() -> None:
    raw = b'{"ok":true}\r\n'
    assert decode_line(raw) == {"ok": True}
