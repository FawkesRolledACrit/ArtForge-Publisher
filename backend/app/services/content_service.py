"""Content generation service for platform-specific content."""

import json

from app.models import Analysis, ContentType, GeneratedContent, Image, ImageStatus, Platform
from app.repositories.content_repository import ContentRepository
from app.repositories.image_repository import ImageRepository
from app.services.ollama_client import OllamaClient
from app.services.prompt_service import PromptService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ContentGenerationService:
    """Service for generating platform-specific content."""
    
    def __init__(
        self,
        content_repo: ContentRepository,
        image_repo: ImageRepository,
        prompt_service: PromptService,
        ollama_client: OllamaClient | None = None
    ):
        """Initialize content generation service.
        
        Args:
            content_repo: Content repository
            image_repo: Image repository
            prompt_service: Prompt service
            ollama_client: Ollama client (optional, for testing)
        """
        self.content_repo = content_repo
        self.image_repo = image_repo
        self.prompt_service = prompt_service
        self.ollama_client = ollama_client or OllamaClient()
    
    async def generate_content(
        self,
        image_id: str,
        platforms: list[Platform] | None = None
    ) -> list[GeneratedContent]:
        """Generate platform-specific content for an image.
        
        Args:
            image_id: Image ID
            platforms: List of platforms to generate for (defaults to all)
            
        Returns:
            List of generated content items
            
        Raises:
            ValueError: If image not found or not analyzed
            RuntimeError: If LM Studio is unavailable
        """
        # Get image
        image = self.image_repo.get(image_id)
        if not image:
            raise ValueError(f"Image not found: {image_id}")
        
        # Check if image has been analyzed
        if image.status != ImageStatus.ANALYZED:
            raise ValueError(f"Image must be analyzed before content generation: {image_id}")
        
        # Get analysis
        from app.repositories.analysis_repository import AnalysisRepository
        analysis_repo = AnalysisRepository(self.image_repo.db)
        analysis = analysis_repo.get_by_image_id(image_id)
        
        if not analysis:
            raise ValueError(f"No analysis found for image: {image_id}")
        
        # Default to all platforms if none specified
        if platforms is None:
            platforms = [
                Platform.ARTSTATION,
                Platform.X,
                Platform.INSTAGRAM,
                Platform.REDDIT,
                Platform.DEVIANTART
            ]
        
        generated_contents = []
        
        # Update image status to generating
        self.image_repo.update_status(image_id, ImageStatus.GENERATING)
        
        try:
            for platform in platforms:
                platform_contents = await self._generate_for_platform(
                    image_id,
                    platform,
                    analysis
                )
                generated_contents.extend(platform_contents)
            
            # Update image status to ready
            self.image_repo.update_status(image_id, ImageStatus.READY)
            
            logger.info(f"Successfully generated content for image: {image_id}")
            return generated_contents
            
        except Exception as e:
            # Update image status to failed
            self.image_repo.update_status(
                image_id,
                ImageStatus.FAILED,
                error_message=str(e)
            )
            logger.error(f"Failed to generate content for image {image_id}: {e}")
            raise
    
    async def _generate_for_platform(
        self,
        image_id: str,
        platform: Platform,
        analysis: Analysis | None
    ) -> list[GeneratedContent]:
        """Generate content for a specific platform.
        
        Args:
            image_id: Image ID
            platform: Platform to generate for
            analysis: Analysis data
            
        Returns:
            List of generated content items
        """
        # Get platform-specific prompt
        prompt_name = f"{platform.value}_post"
        prompt = self.prompt_service.get_prompt_content(prompt_name)
        prompt_version = self.prompt_service._generate_version_hash(prompt)
        
        # Format prompt with analysis data
        if analysis:
            analysis_json = json.dumps({
                "title": analysis.title,
                "subject": analysis.subject,
                "art_style": analysis.art_style,
                "genre": analysis.genre,
                "technical_details": analysis.technical_details,
                "search_keywords": analysis.search_keywords
            }, indent=2)
            formatted_prompt = prompt.replace("{analysis}", analysis_json)
        else:
            formatted_prompt = prompt
        
        # Generate content
        response = await self.ollama_client.generate_content(formatted_prompt)
        
        # Parse response from Ollama
        try:
            content = response["message"]["content"]
            logger.info(f"Raw response from Ollama for {platform}: {content[:200]}...")
            
            # Strip markdown code blocks if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            # Robust JSON parsing - handle control characters and malformed JSON
            # First, try to parse as-is
            try:
                content_data = json.loads(content)
                logger.info(f"Successfully parsed JSON for {platform}")
            except json.JSONDecodeError as e:
                logger.warning(f"Initial JSON parse failed for {platform}: {e}")
                # If that fails, try cleaning the JSON
                try:
                    # Normalize Unicode and remove ALL control characters
                    import unicodedata
                    content = unicodedata.normalize('NFKC', content)
                    # Remove ALL control characters (including \r, \n, \t within strings)
                    import re
                    content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
                    content_data = json.loads(content)
                    logger.info(f"Successfully parsed JSON after removing all control chars for {platform}")
                except json.JSONDecodeError as e2:
                    logger.warning(f"JSON parse after control char removal failed for {platform}: {e2}")
                    # If still failing, try even more aggressive cleaning
                    try:
                        # Remove all newlines and tabs, then re-add them in JSON structure
                        content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                        content_data = json.loads(content)
                        logger.info(f"Successfully parsed JSON after removing all whitespace for {platform}")
                    except json.JSONDecodeError as e3:
                        logger.warning(f"JSON parse after whitespace removal failed for {platform}: {e3}")
                        # Try character-by-character cleaning
                        try:
                            cleaned = []
                            for char in content:
                                # Keep only printable ASCII and valid Unicode
                                if ord(char) >= 32 or char in '\n\t':
                                    cleaned.append(char)
                            content = ''.join(cleaned)
                            content_data = json.loads(content)
                            logger.info(f"Successfully parsed JSON after char-by-char cleaning for {platform}")
                        except json.JSONDecodeError as e4:
                            logger.error(f"Failed to parse content response for {platform}: {e4}")
                            logger.error(f"Response content: {response.get('message', {}).get('content', '')[:1000]}")
                            # Try to extract JSON using regex as last resort
                            try:
                                import re
                                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                                if json_match:
                                    extracted = json_match.group(0)
                                    # Normalize Unicode on extracted JSON
                                    extracted = unicodedata.normalize('NFKC', extracted)
                                    # Remove all control characters
                                    extracted = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', extracted)
                                    content_data = json.loads(extracted)
                                    logger.info(f"Successfully extracted JSON using regex for {platform}")
                                else:
                                    raise ValueError("No JSON found in response")
                            except Exception as e5:
                                logger.error(f"Regex extraction also failed for {platform}: {e5}")
                                raise ValueError(f"Invalid JSON response for {platform}")
        except KeyError as e:
            logger.error(f"Missing expected key in Ollama response: {e}")
            logger.error(f"Response structure: {response}")
            raise ValueError(f"Invalid response structure from Ollama for {platform}")
        
        # Create content records based on platform
        contents = []
        
        if platform == Platform.ARTSTATION:
            contents.extend([
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.TITLE,
                    content=content_data.get("title", ""),
                    prompt_version=prompt_version
                ),
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.DESCRIPTION,
                    content=content_data.get("description", ""),
                    prompt_version=prompt_version
                ),
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.HASHTAGS,
                    content=", ".join(content_data.get("tags", [])),
                    prompt_version=prompt_version
                )
            ])
        
        elif platform == Platform.X:
            for version_type, content in [
                ("short", content_data.get("short_version", "")),
                ("medium", content_data.get("medium_version", "")),
                ("engagement", content_data.get("engagement_version", ""))
            ]:
                contents.append(
                    self.content_repo.create(
                        image_id=image_id,
                        platform=platform,
                        content_type=ContentType.POST,
                        content=f"[{version_type}] {content}",
                        prompt_version=prompt_version
                    )
                )
        
        elif platform == Platform.INSTAGRAM:
            contents.extend([
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.POST,
                    content=content_data.get('caption', ''),
                    prompt_version=prompt_version
                ),
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.HASHTAGS,
                    content=" ".join(content_data.get("hashtags", [])),
                    prompt_version=prompt_version
                )
            ])
        
        elif platform == Platform.REDDIT:
            contents.extend([
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.TITLE,
                    content=content_data.get("titles", [""])[0],
                    prompt_version=prompt_version
                ),
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.DESCRIPTION,
                    content=content_data.get("body", ""),
                    prompt_version=prompt_version
                ),
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.RECOMMENDED_SUBREDDITS,
                    content=json.dumps(content_data.get("recommended_subreddits", [])),
                    prompt_version=prompt_version
                )
            ])
        
        elif platform == Platform.DEVIANTART:
            contents.extend([
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.TITLE,
                    content=content_data.get("title", ""),
                    prompt_version=prompt_version
                ),
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.DESCRIPTION,
                    content=content_data.get("description", ""),
                    prompt_version=prompt_version
                ),
                self.content_repo.create(
                    image_id=image_id,
                    platform=platform,
                    content_type=ContentType.HASHTAGS,
                    content=", ".join(content_data.get("tags", [])),
                    prompt_version=prompt_version
                )
            ])
        
        logger.info(f"Generated {len(contents)} content items for {platform}")
        return contents
    
    def get_content(self, image_id: str) -> list[GeneratedContent]:
        """Get all content for an image.
        
        Args:
            image_id: Image ID
            
        Returns:
            List of content items
        """
        return self.content_repo.get_by_image_id(image_id)
    
    def get_platform_content(
        self,
        image_id: str,
        platform: Platform
    ) -> list[GeneratedContent]:
        """Get content for a specific platform.
        
        Args:
            image_id: Image ID
            platform: Platform
            
        Returns:
            List of content items for the platform
        """
        return self.content_repo.get_by_image_and_platform(image_id, platform)
    
    def update_content(
        self,
        content_id: str,
        new_content: str
    ) -> GeneratedContent | None:
        """Update content.
        
        Args:
            content_id: Content ID
            new_content: New content text
            
        Returns:
            Updated content or None
        """
        content = self.content_repo.get(content_id)
        if not content:
            return None
        
        return self.content_repo.update(
            content,
            content=new_content,
            is_edited=True
        )
    
    def delete_content(self, image_id: str) -> int:
        """Delete all content for an image.
        
        Args:
            image_id: Image ID
            
        Returns:
            Number of deleted items
        """
        return self.content_repo.delete_by_image_id(image_id)
