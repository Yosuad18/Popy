"""Definición de nodos y bordes con LangGraph."""

from typing import Literal, List
from langchain_core.messages import AIMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.agent.state import AgentState
from app.agent.tools import tools, search_catalog, get_product_details, view_cart, search_knowledge


def is_openai_configured() -> bool:
    """Verifica si existe una clave de OpenAI configurada."""
    key = settings.OPENAI_API_KEY
    if not key or not key.strip():
        return False
    if "your_openai_api_key" in key.lower():
        return False
    return True


def call_model(state: AgentState) -> dict:
    """Nodo que invoca al modelo de lenguaje o proporciona modo demo con ejecución de herramientas si no hay clave."""
    messages: List[BaseMessage] = list(state.get("messages", []))
    system_prompt = state.get("system_prompt")

    # Inyectar prompt de sistema si se especifica y no está ya presente
    if system_prompt:
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + messages

    # Si no hay API key configurada, responder en modo demostración con vista previa de herramientas
    if not is_openai_configured():
        raw_msg = messages[-1].content if messages else ""
        lower_msg = raw_msg.lower()

        tool_preview = ""
        if any(w in lower_msg for w in ["producto", "busca", "buscar", "catalogo", "catalog", "tienes"]):
            query = raw_msg
            tool_preview = f"\n\n[Ejecución de herramienta search_catalog]:\n{search_catalog.invoke({'query': query})}"
        elif any(w in lower_msg for w in ["carrito", "carro", "cart"]):
            tool_preview = f"\n\n[Ejecución de herramienta view_cart]:\n{view_cart.invoke({'config': {}})}"
        elif any(w in lower_msg for w in ["envio", "devolver", "pago", "politica", "policy", "envios"]):
            tool_preview = f"\n\n[Ejecución de herramienta search_knowledge]:\n{search_knowledge.invoke({'query': raw_msg})}"

        demo_response = (
            "[MODO DEMO - Clave de OpenAI no configurada]\n\n"
            f"Mensaje recibido: '{raw_msg}'.{tool_preview}\n\n"
            "Para conectar con OpenAI:\n"
            "1. Abre el archivo `.env` en la raíz del proyecto.\n"
            "2. Define `OPENAI_API_KEY=sk-...` con tu clave de OpenAI.\n"
            "3. Reinicia la aplicación.\n\n"
            "El grafo de LangGraph, memoria checkpointer y herramientas de e-commerce están listos y funcionando!"
        )
        return {"messages": [AIMessage(content=demo_response)]}

    # Inicializar cliente ChatOpenAI
    model = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY
    )

    # Vincular herramientas al modelo
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Borde condicional que decide si invocar herramientas o finalizar el turno."""
    messages = state.get("messages", [])
    if not messages:
        return "__end__"
    last_message = messages[-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return "__end__"


def create_agent_graph():
    """Construye y compila el StateGraph con nodos, bordes y checkpointer de memoria."""
    workflow = StateGraph(AgentState)

    # 1. Agregar nodos
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))

    # 2. Definir flujo y bordes
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END
        }
    )
    workflow.add_edge("tools", "agent")

    # 3. Checkpointer en memoria para persistencia multi-turno
    checkpointer = MemorySaver()

    # 4. Compilar el grafo
    return workflow.compile(checkpointer=checkpointer)


# Instancia singleton del grafo compilado
graph = create_agent_graph()


def get_graph_mermaid() -> str:
    """Genera la representación del flujo del grafo en sintaxis Mermaid."""
    try:
        return graph.get_graph().draw_mermaid()
    except Exception:
        return (
            "graph TD\n"
            "    __start__([__start__]) --> agent\n"
            "    agent --> tools\n"
            "    agent --> __end__([__end__])\n"
            "    tools --> agent\n"
        )
