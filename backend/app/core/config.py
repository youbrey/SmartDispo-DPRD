from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_prefix="SMARTDISPO_", extra="ignore")

    env: str = "development"
    database_url: str
    jwt_secret: str = Field(min_length=32)
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    template_dir: str = "../templates"
    template_upload_dir: str = "./storage/templates"
    generated_dir: str = "./generated"
    attachment_dir: str = "./storage/attachments"
    max_attachment_bytes: int = 10 * 1024 * 1024
    sips_api_key: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
