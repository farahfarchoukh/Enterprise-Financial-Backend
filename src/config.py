from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Kudwa AI Financial System"
    OPENAI_API_KEY: str
    GROQ_API_KEY: str
    ADMIN_API_KEY: str
    DATABASE_URL: str
    AI_MODEL: str = "gpt-3.5-turbo"
    LOG_LEVEL: str = "INFO" 




    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()