"""Smoke check: imports do proxy."""

from __future__ import annotations


def test_import_client_app() -> None:
    import client.app as a  # noqa: PLC0415

    assert callable(a.create_app)
