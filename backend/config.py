from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Nowhere"
    debug: bool = False
    redis_url: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"

settings = Settings()
