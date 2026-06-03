"""Pydantic schemas for prompt-related API operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class PromptBase(BaseModel):
    """Base prompt schema."""
    name: str = Field(..., description="Prompt identifier")
    content: str = Field(..., description="Prompt content")


class PromptCreate(PromptBase):
    """Schema for creating a prompt."""
    version: str | None = Field(None, description="Version string")
    set_active: bool = Field(True, description="Set as active version")


class PromptUpdate(BaseModel):
    """Schema for updating a prompt."""
    content: str = Field(..., description="Updated prompt content")


class PromptResponse(PromptBase):
    """Schema for prompt response."""
    id: str
    version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PromptVersionResponse(BaseModel):
    """Schema for prompt version response."""
    id: str
    name: str
    version: str
    content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PromptListResponse(BaseModel):
    """Schema for prompt list response."""
    prompts: dict[str, list[PromptVersionResponse]]


class PromptReloadRequest(BaseModel):
    """Schema for reloading prompt from file."""
    name: str = Field(..., description="Prompt name to reload")


class PromptSetActiveRequest(BaseModel):
    """Schema for setting active prompt version."""
    name: str = Field(..., description="Prompt name")
    version: str = Field(..., description="Version to set as active")
