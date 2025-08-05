from pydantic_settings import BaseSettings
from pydantic import ConfigDict
# from pathlib import Path

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    GEMINI_API_KEY: str
    MODEL_NAME: str = "gemini-2.0-flash"
    OUTLINE_FILE: str = "book_outline.xlsx"
    CHAPTERS_DIR: str = "chapters"
    DEFAULT_LANGUAGE: str
    LOG_LEVEL: str = "INFO"
    BOOKS_DIR: str = "books"

def get_settings():
    return Settings()

settings = get_settings()