"""Configuration management for ArtForge Publisher."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Attributes:
        PROJECT_NAME: Application name
        PROJECT_DESCRIPTION: Application description
        VERSION: Application version
        API_V1_PREFIX: API version prefix
        ALLOWED_ORIGINS: CORS allowed origins
        DATABASE_URL: Database connection URL
        LM_STUDIO_ENDPOINT: LM Studio API endpoint
        LM_STUDIO_MODEL: Model name to use
        MAX_IMAGE_SIZE_MB: Maximum image upload size in MB
        STORAGE_PATH: Base path for file storage
        PROMPTS_PATH: Path to prompt templates
        LOG_LEVEL: Logging level
    """
    
    # Application metadata
    PROJECT_NAME: str = "ArtForge Publisher"
    PROJECT_DESCRIPTION: str = "Local-first AI-powered art publishing assistant"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./artforge.db"
    
    # Ollama settings
    OLLAMA_ENDPOINT: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5vl:latest"
    OLLAMA_TIMEOUT: int = 300  # seconds (5 minutes for vision tasks)
    
    # File upload settings
    MAX_IMAGE_SIZE_MB: int = 50
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/tiff"
    ]
    
    # Storage paths
    STORAGE_PATH: Path = Path("./storage")
    IMAGES_PATH: Path = STORAGE_PATH / "images"
    THUMBNAILS_PATH: Path = STORAGE_PATH / "thumbnails"
    
    # Prompt settings
    PROMPTS_PATH: Path = Path("./prompts")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        """Initialize settings and create storage directories if needed."""
        super().__init__(**kwargs)
        # Ensure storage directories exist
        self.IMAGES_PATH.mkdir(parents=True, exist_ok=True)
        self.THUMBNAILS_PATH.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Cached Settings instance.
    """
    return Settings()


# Global settings instance
settings = get_settings()
