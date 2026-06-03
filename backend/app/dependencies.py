"""Dependency injection for services and repositories."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.base import BaseRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.content_repository import ContentRepository
from app.repositories.prompt_repository import PromptRepository


def get_image_repository(db: Session = Depends(get_db)) -> ImageRepository:
    """Get image repository instance.
    
    Args:
        db: Database session
        
    Returns:
        ImageRepository instance
    """
    return ImageRepository(db)


def get_analysis_repository(db: Session = Depends(get_db)) -> AnalysisRepository:
    """Get analysis repository instance.
    
    Args:
        db: Database session
        
    Returns:
        AnalysisRepository instance
    """
    return AnalysisRepository(db)


def get_content_repository(db: Session = Depends(get_db)) -> ContentRepository:
    """Get content repository instance.
    
    Args:
        db: Database session
        
    Returns:
        ContentRepository instance
    """
    return ContentRepository(db)


def get_prompt_repository(db: Session = Depends(get_db)) -> PromptRepository:
    """Get prompt repository instance.
    
    Args:
        db: Database session
        
    Returns:
        PromptRepository instance
    """
    return PromptRepository(db)


def get_image_service(
    image_repo = Depends(get_image_repository)
):
    """Get image service instance.
    
    Args:
        image_repo: Image repository (optional, for testing)
        
    Returns:
        ImageService instance
    """
    from app.services.image_service import ImageService
    return ImageService(image_repo)


def get_analysis_service(
    analysis_repo = Depends(get_analysis_repository),
    image_repo = Depends(get_image_repository),
    prompt_repo = Depends(get_prompt_repository)
):
    """Get analysis service instance.
    
    Args:
        analysis_repo: Analysis repository (optional)
        image_repo: Image repository (optional)
        prompt_repo: Prompt repository (optional)
        
    Returns:
        AnalysisService instance
    """
    from app.services.analysis_service import AnalysisService
    from app.services.ollama_client import OllamaClient
    from app.services.prompt_service import PromptService
    prompt_service = PromptService(prompt_repo)
    ollama_client = OllamaClient()
    return AnalysisService(analysis_repo, image_repo, prompt_service, ollama_client)


def get_content_service(
    content_repo = Depends(get_content_repository),
    image_repo = Depends(get_image_repository),
    prompt_repo = Depends(get_prompt_repository)
):
    """Get content service instance.
    
    Args:
        content_repo: Content repository (optional)
        image_repo: Image repository (optional)
        prompt_repo: Prompt repository (optional)
        
    Returns:
        ContentService instance
    """
    from app.services.content_service import ContentGenerationService
    from app.services.ollama_client import OllamaClient
    from app.services.prompt_service import PromptService
    prompt_service = PromptService(prompt_repo)
    ollama_client = OllamaClient()
    return ContentGenerationService(content_repo, image_repo, prompt_service, ollama_client)


def get_prompt_service(
    prompt_repo = Depends(get_prompt_repository)
):
    """Get prompt service instance.
    
    Args:
        prompt_repo: Prompt repository (optional)
        
    Returns:
        PromptService instance
    """
    from app.services.prompt_service import PromptService
    return PromptService(prompt_repo)
