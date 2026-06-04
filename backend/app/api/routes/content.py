"""API routes for content generation and management."""

import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

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


@router.get("/generate/stream")
async def generate_content_stream(
    image_id: str,
    platforms: str = None,  # Comma-separated list of platforms
    content_repo = Depends(get_content_repository),
    image_repo = Depends(get_image_repository),
    prompt_repo = Depends(get_prompt_repository)
):
    """Generate platform-specific content with streaming response.
    
    Args:
        image_id: Image ID
        platforms: Comma-separated list of platforms
        content_repo: Content repository
        image_repo: Image repository
        prompt_repo: Prompt repository
        
    Returns:
        Streaming response with NDJSON chunks
    """
    async def event_generator():
        try:
            # Get image
            image = image_repo.get(image_id)
            if not image:
                yield f"data: {json.dumps({'error': 'Image not found'})}\n\n"
                return
            
            # Parse platforms from query parameter
            from app.models import Platform
            platform_list = []
            if platforms:
                for platform_str in platforms.split(','):
                    try:
                        platform_list.append(Platform(platform_str.strip().capitalize()))
                    except ValueError:
                        continue
            
            if not platform_list:
                yield f"data: {json.dumps({'error': 'No valid platforms specified'})}\n\n"
                return
            
            # Stream content generation for each platform
            prompt_service = PromptService(prompt_repo)
            ollama_client = OllamaClient()
            
            for platform in platform_list:
                try:
                    # Get the prompt for this platform
                    prompt = prompt_service.get_prompt_content(f"{platform.lower()}_content")
                    if not prompt:
                        yield f"data: {json.dumps({'error': f'Prompt not found for {platform}'})}\n\n"
                        continue
                    
                    # Stream generation from Ollama
                    yield f"data: {json.dumps({'platform': platform, 'status': 'Generating'})}\n\n"
                    async for chunk in ollama_client.generate_content_stream(prompt):
                        yield f"data: {json.dumps({'platform': platform, 'content': chunk})}\n\n"
                
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e), 'platform': platform})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming content generation error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
