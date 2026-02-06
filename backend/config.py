from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "nowhere-backend"
    REDIS_DSN: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_DSN")
    POSTGRES_DSN: str = Field(
        default="sqlite+aiosqlite:///./nowhere.db",
        validation_alias="POSTGRES_DSN",
    )
    DEVICE_TOKEN_SECRET: str = Field(default="devsecret", validation_alias="DEVICE_TOKEN_SECRET")
    REDIS_TTL_SECONDS: int = Field(default=60 * 60 * 6, validation_alias="REDIS_TTL_SECONDS")
    
    # Explicit JWT settings (lowercase to match usage in jwt.py)
    jwt_secret: str = Field(default="devsecret", validation_alias="JWT_SECRET") 
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")

    model_config = ConfigDict(env_file=".env")


_settings = Settings()


def get_settings() -> Settings:
    return _settings


settings = _settings
# Backwards-compatible aliases for older code expecting different names
def _ensure_compat_aliases(s: Settings):
    # provide camel/other-style aliases used across the codebase
    try:
        setattr(s, "postgres_url", getattr(s, "POSTGRES_DSN"))
    except Exception:
        pass
    try:
        setattr(s, "redis_url", getattr(s, "REDIS_DSN"))
    except Exception:
        pass
    try:
        # older code expects `app_name` lowercased
        setattr(s, "app_name", getattr(s, "APP_NAME"))
    except Exception:
        pass
    
    try:
        if not hasattr(s, "jwt_secret"):
            setattr(s, "jwt_secret", getattr(s, "JWT_SECRET"))
        if not hasattr(s, "jwt_algorithm"):
            setattr(s, "jwt_algorithm", getattr(s, "JWT_ALGORITHM"))
    except Exception:
        pass


_ensure_compat_aliases(settings)
