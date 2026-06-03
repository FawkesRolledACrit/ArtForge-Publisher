"""Prompt repository for database operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import PromptVersion
from app.repositories.base import BaseRepository


class PromptRepository(BaseRepository[PromptVersion]):
    """Repository for prompt version operations."""
    
    def __init__(self, db: Session):
        """Initialize prompt repository.
        
        Args:
            db: Database session
        """
        super().__init__(PromptVersion, db)
    
    def get_by_name(self, name: str) -> List[PromptVersion]:
        """Get all versions of a prompt by name.
        
        Args:
            name: Prompt name
            
        Returns:
            List of prompt versions
        """
        return (
            self.db.query(PromptVersion)
            .filter(PromptVersion.name == name)
            .order_by(PromptVersion.created_at.desc())
            .all()
        )
    
    def get_active_by_name(self, name: str) -> Optional[PromptVersion]:
        """Get the active version of a prompt by name.
        
        Args:
            name: Prompt name
            
        Returns:
            Active prompt version or None
        """
        return (
            self.db.query(PromptVersion)
            .filter(PromptVersion.name == name, PromptVersion.is_active == True)
            .first()
        )
    
    def set_active(self, name: str, version: str) -> Optional[PromptVersion]:
        """Set a specific version as active for a prompt.
        
        Args:
            name: Prompt name
            version: Version string
            
        Returns:
            Updated prompt version or None
        """
        # Deactivate all versions for this prompt
        self.db.query(PromptVersion).filter(
            PromptVersion.name == name
        ).update({"is_active": False})
        
        # Activate the specified version
        prompt_version = (
            self.db.query(PromptVersion)
            .filter(
                PromptVersion.name == name,
                PromptVersion.version == version
            )
            .first()
        )
        
        if prompt_version:
            prompt_version.is_active = True
            self.db.commit()
            self.db.refresh(prompt_version)
        
        return prompt_version
    
    def get_latest_version(self, name: str) -> Optional[PromptVersion]:
        """Get the latest version of a prompt by name.
        
        Args:
            name: Prompt name
            
        Returns:
            Latest prompt version or None
        """
        return (
            self.db.query(PromptVersion)
            .filter(PromptVersion.name == name)
            .order_by(PromptVersion.created_at.desc())
            .first()
        )
