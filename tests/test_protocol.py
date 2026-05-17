from chatnet.protocol import decode, encode


def test_encode_decode_roundtrip() -> None:
    payload = {"type": "chat", "text": "olá", "username": "ana"}
    raw = encode(payload)
    assert raw.endswith(b"\n")
    assert decode(raw) == payload
