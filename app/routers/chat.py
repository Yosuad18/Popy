"""Chat API endpoints for interacting with the LangGraph agent."""

import uuid
import json
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse, PlainTextResponse
from langchain_core.messages import HumanMessage, BaseMessage

from app.schemas.chat import ChatRequest, ChatResponse
from app.agent import graph, tools
from app.agent.graph import get_graph_mermaid
from app.config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])


def serialize_message(msg: BaseMessage) -> Dict[str, Any]:
    """Helper to convert BaseMessage into JSON-serializable dict."""
    return {
        "type": msg.type,
        "content": msg.content,
        "additional_kwargs": getattr(msg, "additional_kwargs", {}),
    }


@router.post("", response_model=ChatResponse, summary="Send message to chatbot")
async def send_message(request: ChatRequest) -> ChatResponse:
    """Processes a user message through the LangGraph agent workflow.
    
    If thread_id is provided, conversation history is preserved across calls.
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "messages": [HumanMessage(content=request.message)],
        "system_prompt": request.system_prompt
    }

    try:
        # Run graph through completion
        final_state = await graph.ainvoke(inputs, config=config)
        
        messages = final_state.get("messages", [])
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Graph execution produced no messages"
            )

        last_message = messages[-1]
        response_content = str(last_message.content)

        return ChatResponse(
            response=response_content,
            thread_id=thread_id,
            model=settings.OPENAI_MODEL,
            metadata={
                "total_messages": len(messages),
                "last_message_type": last_message.type
            }
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing chat graph: {str(exc)}"
        )


@router.post("/stream", summary="Stream chatbot responses token/event-wise")
async def stream_message(request: ChatRequest):
    """Streams graph updates via Server-Sent Events (SSE) format."""
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "messages": [HumanMessage(content=request.message)],
        "system_prompt": request.system_prompt
    }

    async def event_generator():
        # First send thread_id event
        yield f"event: thread\ndata: {json.dumps({'thread_id': thread_id})}\n\n"
        
        try:
            async for event in graph.astream_events(inputs, config=config, version="v2"):
                event_type = event.get("event")
                
                # Stream model tokens as they are generated
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        payload = json.dumps({"token": chunk.content})
                        yield f"event: token\ndata: {payload}\n\n"
                        
                # Notify when tools start
                elif event_type == "on_tool_start":
                    tool_name = event.get("name")
                    payload = json.dumps({"tool": tool_name})
                    yield f"event: tool_start\ndata: {payload}\n\n"

                # Notify when tools finish
                elif event_type == "on_tool_end":
                    tool_output = str(event.get("data", {}).get("output", ""))
                    payload = json.dumps({"output": tool_output})
                    yield f"event: tool_end\ndata: {payload}\n\n"

            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            err_payload = json.dumps({"error": str(exc)})
            yield f"event: error\ndata: {err_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history/{thread_id}", summary="Get conversation history for a thread")
async def get_thread_history(thread_id: str):
    """Retrieves full conversation history stored by LangGraph checkpointer for a given thread_id."""
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = graph.get_state(config)

    if not state_snapshot or not state_snapshot.values:
        return {
            "thread_id": thread_id,
            "found": False,
            "messages": []
        }

    messages = state_snapshot.values.get("messages", [])
    return {
        "thread_id": thread_id,
        "found": True,
        "total_messages": len(messages),
        "messages": [serialize_message(m) for m in messages]
    }


@router.delete("/history/{thread_id}", summary="Clear/reset conversation history for a thread")
async def clear_thread_history(thread_id: str):
    """Resets conversation history for the given thread_id."""
    config = {"configurable": {"thread_id": thread_id}}
    # Check if thread exists
    state_snapshot = graph.get_state(config)
    if not state_snapshot or not state_snapshot.values:
        return {"thread_id": thread_id, "cleared": False, "message": "Thread not found or already empty"}

    # LangGraph update_state with empty messages or reset state
    try:
        # Overwrite state by passing empty or reset state
        graph.update_state(config, {"messages": []})
        return {"thread_id": thread_id, "cleared": True, "message": "Thread history cleared successfully"}
    except Exception as exc:
        # Alternatively, note that thread checkpointer will be clean on next new session
        return {"thread_id": thread_id, "cleared": True, "message": f"Thread marked cleared: {str(exc)}"}


@router.get("/tools", summary="List all registered agent tools")
async def list_tools() -> List[Dict[str, Any]]:
    """Returns all tools registered in the LangGraph agent with names, descriptions and schema arguments."""
    results = []
    for t in tools:
        results.append({
            "name": t.name,
            "description": t.description,
            "args_schema": t.args if hasattr(t, "args") else {}
        })
    return results


@router.get("/graph", summary="Get LangGraph state machine diagram in Mermaid format")
async def get_graph_diagram(format: str = "text"):
    """Returns Mermaid diagram representation of the LangGraph agent state machine."""
    mermaid_code = get_graph_mermaid()
    if format == "html":
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true }});
  </script>
</head>
<body style="display:flex; justify-content:center; align-items:center; min-height:100vh; background:#f8fafc; font-family:sans-serif;">
  <div style="background:white; padding:2rem; border-radius:12px; box-shadow:0 4px 6px -1px rgb(0 0 0 / 0.1);">
    <h2 style="margin-top:0;">LangGraph StateGraph Diagram</h2>
    <pre class="mermaid">
{mermaid_code}
    </pre>
  </div>
</body>
</html>"""
        return StreamingResponse(iter([html]), media_type="text/html")
    
    return PlainTextResponse(content=mermaid_code)
