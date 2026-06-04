"""API routes for image management."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.schemas import ImageCreate, ImageListResponse, ImageResponse, ImageUpdate
from app.core.database import get_db
from app.dependencies import get_image_repository
from app.models import ImageStatus
from app.services.image_service import ImageService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    image_repo = Depends(get_image_repository)
):
    """Upload a new image.
    
    Args:
        file: Uploaded image file
        db: Database session
        image_repo: Image repository
        
    Returns:
        Created image record
    """
    # Read file content
    file_content = await file.read()
    
    # Create image service and upload
    image_service = ImageService(image_repo)
    
    try:
        image = image_service.create_image(
            file_content=file_content,
            filename=file.filename,
            mime_type=file.content_type
        )
        logger.info(f"Uploaded image: {image.id}")
        return image
    except ValueError as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: str,
    image_repo = Depends(get_image_repository)
):
    """Get image by ID.
    
    Args:
        image_id: Image ID
        db: Database session
        image_repo: Image repository
        
    Returns:
        Image record
    """
    image_service = ImageService(image_repo)
    image = image_service.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    return image


@router.get("", response_model=ImageListResponse)
async def list_images(
    skip: int = 0,
    limit: int = 100,
    status: ImageStatus | None = None,
    db: Session = Depends(get_db),
    image_repo = Depends(get_image_repository)
):
    """List images with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status (optional)
        db: Database session
        image_repo: Image repository
        
    Returns:
        List of images
    """
    image_service = ImageService(image_repo)
    images = image_service.list_images(skip, limit, status)
    total = len(images)
    return ImageListResponse(
        images=images,
        total=total,
        skip=skip,
        limit=limit
    )


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: str,
    image_repo = Depends(get_image_repository)
):
    """Delete an image.
    
    Args:
        image_id: Image ID
        db: Database session
        image_repo: Image repository
    """
    image_service = ImageService(image_repo)
    success = image_service.delete_image(image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    logger.info(f"Deleted image: {image_id}")


@router.patch("/{image_id}", response_model=ImageResponse)
async def update_image(
    image_id: str,
    image_update: ImageUpdate,
    image_repo = Depends(get_image_repository)
):
    """Update image status.
    
    Args:
        image_id: Image ID
        image_update: Update data
        db: Database session
        image_repo: Image repository
        
    Returns:
        Updated image
    """
    image = image_repo.get(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    if image_update.status:
        image_repo.update_status(
            image_id,
            image_update.status,
            image_update.error_message
        )
    
    return image_repo.get(image_id)


@router.get("/{image_id}/file")
async def get_image_file(
    image_id: str,
    image_repo = Depends(get_image_repository)
):
    """Get image file by ID.
    
    Args:
        image_id: Image ID
        image_repo: Image repository
        
    Returns:
        Image file
    """
    image = image_repo.get(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Return the thumbnail if available, otherwise return original
    file_path = image.thumbnail_path if image.thumbnail_path else image.original_path
    
    if not file_path or not Path(file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found"
        )
    
    return FileResponse(file_path)
