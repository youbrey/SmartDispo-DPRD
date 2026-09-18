from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_prefix="SMARTDISPO_", extra="ignore")

    env: str = "development"
    database_url: str
    jwt_secret: str = Field(min_length=32)
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    # NoDecode keeps comma-separated deployment values from being treated as JSON
    # before the validator below can normalize them.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    template_dir: str = "../templates"
    template_upload_dir: str = "./storage/templates"
    generated_dir: str = "./generated"
    attachment_dir: str = "./storage/attachments"
    max_attachment_bytes: int = 10 * 1024 * 1024
    sips_api_key: str = ""
    firebase_project_id: str = ""
    firebase_service_account_file: str = ""
    push_poll_seconds: int = Field(default=5, ge=1, le=300)
    redis_url: str = "redis://redis:6379/0"
    api_rate_limit_per_minute: int = Field(default=240, ge=10, le=10000)
    login_rate_limit_per_minute: int = Field(default=10, ge=3, le=1000)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
