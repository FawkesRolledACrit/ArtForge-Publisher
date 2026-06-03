"""Base repository class for common database operations."""

from typing import Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations.
    
    This class provides a generic interface for database operations
    that can be extended by specific repositories.
    
    Attributes:
        model: The SQLAlchemy model class
        db: Database session
    """
    
    def __init__(self, model: type[ModelType], db: Session):
        """Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db
    
    def get(self, id: str) -> Optional[ModelType]:
        """Get a single record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Model instance or None
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """Get all records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, **kwargs) -> ModelType:
        """Create a new record.
        
        Args:
            **kwargs: Model field values
            
        Returns:
            Created model instance
        """
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, db_obj: ModelType, **kwargs) -> ModelType:
        """Update an existing record.
        
        Args:
            db_obj: Model instance to update
            **kwargs: Field values to update
            
        Returns:
            Updated model instance
        """
        for field, value in kwargs.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, db_obj: ModelType) -> None:
        """Delete a record.
        
        Args:
            db_obj: Model instance to delete
        """
        self.db.delete(db_obj)
        self.db.commit()
    
    def count(self) -> int:
        """Count total records.
        
        Returns:
            Total number of records
        """
        return self.db.query(self.model).count()
