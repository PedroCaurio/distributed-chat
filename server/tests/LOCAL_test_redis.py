"""LOCAL: teste de integração com Redis real (requer REDIS_URL no ambiente)."""

import os

import pytest

redis = pytest.importorskip("redis")


@pytest.mark.integration
def test_redis_ping() -> None:
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        pytest.skip("Defina REDIS_URL no .env para este teste LOCAL.")
    client = redis.Redis.from_url(url)
    client.ping()
