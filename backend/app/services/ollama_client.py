import base64
import logging
import httpx
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_ENDPOINT
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        
    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama availability check failed: {e}")
            return False
    
    async def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Analyze an image using Ollama vision model.
        
        Args:
            image_path: Path to the image file
            prompt: Analysis prompt
            
        Returns:
            Response from Ollama
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_data]
                    }
                ],
                "stream": False
            }
            
            logger.info(f"Sending image analysis request to Ollama: {self.base_url}")
            logger.debug(f"Payload model: {self.model}, prompt length: {len(prompt)}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Ollama response received: {result.get('message', {}).get('content', '')[:200]}...")
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error from Ollama: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama image analysis failed: {e}")
            raise
    
    async def generate_content(self, prompt: str) -> Dict[str, Any]:
        """Generate text content using Ollama.
        
        Args:
            prompt: Generation prompt
            
        Returns:
            Response from Ollama
        """
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            }
            
            logger.info(f"Sending content generation request to Ollama")
            logger.debug(f"Payload model: {self.model}, prompt length: {len(prompt)}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Ollama response received: {result.get('message', {}).get('content', '')[:200]}...")
                
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error from Ollama: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama content generation failed: {e}")
            raise
    
    def set_model(self, model: str):
        """Change the model being used."""
        self.model = model
        logger.info(f"Ollama model changed to: {model}")
