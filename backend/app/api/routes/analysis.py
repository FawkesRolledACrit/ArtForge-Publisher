"""API routes for image analysis."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import AnalysisRequest, AnalysisResponse, AnalysisUpdate
from app.dependencies import get_analysis_repository, get_image_repository, get_prompt_repository
from app.services.analysis_service import AnalysisService
from app.services.ollama_client import OllamaClient
from app.services.prompt_service import PromptService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    analysis_data: AnalysisUpdate,
    analysis_repo = Depends(get_analysis_repository),
    image_repo = Depends(get_image_repository)
):
    """Create analysis with manual data (skip AI analysis).
    
    Args:
        analysis_data: Analysis data to create
        analysis_repo: Analysis repository
        image_repo: Image repository
        
    Returns:
        Created analysis
    """
    # Extract image_id from the data
    image_id = analysis_data.image_id
    if not image_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="image_id is required"
        )
    
    # Check if image exists
    image = image_repo.get(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Create analysis with manual data (use defaults for AI-specific fields)
    analysis_service = AnalysisService(analysis_repo, image_repo, None)
    analysis = analysis_service.create_analysis(
        image_id,
        raw_response={},  # Empty since no AI analysis
        model_used="manual",
        prompt_version="manual",
        **analysis_data.model_dump(exclude_unset=True, exclude={"image_id"})
    )
    
    # Update image status to analyzed
    from app.models import ImageStatus
    image_repo.update_status(image_id, ImageStatus.ANALYZED)
    
    logger.info(f"Created manual analysis for image: {image_id}")
    return analysis


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_image(
    request: AnalysisRequest,
    analysis_repo = Depends(get_analysis_repository),
    image_repo = Depends(get_image_repository),
    prompt_repo = Depends(get_prompt_repository)
):
    """Analyze an image using the vision model.
    
    Args:
        request: Analysis request
        db: Database session
        analysis_service: Analysis service
        
    Returns:
        Analysis result
    """
    try:
        prompt_service = PromptService(prompt_repo)
        ollama_client = OllamaClient()
        analysis_service = AnalysisService(analysis_repo, image_repo, prompt_service, ollama_client)
        analysis = await analysis_service.analyze_image(request.image_id)
        logger.info(f"Analyzed image: {request.image_id}")
        return analysis
    except ValueError as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze image"
        )


@router.get("/{image_id}", response_model=AnalysisResponse)
async def get_analysis(
    image_id: str,
    analysis_repo = Depends(get_analysis_repository)
):
    """Get analysis for an image.
    
    Args:
        image_id: Image ID
        db: Database session
        analysis_service: Analysis service
        
    Returns:
        Analysis result
    """
    analysis_service = AnalysisService(analysis_repo, None, None)
    analysis = analysis_service.get_analysis(image_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    return analysis


@router.put("/{image_id}", response_model=AnalysisResponse)
async def update_analysis(
    image_id: str,
    analysis_update: AnalysisUpdate,
    analysis_repo = Depends(get_analysis_repository),
    image_repo = Depends(get_image_repository)
):
    """Update analysis data.
    
    Args:
        image_id: Image ID
        analysis_update: Update data
        db: Database session
        analysis_service: Analysis service
        
    Returns:
        Updated analysis
    """
    analysis_service = AnalysisService(analysis_repo, image_repo, None)
    analysis = analysis_service.update_analysis(image_id, **analysis_update.model_dump(exclude_unset=True))
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # Update image status to analyzed
    from app.models import ImageStatus
    image_repo.update_status(image_id, ImageStatus.ANALYZED)
    
    logger.info(f"Updated analysis for image: {image_id}")
    return analysis


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    image_id: str,
    analysis_repo = Depends(get_analysis_repository)
):
    """Delete analysis for an image.
    
    Args:
        image_id: Image ID
        db: Database session
        analysis_service: Analysis service
    """
    analysis_service = AnalysisService(analysis_repo, None, None)
    success = analysis_service.delete_analysis(image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    logger.info(f"Deleted analysis for image: {image_id}")
