"""LM Studio client for vision model integration."""

import base64
from typing import Any

import httpx

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class LMStudioClient:
    """Client for interacting with LM Studio's OpenAI-compatible API."""
    
    def __init__(
        self,
        endpoint: str | None = None,
        model: str | None = None,
        timeout: int | None = None
    ):
        """Initialize LM Studio client.
        
        Args:
            endpoint: LM Studio API endpoint (defaults to config)
            model: Model name (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
        """
        self.endpoint = endpoint or settings.LM_STUDIO_ENDPOINT
        self.model = model or settings.LM_STUDIO_MODEL
        self.timeout = timeout or settings.LM_STUDIO_TIMEOUT
        
        logger.info(
            f"Initialized LM Studio client: endpoint={self.endpoint}, "
            f"model={self.model}, timeout={self.timeout}s"
        )
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    async def analyze_image(
        self,
        image_path: str,
        prompt: str
    ) -> dict[str, Any]:
        """Send image to LM Studio for analysis.
        
        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            
        Returns:
            Analysis response as dictionary
            
        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response parsing fails
        """
        # Encode image
        base64_image = self.encode_image(image_path)
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        logger.info(f"Sending analysis request to LM Studio for image: {image_path}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                logger.info(f"LM Studio response status: {response.status_code}")
                logger.info(f"LM Studio response headers: {response.headers}")
                
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"LM Studio response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                
                # Extract content from response
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    logger.info(f"Received analysis response from LM Studio")
                    return {"content": content, "raw_response": result}
                else:
                    logger.error(f"Invalid response format from LM Studio: {result}")
                    raise ValueError("Invalid response format from LM Studio")
                    
        except httpx.HTTPError as e:
            logger.error(f"HTTP error from LM Studio: {e}")
            raise
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            raise
    
    async def generate_content(
        self,
        prompt: str
    ) -> dict[str, Any]:
        """Generate content using LM Studio (text-only).
        
        Args:
            prompt: Generation prompt
            
        Returns:
            Generated content response
            
        Raises:
            httpx.HTTPError: If request fails
            ValueError: If response parsing fails
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        logger.info("Sending content generation request to LM Studio")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract content from response
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    logger.info("Received content generation response from LM Studio")
                    return {"content": content, "raw_response": result}
                else:
                    raise ValueError("Invalid response format from LM Studio")
                    
        except httpx.HTTPError as e:
            logger.error(f"HTTP error from LM Studio: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if LM Studio endpoint is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            response = httpx.get(
                self.endpoint.replace("/chat/completions", "/models"),
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
