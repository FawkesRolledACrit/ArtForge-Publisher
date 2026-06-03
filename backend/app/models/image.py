"""Image model for storing artwork metadata."""

from enum import Enum
from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ImageStatus(str, Enum):
    """Status enum for image processing states."""
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class Image(Base, UUIDMixin, TimestampMixin):
    """Database model for storing artwork images.
    
    Attributes:
        id: Unique identifier (UUID)
        filename: Original filename
        original_path: File system path to original image
        thumbnail_path: File system path to thumbnail
        file_size: File size in bytes
        width: Image width in pixels
        height: Image height in pixels
        mime_type: MIME type of the image
        status: Current processing status
        error_message: Error message if processing failed
        analysis: Relationship to analysis results
        generated_content: Relationship to generated content
    """
    
    __tablename__ = "images"
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ImageStatus] = mapped_column(
        String(50),
        default=ImageStatus.UPLOADED,
        nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship(
        "Analysis",
        back_populates="image",
        uselist=False,
        cascade="all, delete-orphan"
    )
    generated_content: Mapped[list["GeneratedContent"]] = relationship(
        "GeneratedContent",
        back_populates="image",
        cascade="all, delete-orphan"
    )
