"""Analysis model for storing AI vision analysis results."""

from typing import Optional

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.image import Image


class Analysis(Base, UUIDMixin, TimestampMixin):
    """Database model for storing AI vision analysis results.
    
    Attributes:
        id: Unique identifier (UUID)
        image_id: Foreign key to image
        raw_response: Raw JSON response from AI model
        title: Generated title
        subject: Subject description
        character_description: Character details
        environment: Environment description
        art_style: Art style identification
        color_palette: List of colors
        mood: Mood/atmosphere
        genre: Genre classification
        technical_details: Technical information
        artistic_influences: Identified influences
        search_keywords: SEO keywords
        audience_interests: Target audience interests
        model_used: AI model used for analysis
        prompt_version: Version of prompt used
        image: Relationship to image
    """
    
    __tablename__ = "analyses"
    
    image_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("images.id"),
        nullable=False,
        unique=True
    )
    raw_response: Mapped[dict] = mapped_column(JSON, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    character_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    environment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    art_style: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    color_palette: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    mood: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    technical_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artistic_influences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    search_keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    audience_interests: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Relationships
    image: Mapped[Image] = relationship("Image", back_populates="analysis")
