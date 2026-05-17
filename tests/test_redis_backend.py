from __future__ import annotations

from chatnet.redis_backend import RedisBackend


def test_claim_and_drop_clears_client_binding(backend: RedisBackend) -> None:
    backend.reclaim_for_client("browser-1", "ana", "sess-a")
    assert backend.get_client("browser-1") == {
        "session_id": "sess-a",
        "username": "ana",
    }

    backend.drop_session_keys("sess-a")
    assert backend.get_client("browser-1") is None
    assert backend.get_username("sess-a") is None


def test_reload_same_client_new_username(backend: RedisBackend) -> None:
    assert backend.reclaim_for_client("browser-1", "ana", "sess-1")
    assert backend.reclaim_for_client("browser-1", "bob", "sess-2")

    assert backend.get_client("browser-1") == {
        "session_id": "sess-2",
        "username": "bob",
    }
    assert backend.get_username("sess-2") == "bob"
    assert backend.get_username("sess-1") is None


def test_reload_same_client_same_username(backend: RedisBackend) -> None:
    assert backend.reclaim_for_client("browser-1", "ana", "sess-1")
    assert backend.reclaim_for_client("browser-1", "ana", "sess-2")

    assert backend.get_client("browser-1")["session_id"] == "sess-2"
    assert backend.get_online_users() == ["ana"]


def test_second_browser_cannot_steal_live_username(backend: RedisBackend) -> None:
    assert backend.reclaim_for_client("browser-1", "ana", "sess-1")
    assert not backend.reclaim_for_client("browser-2", "ana", "sess-2")


def test_history_since_filters_by_timestamp(backend: RedisBackend) -> None:
    backend.append_history(
        {"type": "chat", "id": "1", "username": "ana", "text": "a", "ts": 10.0}
    )
    backend.append_history(
        {"type": "chat", "id": "2", "username": "bob", "text": "b", "ts": 20.0}
    )
    items = backend.get_history_since(15.0)
    assert len(items) == 1
    assert items[0]["text"] == "b"
