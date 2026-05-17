from __future__ import annotations

import fakeredis
import pytest

from redis_backend import RedisBackend


@pytest.fixture
def backend() -> RedisBackend:
  client = fakeredis.FakeRedis(decode_responses=True)
  return RedisBackend("redis://fake", client=client)
