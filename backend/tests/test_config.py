from app.core.config import Settings


def test_cors_origins_accepts_comma_separated_environment_value(monkeypatch) -> None:
    monkeypatch.setenv(
        "SMARTDISPO_CORS_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080",
    )
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://smartdispo:smartdispo@postgres:5432/smartdispo",
        jwt_secret="unit-test-secret-at-least-32-characters",
    )

    assert settings.cors_origins == [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
