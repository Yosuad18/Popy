from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.agent.state import AgentState
from app.agent.tools import tools

SYSTEM_PROMPT = """Eres el asistente virtual oficial de nuestro E-Commerce.
Tu objetivo es ayudar a los usuarios a consultar productos, gestionar su carrito y realizar pedidos.

Instrucciones de comportamiento:
1. Siempre que un usuario pregunte por productos, precios, usuarios, repartidores o métodos de pago, DEBES invocar la herramienta `search_catalog`.
2. Responde ÚNICAMENTE con la información devuelta por tus herramientas. No inventes productos ni precios que no estén en la base de datos.
3. Sé amable, conciso y directo en tus respuestas.
"""

def is_openai_configured() -> bool:
    return bool(settings.OPENAI_API_KEY)

def agent_node(state: AgentState):
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).bind_tools(tools)

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

memory = MemorySaver()

graph = workflow.compile(checkpointer=memory)

def get_graph_mermaid() -> str:
    return graph.get_graph().draw_mermaid()