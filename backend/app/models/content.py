"""Content model for storing generated platform-specific content."""

from enum import Enum

from sqlalchemy import Boolean, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.image import Image


class Platform(str, Enum):
    """Supported social media platforms."""
    ARTSTATION = "artstation"
    X = "x"
    INSTAGRAM = "instagram"
    REDDIT = "reddit"
    DEVIANTART = "deviantart"


class ContentType(str, Enum):
    """Types of generated content."""
    TITLE = "title"
    DESCRIPTION = "description"
    HASHTAGS = "hashtags"
    POST = "post"
    RECOMMENDED_SUBREDDITS = "recommended_subreddits"


class GeneratedContent(Base, UUIDMixin, TimestampMixin):
    """Database model for storing platform-specific generated content.
    
    Attributes:
        id: Unique identifier (UUID)
        image_id: Foreign key to image
        platform: Target platform
        content_type: Type of content
        content: Generated content text
        is_edited: Whether content was manually edited
        prompt_version: Version of prompt used
        image: Relationship to image
    """
    
    __tablename__ = "generated_content"
    
    image_id: Mapped[str] = mapped_column(String(36), ForeignKey("images.id"), nullable=False)
    platform: Mapped[Platform] = mapped_column(String(50), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Relationships
    image: Mapped[Image] = relationship("Image", back_populates="generated_content")
    
    # Unique constraint to ensure one content item per platform/type per image
    __table_args__ = (
        {"sqlite_autoincrement": True}
    )
