"""Analysis service for image analysis operations."""

import json

from app.models import Analysis, Image, ImageStatus
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.image_repository import ImageRepository
from app.services.ollama_client import OllamaClient
from app.services.prompt_service import PromptService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class AnalysisService:
    """Service for image analysis operations."""
    
    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        image_repo: ImageRepository,
        prompt_service: PromptService,
        ollama_client: OllamaClient | None = None
    ):
        """Initialize analysis service.
        
        Args:
            analysis_repo: Analysis repository
            image_repo: Image repository
            prompt_service: Prompt service
            ollama_client: Ollama client (optional, for testing)
        """
        self.analysis_repo = analysis_repo
        self.image_repo = image_repo
        self.prompt_service = prompt_service
        self.ollama_client = ollama_client or OllamaClient()
    
    async def analyze_image(self, image_id: str) -> Analysis:
        """Analyze an image using the vision model.
        
        Args:
            image_id: Image ID to analyze
            
        Returns:
            Created Analysis instance
            
        Raises:
            ValueError: If image not found or already analyzed
            RuntimeError: If Ollama is unavailable
        """
        # Get image
        image = self.image_repo.get(image_id)
        if not image:
            raise ValueError(f"Image not found: {image_id}")
        
        # Check if already analyzed
        existing_analysis = self.analysis_repo.get_by_image_id(image_id)
        if existing_analysis:
            logger.info(f"Image already analyzed: {image_id}")
            return existing_analysis
        
        # Update image status to analyzing
        self.image_repo.update_status(image_id, ImageStatus.ANALYZING)
        
        try:
            # Get vision analysis prompt
            prompt = self.prompt_service.get_prompt_content("vision_analysis")
            prompt_version = self.prompt_service._generate_version_hash(prompt)
            
            # Use the correct image path from the database
            image_path = image.original_path
            logger.info(f"Image ID: {image_id}")
            logger.info(f"Image original_path from database: {image_path}")
            logger.info(f"Image file_name from database: {image.filename}")
            
            # Check if the file exists
            import os
            if not os.path.exists(image_path):
                logger.error(f"Image file does not exist at path: {image_path}")
                # Try the storage path as fallback
                from app.core.config import settings
                storage_path = settings.IMAGES_PATH / f"{image_id}.webp"
                logger.info(f"Trying storage path: {storage_path}")
                if storage_path.exists():
                    image_path = str(storage_path)
                    logger.info(f"Using storage path instead")
                else:
                    raise ValueError(f"Image file not found at either path")
            
            logger.info(f"Final image path for Ollama: {image_path}")
            
            # Send to Ollama
            response = await self.ollama_client.analyze_image(image_path, prompt)
            
            # Parse JSON response from Ollama
            try:
                content = response["message"]["content"]
                # Strip markdown code blocks if present
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()
                
                # Remove control characters and fix newlines in JSON
                lines = content.split('\n')
                cleaned_lines = []
                in_string = False
                escape_next = False
                
                for line in lines:
                    # Skip empty lines
                    if not line.strip() and not in_string:
                        continue
                    
                    # Process line character by character to handle newlines in strings
                    processed_line = []
                    for char in line:
                        if escape_next:
                            processed_line.append(char)
                            escape_next = False
                        elif char == '\\':
                            processed_line.append(char)
                            escape_next = True
                        elif char == '"':
                            processed_line.append(char)
                            in_string = not in_string
                        elif char == '\n' and in_string:
                            processed_line.append('\\n')
                        else:
                            processed_line.append(char)
                    
                    cleaned_lines.append(''.join(processed_line))
                
                content = '\n'.join(cleaned_lines)
                analysis_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse analysis response as JSON: {e}")
                logger.error(f"Response content: {response.get('message', {}).get('content', '')[:500]}")
                raise ValueError("Invalid JSON response from vision model")
            except KeyError as e:
                logger.error(f"Missing expected key in Ollama response: {e}")
                logger.error(f"Response structure: {response}")
                raise ValueError("Invalid response structure from Ollama")
            
            # Create analysis record
            analysis = self.analysis_repo.create(
                image_id=image_id,
                raw_response=response,
                title=analysis_data.get("title"),
                subject=analysis_data.get("subject"),
                character_description=analysis_data.get("character_description"),
                environment=analysis_data.get("environment"),
                art_style=analysis_data.get("art_style"),
                color_palette=analysis_data.get("color_palette", []),
                mood=analysis_data.get("mood"),
                genre=analysis_data.get("genre"),
                technical_details=analysis_data.get("technical_details"),
                artistic_influences=analysis_data.get("artistic_influences"),
                search_keywords=analysis_data.get("search_keywords", []),
                audience_interests=analysis_data.get("audience_interests", []),
                model_used=self.ollama_client.model,
                prompt_version=prompt_version
            )
            
            # Update image status to analyzed
            self.image_repo.update_status(image_id, ImageStatus.ANALYZED)
            
            logger.info(f"Successfully analyzed image: {image_id}")
            return analysis
            
        except Exception as e:
            # Update image status to failed
            self.image_repo.update_status(
                image_id,
                ImageStatus.FAILED,
                error_message=str(e)
            )
            logger.error(f"Failed to analyze image {image_id}: {e}")
            raise
    
    def get_analysis(self, image_id: str) -> Analysis | None:
        """Get analysis for an image.
        
        Args:
            image_id: Image ID
            
        Returns:
            Analysis instance or None
        """
        return self.analysis_repo.get_by_image_id(image_id)
    
    def update_analysis(
        self,
        image_id: str,
        **kwargs
    ) -> Analysis | None:
        """Update analysis data.
        
        Args:
            image_id: Image ID
            **kwargs: Fields to update
            
        Returns:
            Updated analysis or None
        """
        analysis = self.analysis_repo.get_by_image_id(image_id)
        if not analysis:
            return None
        
        return self.analysis_repo.update(analysis, **kwargs)
    
    def create_analysis(
        self,
        image_id: str,
        raw_response: dict,
        model_used: str,
        prompt_version: str,
        **kwargs
    ) -> Analysis:
        """Create analysis with manual data (skip AI analysis).
        
        Args:
            image_id: Image ID
            raw_response: Raw AI response (empty for manual)
            model_used: Model name (manual for manual entry)
            prompt_version: Prompt version (manual for manual entry)
            **kwargs: Analysis fields
            
        Returns:
            Created analysis
        """
        # Create analysis with provided data
        analysis = self.analysis_repo.create(
            image_id=image_id,
            raw_response=raw_response,
            model_used=model_used,
            prompt_version=prompt_version,
            **kwargs
        )
        
        logger.info(f"Created manual analysis for image: {image_id}")
        return analysis
    
    def delete_analysis(self, image_id: str) -> bool:
        """Delete analysis for an image.
        
        Args:
            image_id: Image ID
            
        Returns:
            True if deleted, False otherwise
        """
        return self.analysis_repo.delete_by_image_id(image_id)
