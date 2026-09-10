"""FastAPI router for handling chat endpoints."""

from typing import Dict
import uuid
from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.agent.graph import graph, get_graph_mermaid
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """Endpoint principal de conversación con el agente de LangGraph."""
    thread_id = payload.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=payload.message)]},
            config=config
        )

        last_message = result["messages"][-1]

        return ChatResponse(
            response=last_message.content,
            thread_id=thread_id,
            model="gpt-4o-mini",
            metadata={"total_messages": len(result["messages"])}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing chat graph: {str(e)}")


@router.get("/graph", response_model=Dict[str, str])
async def get_graph():
    """Devuelve el diagrama Mermaid del grafo."""
    return {"mermaid": get_graph_mermaid()}