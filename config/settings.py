from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pydantic import Field

# from pathlib import Path

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    LLM_PROVIDER: str = Field(default="gemini", env="LLM_PROVIDER")  # gemini, openai, etc.

    # GEMINI_API_KEY: str
    # MODEL_NAME: str = "gemini-2.0-flash"
    
    # Gemini-specific settings
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash", env="GEMINI_MODEL")
    
    # OpenAI-specific settings
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4-turbo", env="OPENAI_MODEL")
    
    OUTLINE_FILE: str = "book_outline.xlsx"
    CHAPTERS_DIR: str = "chapters"
    DEFAULT_LANGUAGE: str
    LOG_LEVEL: str = "INFO"
    BOOKS_DIR: str = "books"

def get_settings():
    return Settings()

settings = get_settings()