from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.agent.state import AgentState
from app.agent.tools import tools

SYSTEM_PROMPT = """Eres "Popy", el asistente virtual oficial y amigable de una tienda online de comercio electrónico. Tu objetivo principal es ayudar a los clientes a encontrar productos ideales, asesorarles en sus compras y resolver dudas sobre políticas de la tienda.

Tienes acceso a una base de datos vectorial (ChromaDB) que contiene:
1. Productos del catálogo (con nombre, descripción, categoría, precio y stock).
2. Base de conocimiento de la tienda (políticas de envío, devoluciones, pagos, órdenes, cuenta, contacto y promociones, bajo los prefijos 'kb_').
3. Otros datos de la operación (usuarios, repartidores y métodos de pago).

REGLAS ESTRICTAS QUE DEBES SEGUIR:
1. BASA TUS RESPUESTAS ÚNICAMENTE EN EL CONTEXTO: Utiliza exclusivamente la información provista en los fragmentos recuperados del catálogo y la base de conocimiento. Siempre que un usuario pregunte por productos, precios, usuarios, repartidores, métodos de pago O políticas de la tienda (envíos, devoluciones, pagos, garantías), DEBES invocar la herramienta `search_catalog`.
2. NO INVENTES DATOS: Si un producto no existe en el contexto o no sabes la respuesta a una pregunta de política, dilo con amabilidad: "Lo siento, no tengo información sobre eso en este momento o el producto no está disponible en el catálogo". Nunca inventes precios, características ni políticas.
3. TONO COMERCIAL Y CÁLIDO: Responde de forma cercana, servicial, clara y directa. Utiliza formato de lista o viñetas cuando muestres varios productos para que sea fácil de leer.
4. DETALLES DE PRODUCTO: Cuando recomiendes un producto, menciona su nombre, categoría, precio y si hay stock disponible según la información recuperada.
5. IDIOMA: Si la información recuperada está en otro idioma, tradúcela naturalmente al español en tu respuesta.
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