import os

import pytest

redis = pytest.importorskip("redis")


@pytest.mark.integration
def test_redis_ping_integration() -> None:
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        pytest.skip("Defina REDIS_URL para executar este diagnóstico.")
    client = redis.Redis.from_url(url)
    client.ping()
