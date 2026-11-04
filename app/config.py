"""Application configuration settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    APP_NAME: str = "Popy — Asistente Virtual"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # OpenAI / LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.7

    # Wompi (payment gateway)
    WOMPI_PUBLIC_KEY: Optional[str] = None
    WOMPI_PRIVATE_KEY: Optional[str] = None
    WOMPI_INTEGRITY_SECRET: Optional[str] = None
    WOMPI_EVENTS_SECRET: Optional[str] = None
    WOMPI_BASE_URL: str = "https://sandbox.wompi.co/v1"


settings = Settings()
