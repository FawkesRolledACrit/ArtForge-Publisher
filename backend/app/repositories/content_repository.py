"""Content repository for database operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import ContentType, GeneratedContent, Platform
from app.repositories.base import BaseRepository


class ContentRepository(BaseRepository[GeneratedContent]):
    """Repository for content operations."""
    
    def __init__(self, db: Session):
        """Initialize content repository.
        
        Args:
            db: Database session
        """
        super().__init__(GeneratedContent, db)
    
    def get_by_image_id(self, image_id: str) -> List[GeneratedContent]:
        """Get all content for an image.
        
        Args:
            image_id: Image ID
            
        Returns:
            List of content items
        """
        return (
            self.db.query(GeneratedContent)
            .filter(GeneratedContent.image_id == image_id)
            .all()
        )
    
    def get_by_image_and_platform(
        self,
        image_id: str,
        platform: Platform
    ) -> List[GeneratedContent]:
        """Get content for an image and platform.
        
        Args:
            image_id: Image ID
            platform: Platform
            
        Returns:
            List of content items for the platform
        """
        return (
            self.db.query(GeneratedContent)
            .filter(
                GeneratedContent.image_id == image_id,
                GeneratedContent.platform == platform
            )
            .all()
        )
    
    def get_by_image_platform_and_type(
        self,
        image_id: str,
        platform: Platform,
        content_type: ContentType
    ) -> Optional[GeneratedContent]:
        """Get specific content for an image, platform, and type.
        
        Args:
            image_id: Image ID
            platform: Platform
            content_type: Content type
            
        Returns:
            Content item or None
        """
        return (
            self.db.query(GeneratedContent)
            .filter(
                GeneratedContent.image_id == image_id,
                GeneratedContent.platform == platform,
                GeneratedContent.content_type == content_type
            )
            .first()
        )
    
    def delete_by_image_id(self, image_id: str) -> int:
        """Delete all content for an image.
        
        Args:
            image_id: Image ID
            
        Returns:
            Number of deleted items
        """
        count = (
            self.db.query(GeneratedContent)
            .filter(GeneratedContent.image_id == image_id)
            .delete()
        )
        self.db.commit()
        return count
