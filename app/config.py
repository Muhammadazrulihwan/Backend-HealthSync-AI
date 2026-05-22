from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Gemini AI
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    MAX_TOKENS: int = 8192

    # App 
    APP_NAME: str = "AI-Powered Healthcare Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    #  Database
    DATABASE_URL: str = "sqlite:///./healthcare.db"

    #  CORS 
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
