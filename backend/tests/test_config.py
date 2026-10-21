from app.config import Settings


def test_render_postgres_url_uses_psycopg_driver() -> None:
    settings = Settings(
        database_url="postgres://planner:secret@db.example.test/eventora"
    )
    assert settings.sqlalchemy_url == (
        "postgresql+psycopg://planner:secret@db.example.test/eventora"
    )


def test_postgresql_url_uses_psycopg_driver() -> None:
    settings = Settings(
        database_url="postgresql://planner:secret@db.example.test/eventora"
    )
    assert settings.sqlalchemy_url == (
        "postgresql+psycopg://planner:secret@db.example.test/eventora"
    )


def test_local_database_defaults_to_sqlite() -> None:
    settings = Settings(database_url="")
    assert settings.sqlalchemy_url.startswith("sqlite:///")
