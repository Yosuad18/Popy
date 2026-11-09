"""FastAPI router for handling chat endpoints."""

from typing import Dict
import json
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, ToolMessage

from app.agent.graph import graph, get_graph_mermaid
from app.schemas.chat import ChatRequest, ChatResponse


def _extract_html_tool_response(messages) -> str | None:
    """Return the raw `html:` output of place_order from the *current* turn only.

    Guarantees the Nequi payment form reaches the frontend intact,
    regardless of how the LLM rephrases the final answer. Historical
    place_order results are ignored so later replies are not overridden.
    """
    # Current turn starts after the last human message.
    start = 0
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage):
            start = i + 1
            break

    for msg in reversed(messages[start:]):
        if (
            isinstance(msg, ToolMessage)
            and msg.name == "place_order"
            and isinstance(msg.content, str)
            and msg.content.startswith("html:")
        ):
            return msg.content
    return None


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
        response = _extract_html_tool_response(result["messages"]) or last_message.content

        return ChatResponse(
            response=response,
            thread_id=thread_id,
            model="gpt-4o-mini",
            metadata={"total_messages": len(result["messages"])}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing chat graph: {str(e)}")


@router.post("/stream")
async def chat_stream_endpoint(payload: ChatRequest):
    """Return a chat response using the frontend's server-sent event protocol."""
    thread_id = payload.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def events():
        try:
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=payload.message)]},
                config=config
            )
            response = _extract_html_tool_response(result["messages"]) or result["messages"][-1].content
            yield f"event: thread\ndata: {json.dumps({'thread_id': thread_id})}\n\n"
            yield f"event: token\ndata: {json.dumps({'token': response})}\n\n"
            yield f"event: done\ndata: {json.dumps({'thread_id': thread_id})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/graph", response_model=Dict[str, str])
async def get_graph():
    """Devuelve el diagrama Mermaid del grafo."""
    return {"mermaid": get_graph_mermaid()}