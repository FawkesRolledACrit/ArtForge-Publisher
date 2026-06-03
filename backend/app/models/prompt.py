"""Prompt model for storing prompt versions."""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class PromptVersion(Base, UUIDMixin, TimestampMixin):
    """Database model for storing prompt template versions.
    
    This enables tracking prompt changes over time and comparing
    the effectiveness of different prompt versions.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Prompt identifier (e.g., 'vision_analysis')
        version: Version number
        content: Prompt template content
        is_active: Whether this is the currently active version
    """
    
    __tablename__ = "prompt_versions"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
