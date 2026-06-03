"""Image repository for database operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Image, ImageStatus
from app.repositories.base import BaseRepository


class ImageRepository(BaseRepository[Image]):
    """Repository for image operations."""
    
    def __init__(self, db: Session):
        """Initialize image repository.
        
        Args:
            db: Database session
        """
        super().__init__(Image, db)
    
    def get_by_status(self, status: ImageStatus, skip: int = 0, limit: int = 100) -> List[Image]:
        """Get images by status.
        
        Args:
            status: Image status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of images with the specified status
        """
        return (
            self.db.query(Image)
            .filter(Image.status == status)
            .order_by(Image.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_filename(self, filename: str) -> Optional[Image]:
        """Get image by filename.
        
        Args:
            filename: Filename to search for
            
        Returns:
            Image instance or None
        """
        return (
            self.db.query(Image)
            .filter(Image.filename == filename)
            .first()
        )
    
    def update_status(self, image_id: str, status: ImageStatus, error_message: Optional[str] = None) -> Optional[Image]:
        """Update image status.
        
        Args:
            image_id: Image ID
            status: New status
            error_message: Optional error message if status is failed
            
        Returns:
            Updated image instance or None
        """
        image = self.get(image_id)
        if image:
            image.status = status
            if error_message:
                image.error_message = error_message
            else:
                image.error_message = None
            self.db.commit()
            self.db.refresh(image)
        return image
