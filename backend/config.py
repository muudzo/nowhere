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
