"""API routes for content generation and management."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import (
    AllContentResponse,
    ContentGenerationRequest,
    ContentResponse,
    ContentUpdate,
)
from app.dependencies import get_content_repository, get_image_repository, get_prompt_repository
from app.models import Platform
from app.services.content_service import ContentGenerationService
from app.services.ollama_client import OllamaClient
from app.services.prompt_service import PromptService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/generate", response_model=list[ContentResponse], status_code=status.HTTP_201_CREATED)
async def generate_content(
    request: ContentGenerationRequest,
    content_repo = Depends(get_content_repository),
    image_repo = Depends(get_image_repository),
    prompt_repo = Depends(get_prompt_repository)
):
    """Generate platform-specific content for an image.
    
    Args:
        request: Content generation request
        db: Database session
        content_service: Content generation service
        
    Returns:
        List of generated content items
    """
    try:
        prompt_service = PromptService(prompt_repo)
        ollama_client = OllamaClient()
        content_service = ContentGenerationService(content_repo, image_repo, prompt_service, ollama_client)
        contents = await content_service.generate_content(
            request.image_id,
            request.platforms
        )
        logger.info(f"Generated content for image: {request.image_id}")
        return contents
    except ValueError as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate content"
        )


@router.get("/{image_id}", response_model=AllContentResponse)
async def get_content(
    image_id: str,
    content_repo = Depends(get_content_repository)
):
    """Get all content for an image.
    
    Args:
        image_id: Image ID
        db: Database session
        content_service: Content generation service
        
    Returns:
        All content for the image
    """
    content_service = ContentGenerationService(content_repo, None, None, None)
    contents = content_service.get_content(image_id)
    
    # Group by platform
    platforms: dict[Platform, list] = {}
    for content in contents:
        if content.platform not in platforms:
            platforms[content.platform] = []
        platforms[content.platform].append(content)
    
    return AllContentResponse(image_id=image_id, platforms=platforms)


@router.get("/{image_id}/{platform}", response_model=list[ContentResponse])
async def get_platform_content(
    image_id: str,
    platform: Platform,
    content_repo = Depends(get_content_repository)
):
    """Get content for a specific platform.
    
    Args:
        image_id: Image ID
        platform: Platform
        db: Database session
        content_service: Content generation service
        
    Returns:
        Content for the platform
    """
    content_service = ContentGenerationService(content_repo, None, None, None)
    contents = content_service.get_platform_content(image_id, platform)
    return contents


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    content_update: ContentUpdate,
    content_repo = Depends(get_content_repository)
):
    """Update content.
    
    Args:
        content_id: Content ID
        content_update: Update data
        db: Database session
        content_service: Content generation service
        
    Returns:
        Updated content
    """
    content_service = ContentGenerationService(content_repo, None, None, None)
    content = content_service.update_content(content_id, content_update.content)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    logger.info(f"Updated content: {content_id}")
    return content


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    image_id: str,
    content_repo = Depends(get_content_repository)
):
    """Delete all content for an image.
    
    Args:
        image_id: Image ID
        db: Database session
        content_service: Content generation service
    """
    content_service = ContentGenerationService(content_repo, None, None, None)
    count = content_service.delete_content(image_id)
    logger.info(f"Deleted {count} content items for image: {image_id}")
