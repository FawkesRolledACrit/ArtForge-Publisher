"""Prompt service for managing prompt templates."""

import hashlib
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings
from app.models import PromptVersion
from app.repositories.prompt_repository import PromptRepository
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class PromptService:
    """Service for managing prompt templates and versions.
    
    This service handles loading prompts from files, tracking versions,
    and managing the active version for each prompt.
    """
    
    def __init__(self, prompt_repo: Optional[PromptRepository] = None):
        """Initialize prompt service.
        
        Args:
            prompt_repo: Prompt repository (optional for testing)
        """
        self.prompt_repo = prompt_repo
        self.prompts_path = settings.PROMPTS_PATH
    
    def load_prompt_from_file(self, prompt_name: str) -> str:
        """Load a prompt template from file.
        
        Args:
            prompt_name: Name of the prompt (without .txt extension)
            
        Returns:
            Prompt content as string
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompt_file = self.prompts_path / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        with open(prompt_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        logger.info(f"Loaded prompt from file: {prompt_name}")
        return content
    
    def get_prompt_content(self, prompt_name: str) -> str:
        """Get the active prompt content for a given prompt name.
        
        This loads from the active version in the database, or falls back
        to the file if no database version exists.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Prompt content as string
        """
        if self.prompt_repo:
            active_version = self.prompt_repo.get_active_by_name(prompt_name)
            if active_version:
                logger.info(f"Using active database version for prompt: {prompt_name}")
                return active_version.content
        
        # Fallback to file
        return self.load_prompt_from_file(prompt_name)
    
    def save_prompt_version(
        self,
        name: str,
        content: str,
        version: Optional[str] = None,
        set_active: bool = True
    ) -> PromptVersion:
        """Save a new prompt version to the database.
        
        Args:
            name: Prompt name
            content: Prompt content
            version: Version string (auto-generated if not provided)
            set_active: Whether to set this as the active version
            
        Returns:
            Created PromptVersion instance
        """
        if not self.prompt_repo:
            raise RuntimeError("Prompt repository not initialized")
        
        # Generate version hash if not provided
        if version is None:
            version = self._generate_version_hash(content)
        
        # Create new version
        prompt_version = self.prompt_repo.create(
            name=name,
            version=version,
            content=content,
            is_active=set_active
        )
        
        # Deactivate other versions if this one is active
        if set_active:
            self.prompt_repo.set_active(name, version)
        
        logger.info(f"Saved prompt version: {name} v{version}")
        return prompt_version
    
    def reload_prompt_from_file(self, prompt_name: str) -> PromptVersion:
        """Reload a prompt from file and save as new version.
        
        This is useful when you've edited a prompt file and want to
        update the database with the new content.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Created PromptVersion instance
        """
        content = self.load_prompt_from_file(prompt_name)
        return self.save_prompt_version(prompt_name, content)
    
    def list_prompts(self) -> Dict[str, str]:
        """List all available prompt templates from files.
        
        Returns:
            Dictionary mapping prompt names to their file paths
        """
        prompts = {}
        
        if not self.prompts_path.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_path}")
            return prompts
        
        for prompt_file in self.prompts_path.glob("*.txt"):
            name = prompt_file.stem
            prompts[name] = str(prompt_file)
        
        logger.info(f"Found {len(prompts)} prompt templates")
        return prompts
    
    def get_prompt_versions(self, prompt_name: str) -> list[PromptVersion]:
        """Get all versions of a prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            List of prompt versions
        """
        if not self.prompt_repo:
            raise RuntimeError("Prompt repository not initialized")
        
        return self.prompt_repo.get_by_name(prompt_name)
    
    def set_active_version(self, prompt_name: str, version: str) -> Optional[PromptVersion]:
        """Set a specific version as active.
        
        Args:
            prompt_name: Name of the prompt
            version: Version string
            
        Returns:
            Updated prompt version or None
        """
        if not self.prompt_repo:
            raise RuntimeError("Prompt repository not initialized")
        
        return self.prompt_repo.set_active(prompt_name, version)
    
    def _generate_version_hash(self, content: str) -> str:
        """Generate a version hash from content.
        
        Args:
            content: Prompt content
            
        Returns:
            Hash string for version identification
        """
        return hashlib.md5(content.encode()).hexdigest()[:8]
