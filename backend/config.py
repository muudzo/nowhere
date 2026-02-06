from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "nowhere-backend"
    REDIS_DSN: str = Field("redis://localhost:6379/0", env="REDIS_DSN")
    POSTGRES_DSN: str = Field(
        "postgresql://postgres:postgres@localhost:5432/nowhere",
        env="POSTGRES_DSN",
    )
    DEVICE_TOKEN_SECRET: str = Field("devsecret", env="DEVICE_TOKEN_SECRET")
    REDIS_TTL_SECONDS: int = Field(60 * 60 * 6, env="REDIS_TTL_SECONDS")

    model_config = {"env_file": ".env"}


_settings = Settings()


def get_settings() -> Settings:
    return _settings


settings = _settings
