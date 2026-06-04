import base64
import logging
import httpx
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
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
            logger.info(f"Reading image from: {image_path}")
            
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
                image_data = base64.b64encode(image_bytes).decode('utf-8')
            
            logger.info(f"Image size: {len(image_bytes)} bytes, encoded size: {len(image_data)} characters")
            
            # Use the correct Ollama API format for vision models
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_data],
                "stream": False
            }
            
            logger.info(f"Sending request to Ollama: {self.base_url}/api/generate")
            logger.info(f"Model: {self.model}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                logger.info(f"Response status: {response.status_code}")
                if response.status_code != 200:
                    logger.error(f"Response body: {response.text}")
                
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get('response', '')
                logger.info(f"Ollama response received successfully: {response_text[:200]}...")
                
                # Format response to match expected structure
                return {"message": {"content": response_text}}
                
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            logger.error(f"Ollama image analysis failed: {e}")
            raise

    async def analyze_image_stream(self, image_path: str, prompt: str) -> AsyncGenerator[str, None]:
        """Analyze an image using Ollama vision model with streaming response.
        
        Args:
            image_path: Path to the image file
            prompt: Analysis prompt
            
        Yields:
            Text chunks as they are generated
        """
        try:
            logger.info(f"Reading image from: {image_path}")
            
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
                image_data = base64.b64encode(image_bytes).decode('utf-8')
            
            # Use the correct Ollama API format for vision models
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_data],
                "stream": True
            }
            
            logger.info(f"Sending streaming request to Ollama: {self.base_url}/api/generate")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream('POST', f"{self.base_url}/api/generate", json=payload, headers={"Content-Type": "application/json"}) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                # Parse NDJSON line
                                data = json.loads(line)
                                if "response" in data:
                                    content = data["response"]
                                    if content:
                                        logger.debug(f"Streamed chunk: {content[:50]}...")
                                        yield content
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse NDJSON: {e}")
                                continue
                                
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            raise
        except Exception as e:
            logger.error(f"Ollama streaming image analysis failed: {e}")
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
                "prompt": prompt,
                "stream": False
            }
            
            logger.info(f"Sending content generation request to Ollama")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get('response', '')
                logger.info(f"Ollama response received: {response_text[:200]}...")
                
                # Format response to match expected structure
                return {"message": {"content": response_text}}
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error from Ollama: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama content generation failed: {e}")
            raise
    
    async def generate_content_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Generate text content using Ollama with streaming response.
        
        Args:
            prompt: Generation prompt
            
        Yields:
            Text chunks as they are generated
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True
            }
            
            logger.info(f"Sending streaming content generation request to Ollama")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream('POST', f"{self.base_url}/api/generate", json=payload, headers={"Content-Type": "application/json"}) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                # Parse NDJSON line
                                data = json.loads(line)
                                if "response" in data:
                                    content = data["response"]
                                    if content:
                                        logger.debug(f"Streamed chunk: {content[:50]}...")
                                        yield content
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse NDJSON: {e}")
                                continue
                                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error from Ollama: {e}")
            raise
        except Exception as e:
            logger.error(f"Ollama streaming content generation failed: {e}")
            raise
    
    def set_model(self, model: str):
        """Change the model being used."""
        self.model = model
        logger.info(f"Ollama model changed to: {model}")
