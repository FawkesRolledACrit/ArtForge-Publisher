"""Pydantic schemas for content-related API operations."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.content import ContentType, Platform


class ContentBase(BaseModel):
    """Base content schema."""
    platform: Platform = Field(..., description="Target platform")
    content_type: ContentType = Field(..., description="Type of content")
    content: str = Field(..., description="Generated content")
    prompt_version: str = Field(..., description="Version of prompt used")


class ContentCreate(ContentBase):
    """Schema for creating content."""
    image_id: str = Field(..., description="Image ID")


class ContentUpdate(BaseModel):
    """Schema for updating content."""
    content: str = Field(..., description="Updated content")
    is_edited: bool = Field(True, description="Mark as manually edited")


class ContentResponse(ContentBase):
    """Schema for content response."""
    id: str
    image_id: str
    is_edited: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContentGenerationRequest(BaseModel):
    """Schema for requesting content generation."""
    image_id: str = Field(..., description="Image ID")
    platforms: list[Platform] = Field(
        default_factory=lambda: [Platform.ARTSTATION, Platform.X, Platform.INSTAGRAM, Platform.REDDIT, Platform.DEVIANTART],
        description="Platforms to generate content for"
    )


class PlatformContentResponse(BaseModel):
    """Schema for platform-specific content response."""
    platform: Platform
    contents: dict[ContentType, str]


class AllContentResponse(BaseModel):
    """Schema for all generated content for an image."""
    image_id: str
    platforms: dict[Platform, list[ContentResponse]]
