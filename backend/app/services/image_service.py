"""Image service for image management operations."""

from typing import Optional

from app.models import Image, ImageStatus
from app.repositories.image_repository import ImageRepository
from app.utils.image_utils import (
    delete_image_files,
    generate_thumbnail,
    save_uploaded_image,
    validate_image_size,
    validate_image_type,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ImageService:
    """Service for image management operations."""
    
    def __init__(self, image_repo: ImageRepository):
        """Initialize image service.
        
        Args:
            image_repo: Image repository
        """
        self.image_repo = image_repo
    
    def create_image(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str
    ) -> Image:
        """Create a new image record and save file.
        
        Args:
            file_content: Image file content as bytes
            filename: Original filename
            mime_type: MIME type of the image
            
        Returns:
            Created Image instance
            
        Raises:
            ValueError: If image validation fails
        """
        # Validate image type
        if not validate_image_type(mime_type):
            raise ValueError(f"Invalid image type: {mime_type}")
        
        # Validate image size
        if not validate_image_size(len(file_content)):
            max_size_mb = len(file_content) / (1024 * 1024)
            raise ValueError(
                f"Image size exceeds maximum allowed size. "
                f"Size: {max_size_mb:.2f}MB"
            )
        
        # Save image files
        original_path, thumbnail_path, file_size, dimensions = save_uploaded_image(
            file_content, filename, mime_type
        )
        
        # Create database record
        width, height = dimensions if dimensions else (None, None)
        image = self.image_repo.create(
            filename=filename,
            original_path=original_path,
            thumbnail_path=thumbnail_path,
            file_size=file_size,
            width=width,
            height=height,
            mime_type=mime_type,
            status=ImageStatus.UPLOADED
        )
        
        logger.info(f"Created image record: {image.id}")
        return image
    
    def get_image(self, image_id: str) -> Optional[Image]:
        """Get image by ID.
        
        Args:
            image_id: Image ID
            
        Returns:
            Image instance or None
        """
        return self.image_repo.get(image_id)
    
    def list_images(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ImageStatus] = None
    ) -> list[Image]:
        """List images with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status (optional)
            
        Returns:
            List of images
        """
        if status:
            return self.image_repo.get_by_status(status, skip, limit)
        return self.image_repo.get_all(skip, limit)
    
    def delete_image(self, image_id: str) -> bool:
        """Delete image and associated files.
        
        Args:
            image_id: Image ID
            
        Returns:
            True if deleted, False otherwise
        """
        image = self.image_repo.get(image_id)
        if not image:
            return False
        
        # Delete files
        delete_image_files(image.original_path, image.thumbnail_path)
        
        # Delete database record
        self.image_repo.delete(image)
        
        logger.info(f"Deleted image: {image_id}")
        return True
    
    def update_image_status(
        self,
        image_id: str,
        status: ImageStatus,
        error_message: Optional[str] = None
    ) -> Optional[Image]:
        """Update image status.
        
        Args:
            image_id: Image ID
            status: New status
            error_message: Optional error message
            
        Returns:
            Updated image or None
        """
        return self.image_repo.update_status(image_id, status, error_message)
