"""Analysis repository for database operations."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models import Analysis
from app.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository[Analysis]):
    """Repository for analysis operations."""
    
    def __init__(self, db: Session):
        """Initialize analysis repository.
        
        Args:
            db: Database session
        """
        super().__init__(Analysis, db)
    
    def get_by_image_id(self, image_id: str) -> Optional[Analysis]:
        """Get analysis by image ID.
        
        Args:
            image_id: Image ID
            
        Returns:
            Analysis instance or None
        """
        return (
            self.db.query(Analysis)
            .filter(Analysis.image_id == image_id)
            .first()
        )
    
    def delete_by_image_id(self, image_id: str) -> bool:
        """Delete analysis by image ID.
        
        Args:
            image_id: Image ID
            
        Returns:
            True if deleted, False otherwise
        """
        analysis = self.get_by_image_id(image_id)
        if analysis:
            self.delete(analysis)
            return True
        return False
