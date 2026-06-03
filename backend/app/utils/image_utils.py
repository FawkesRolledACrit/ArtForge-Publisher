"""Image utility functions."""

import uuid
from pathlib import Path
from typing import Tuple

from PIL import Image as PILImage

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def save_uploaded_image(
    file_content: bytes,
    filename: str,
    mime_type: str
) -> Tuple[str, str, int, Tuple[int, int] | None]:
    """Save uploaded image to storage.
    
    Args:
        file_content: Image file content as bytes
        filename: Original filename
        mime_type: MIME type of the image
        
    Returns:
        Tuple of (saved_path, thumbnail_path, file_size, dimensions)
    """
    # Generate unique filename
    file_extension = Path(filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    saved_path = settings.IMAGES_PATH / unique_filename
    
    # Save original image
    with open(saved_path, "wb") as f:
        f.write(file_content)
    
    file_size = len(file_content)
    
    # Get image dimensions
    dimensions = None
    try:
        with PILImage.open(saved_path) as img:
            dimensions = img.size
            logger.info(f"Image dimensions: {dimensions[0]}x{dimensions[1]}")
    except Exception as e:
        logger.error(f"Failed to get image dimensions: {e}")
    
    # Generate thumbnail
    thumbnail_path = generate_thumbnail(saved_path)
    
    logger.info(f"Saved image: {saved_path}, thumbnail: {thumbnail_path}")
    return str(saved_path), str(thumbnail_path), file_size, dimensions


def generate_thumbnail(image_path: Path, size: Tuple[int, int] = (300, 300)) -> str:
    """Generate thumbnail for image.
    
    Args:
        image_path: Path to original image
        size: Thumbnail size (width, height)
        
    Returns:
        Path to generated thumbnail
    """
    try:
        with PILImage.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode == "RGBA":
                img = img.convert("RGB")
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, PILImage.Resampling.LANCZOS)
            
            # Generate thumbnail filename
            thumbnail_filename = f"thumb_{image_path.stem}.jpg"
            thumbnail_path = settings.THUMBNAILS_PATH / thumbnail_filename
            
            # Save thumbnail
            img.save(thumbnail_path, "JPEG", quality=85)
            
            logger.info(f"Generated thumbnail: {thumbnail_path}")
            return str(thumbnail_path)
    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}")
        return ""


def delete_image_files(original_path: str, thumbnail_path: str | None) -> None:
    """Delete image files from storage.
    
    Args:
        original_path: Path to original image
        thumbnail_path: Path to thumbnail (optional)
    """
    try:
        if original_path:
            Path(original_path).unlink(missing_ok=True)
            logger.info(f"Deleted original image: {original_path}")
    except Exception as e:
        logger.error(f"Failed to delete original image: {e}")
    
    try:
        if thumbnail_path:
            Path(thumbnail_path).unlink(missing_ok=True)
            logger.info(f"Deleted thumbnail: {thumbnail_path}")
    except Exception as e:
        logger.error(f"Failed to delete thumbnail: {e}")


def validate_image_type(mime_type: str) -> bool:
    """Validate image MIME type.
    
    Args:
        mime_type: MIME type to validate
        
    Returns:
        True if valid, False otherwise
    """
    return mime_type in settings.ALLOWED_IMAGE_TYPES


def validate_image_size(file_size: int) -> bool:
    """Validate image file size.
    
    Args:
        file_size: File size in bytes
        
    Returns:
        True if valid, False otherwise
    """
    max_size_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    return file_size <= max_size_bytes
