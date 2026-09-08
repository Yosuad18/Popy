"""Health check router."""

from fastapi import APIRouter
from app.schemas.chat import HealthResponse
from app.config import settings
from app.agent.graph import is_openai_configured

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse, summary="Check API Health")
async def health_check() -> HealthResponse:
    """Returns application health status, version, and OpenAI configuration state."""
    return HealthResponse(
        status="healthy",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        openai_configured=is_openai_configured()
    )
