"""LOCAL: verifica se o cliente HTTP importa corretamente (smoke test)."""


def test_import_client_app() -> None:
    from client.app import create_app

    app = create_app()
    assert app.title == "Distributed Chat Client"
