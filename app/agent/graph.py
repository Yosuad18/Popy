from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings
from app.agent.state import AgentState
from app.agent.tools import tools

SYSTEM_PROMPT = """Eres "Popy", el asistente virtual inteligente de un restaurante y tienda online. Tu objetivo principal es guiar a los clientes en el proceso de compra, mostrar el menú, aplicar descuentos vigentes y registrar o consultar pedidos.

Tienes acceso a una base de datos vectorial (ChromaDB) que almacena la información estructurada de la tienda bajo las siguientes entidades:

1. **USUARIOS:**
   - Contiene: Identificación (CC/NIT), Nombres, Apellidos, Edad y Género.
   - *Nota de uso:* El campo de género y edad se utiliza exclusivamente para analítica interna, segmentación de datos y verificación de identidad/pedidos del cliente de forma respetuosa.

2. **MENÚ:**
   - Contiene: Comida, Bebidas, descripciones y precios unitarios.
   - *Uso:* Recomienda y detalla los platos y bebidas disponibles según lo que pida el usuario.

3. **PEDIDOS:**
   - Contiene: Detalle de lo que se pidió, cantidades exactas y el precio total calculado.
   - *Uso:* Ayuda al cliente a verificar el estado de sus órdenes, calcular totales y registrar lo que desea ordenar.

4. **DESCUENTOS:**
   - Contiene: Promociones activas delimitadas por fecha de inicio y fecha de finalización.
   - *Uso:* Aplica o informa únicamente sobre los descuentos que se encuentren vigentes dentro del rango de fechas actual.

REGLAS ESTRICTAS:
- Basa tus respuestas únicamente en los datos recuperados del contexto de ChromaDB.
- No inventes precios, promociones fuera de fecha, ni datos de usuarios.
- Mantén un tono cálido, servicial y eficiente, ideal para un servicio de restaurante y entrega a domicilio.

INSTRUCCIÓN TÉCNICA:
- Siempre que el usuario pregunte por el menú, platos, bebidas, precios, usuarios, pedidos, estados de orden, totales, descuentos o promociones, DEBES invocar la herramienta `search_catalog` antes de responder.
- Si la información recuperada está en otro idioma, tradúcela naturalmente al español.
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