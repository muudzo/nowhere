from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    APP_NAME: str = "nowhere-backend"
    REDIS_DSN: str = Field("redis://localhost:6379/0", env="REDIS_DSN")
    POSTGRES_DSN: str = Field("postgresql://postgres:postgres@localhost:5432/nowhere", env="POSTGRES_DSN")
    DEVICE_TOKEN_SECRET: str = Field("devsecret", env="DEVICE_TOKEN_SECRET")
    REDIS_TTL_SECONDS: int = Field(60 * 60 * 6, env="REDIS_TTL_SECONDS")

    class Config:
        env_file = ".env"


_settings = Settings()


def get_settings() -> Settings:
    return _settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Nowhere"
    debug: bool = False
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "super-secret-key-change-me-in-prod"
    jwt_algorithm: str = "HS256"
    postgres_url: str = "postgresql+asyncpg://user:password@localhost:5432/nowhere"
    
    class Config:
        env_file = ".env"

settings = Settings()
