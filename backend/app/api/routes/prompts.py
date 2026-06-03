"""API routes for prompt management."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import (
    PromptCreate,
    PromptListResponse,
    PromptReloadRequest,
    PromptResponse,
    PromptSetActiveRequest,
    PromptUpdate,
)
from app.dependencies import get_prompt_repository
from app.services.prompt_service import PromptService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    prompt_repo = Depends(get_prompt_repository)
):
    """List all available prompts.
    
    Args:
        prompt_repo: Prompt repository
        
    Returns:
        List of prompts with their versions
    """
    prompt_service = PromptService(prompt_repo)
    prompts = prompt_service.list_prompts()
    
    # Get versions for each prompt
    prompt_versions = {}
    for prompt_name in prompts.keys():
        versions = prompt_service.get_prompt_versions(prompt_name)
        prompt_versions[prompt_name] = versions
    
    return PromptListResponse(prompts=prompt_versions)


@router.get("/{name}", response_model=PromptResponse)
async def get_prompt(
    name: str,
    prompt_repo = Depends(get_prompt_repository)
):
    """Get the active version of a prompt.
    
    Args:
        name: Prompt name
        prompt_service: Prompt service
        
    Returns:
        Active prompt version
    """
    try:
        prompt_service = PromptService(prompt_repo)
        content = prompt_service.get_prompt_content(name)
        # Return as a response with placeholder version
        return PromptResponse(
            id="00000000-0000-0000-0000-000000000000",  # Placeholder for file-based prompts
            name=name,
            version="file",
            content=content,
            is_active=True,
            created_at=None,
            updated_at=None
        )
    except FileNotFoundError as e:
        logger.error(f"Prompt not found: {name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_create: PromptCreate,
    prompt_repo = Depends(get_prompt_repository)
):
    """Create a new prompt version.
    
    Args:
        prompt_create: Prompt creation data
        db: Database session
        prompt_service: Prompt service
        
    Returns:
        Created prompt version
    """
    try:
        prompt_service = PromptService(prompt_repo)
        prompt = prompt_service.save_prompt_version(
            name=prompt_create.name,
            content=prompt_create.content,
            version=prompt_create.version,
            set_active=prompt_create.set_active
        )
        logger.info(f"Created prompt: {prompt_create.name}")
        return prompt
    except RuntimeError as e:
        logger.error(f"Failed to create prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{name}", response_model=PromptResponse)
async def update_prompt(
    name: str,
    prompt_update: PromptUpdate,
    prompt_repo = Depends(get_prompt_repository)
):
    """Update a prompt (creates new version).
    
    Args:
        name: Prompt name
        prompt_update: Update data
        db: Database session
        prompt_service: Prompt service
        
    Returns:
        New prompt version
    """
    try:
        prompt_service = PromptService(prompt_repo)
        prompt = prompt_service.save_prompt_version(
            name=name,
            content=prompt_update.content,
            set_active=True
        )
        logger.info(f"Updated prompt: {name}")
        return prompt
    except RuntimeError as e:
        logger.error(f"Failed to update prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reload", response_model=PromptResponse)
async def reload_prompt(
    request: PromptReloadRequest,
    prompt_repo = Depends(get_prompt_repository)
):
    """Reload a prompt from file.
    
    Args:
        request: Reload request
        db: Database session
        prompt_service: Prompt service
        
    Returns:
        Reloaded prompt version
    """
    try:
        prompt_service = PromptService(prompt_repo)
        prompt = prompt_service.reload_prompt_from_file(request.name)
        logger.info(f"Reloaded prompt from file: {request.name}")
        return prompt
    except FileNotFoundError as e:
        logger.error(f"Prompt file not found: {request.name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Failed to reload prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/set-active", response_model=PromptResponse)
async def set_active_prompt(
    request: PromptSetActiveRequest,
    prompt_repo = Depends(get_prompt_repository)
):
    """Set a specific prompt version as active.
    
    Args:
        request: Set active request
        db: Database session
        prompt_service: Prompt service
        
    Returns:
        Updated prompt version
    """
    prompt_service = PromptService(prompt_repo)
    prompt = prompt_service.set_active_version(request.name, request.version)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt version not found"
        )
    logger.info(f"Set active version for prompt: {request.name} v{request.version}")
    return prompt
