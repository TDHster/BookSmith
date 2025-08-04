from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    MODEL_NAME: str = "gemini-1.5-pro-latest"
    OUTLINE_FILE: str = "book_outline.xlsx"
    CHAPTERS_DIR: str = "chapters"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings():
    return Settings()

settings = get_settings()