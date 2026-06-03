"""Pydantic schemas for image-related API operations."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.image import ImageStatus


class ImageBase(BaseModel):
    """Base image schema."""
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the image")


class ImageCreate(ImageBase):
    """Schema for creating a new image."""
    width: int | None = Field(None, description="Image width in pixels")
    height: int | None = Field(None, description="Image height in pixels")


class ImageUpdate(BaseModel):
    """Schema for updating an image."""
    status: ImageStatus | None = None
    error_message: str | None = None


class ImageResponse(ImageBase):
    """Schema for image response."""
    id: str
    original_path: str
    thumbnail_path: str | None
    width: int | None
    height: int | None
    status: ImageStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    """Schema for image list response."""
    images: list[ImageResponse]
    total: int
    skip: int
    limit: int
