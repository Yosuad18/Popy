"""Chat request and response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ChatMessage(BaseModel):
    """Represents an individual message in a conversation."""
    role: str = Field(..., description="Role of the speaker: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content text")


class ChatRequest(BaseModel):
    """Request payload for sending a chat message."""
    message: str = Field(..., min_length=1, description="The user's prompt or question")
    thread_id: Optional[str] = Field(
        default=None,
        description="Optional session/thread identifier for multi-turn conversational memory"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional custom system prompt to steer chatbot behavior"
    )


class ChatResponse(BaseModel):
    """Response payload returned from the chatbot."""
    response: str = Field(..., description="The assistant's generated response")
    thread_id: str = Field(..., description="The conversation thread ID")
    model: str = Field(..., description="The LLM model used")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional execution metadata")


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field("healthy", description="Application status")
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    openai_configured: bool = Field(..., description="Whether a valid OpenAI API key is detected")