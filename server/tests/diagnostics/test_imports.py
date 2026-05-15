"""Verificação rápida de que o pacote do servidor importa sem side effects graves."""

from __future__ import annotations


def test_import_server_main() -> None:
    import server.main as m  # noqa: PLC0415 - import tardio intencional

    assert callable(m.main)
