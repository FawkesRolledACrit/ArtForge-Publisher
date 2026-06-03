"""Pydantic schemas for analysis-related API operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisBase(BaseModel):
    """Base analysis schema."""
    raw_response: dict = Field(default={}, description="Raw JSON response from AI model")
    model_used: str = Field(default="manual", description="AI model used for analysis")
    prompt_version: str = Field(default="manual", description="Version of prompt used")


class AnalysisCreate(AnalysisBase):
    """Schema for creating analysis."""
    image_id: str = Field(..., description="Image ID")


class AnalysisUpdate(BaseModel):
    """Schema for updating analysis."""
    image_id: str | None = None
    title: str | None = None
    subject: str | None = None
    character_description: str | None = None
    environment: str | None = None
    art_style: str | None = None
    color_palette: list[str] | None = None
    mood: str | None = None
    genre: str | None = None
    technical_details: str | None = None
    artistic_influences: str | None = None
    search_keywords: list[str] | None = None
    audience_interests: list[str] | None = None


class AnalysisResponse(AnalysisBase):
    """Schema for analysis response."""
    id: str
    image_id: str
    title: str | None
    subject: str | None
    character_description: str | None
    environment: str | None
    art_style: str | None
    color_palette: list[str]
    mood: str | None
    genre: str | None
    technical_details: str | None
    artistic_influences: str | None
    search_keywords: list[str]
    audience_interests: list[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    """Schema for requesting analysis."""
    image_id: str = Field(..., description="Image ID to analyze")
