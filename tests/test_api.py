"""Comprehensive test suite for FastAPI + LangGraph Chatbot."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.agent.tools import (
    calculate,
    get_current_time,
    get_weather,
    save_note,
    get_notes,
    search_knowledge,
)
from app.agent.main import run_agent

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint provides correct metadata, status, and navigation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "docs_url" in data
    assert "chat_url" in data
    assert "tools_url" in data
    assert "graph_diagram_url" in data


def test_health_endpoint():
    """Verify healthcheck endpoint returns healthy status and metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "openai_configured" in data
    assert "version" in data


def test_demo_ui_endpoint():
    """Verify the interactive demo UI is served as HTML."""
    response = client.get("/demo")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LangGraph" in response.text


def test_list_tools_endpoint():
    """Verify /chat/tools returns registered agent tools."""
    response = client.get("/chat/tools")
    assert response.status_code == 200
    tools_list = response.json()
    assert isinstance(tools_list, list)
    names = [t["name"] for t in tools_list]
    assert "calculate" in names
    assert "get_current_time" in names
    assert "get_weather" in names
    assert "save_note" in names
    assert "get_notes" in names
    assert "search_knowledge" in names


def test_graph_diagram_endpoint():
    """Verify /chat/graph returns Mermaid diagram and HTML representation."""
    # Plain text format
    text_res = client.get("/chat/graph")
    assert text_res.status_code == 200
    assert "graph" in text_res.text.lower() or "agent" in text_res.text

    # HTML format
    html_res = client.get("/chat/graph?format=html")
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers["content-type"]
    assert "mermaid" in html_res.text


def test_tool_calculate():
    """Verify safe calculator tool handles operations and safely rejects unsafe code."""
    assert calculate.invoke({"expression": "5 * 5"}) == "25"
    assert calculate.invoke({"expression": "(10 + 20) / 2"}) == "15.0"
    assert calculate.invoke({"expression": "2 ** 3"}) == "8"
    result = calculate.invoke({"expression": "__import__('os').system('ls')"})
    assert "Error" in result


def test_tool_get_current_time():
    """Verify get_current_time returns formatted date string."""
    time_str = get_current_time.invoke({})
    assert isinstance(time_str, str)
    assert len(time_str) >= 10


def test_tool_get_weather():
    """Verify get_weather returns forecasts for requested cities."""
    res_bogota = get_weather.invoke({"city": "Bogota"})
    assert "Bogota" in res_bogota
    assert "°C" in res_bogota

    res_madrid = get_weather.invoke({"city": "Madrid"})
    assert "Madrid" in res_madrid


def test_tool_notes_management():
    """Verify save_note and get_notes can store and recall memory items."""
    save_res = save_note.invoke({"title": "meeting", "content": "Team standup at 10 AM"})
    assert "guardada" in save_res.lower() or "exitosa" in save_res.lower()

    notes_res = get_notes.invoke({})
    assert "Meeting" in notes_res
    assert "Team standup at 10 AM" in notes_res


def test_tool_search_knowledge():
    """Verify search_knowledge retrieves relevant tech docs."""
    result = search_knowledge.invoke({"query": "fastapi"})
    assert "FastAPI" in result


def test_chat_message_flow():
    """Verify /chat endpoint processes request and maintains state."""
    thread_id = "test-session-suite"
    payload = {
        "message": "Hello, testing chatbot memory!",
        "thread_id": thread_id
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["thread_id"] == thread_id
    assert "model" in data

    # Verify conversation history was recorded under this thread_id
    hist_response = client.get(f"/chat/history/{thread_id}")
    assert hist_response.status_code == 200
    hist_data = hist_response.json()
    assert hist_data["found"] is True
    assert hist_data["total_messages"] >= 2


def test_delete_thread_history():
    """Verify DELETE /chat/history/{thread_id} resets state."""
    thread_id = "test-session-to-clear"
    # First create a message
    client.post("/chat", json={"message": "Save this message", "thread_id": thread_id})
    # Now clear it
    del_res = client.delete(f"/chat/history/{thread_id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["cleared"] is True


def test_chat_validation():
    """Verify invalid payloads return validation error (HTTP 422)."""
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_stream_endpoint():
    """Verify /chat/stream returns text/event-stream with thread and done events."""
    thread_id = "test-stream-thread-suite"
    payload = {
        "message": "Stream test message",
        "thread_id": thread_id
    }
    with client.stream("POST", "/chat/stream", json=payload) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = "".join([chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in response.iter_text()])
        assert "event: thread" in body
        assert thread_id in body
        assert "event: done" in body


def test_run_agent_direct():
    """Verify run_agent in app.agent.main executes directly and maintains memory."""
    thread_id = "direct-agent-test-suite"
    result = run_agent("Hello from direct agent test", thread_id=thread_id)
    assert "response" in result
    assert result["thread_id"] == thread_id
    assert result["total_messages"] >= 2
