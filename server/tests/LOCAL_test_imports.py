"""LOCAL: verifica se o pacote do servidor importa corretamente (smoke test)."""

from __future__ import annotations


def test_import_server_main() -> None:
    import server.main as m

    assert callable(m.main)
