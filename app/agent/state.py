"""Define el estado del grafo para el agente LangGraph."""

from typing import Annotated, Sequence, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Estado del agente que rastrea el historial de mensajes y el contexto."""

    # Annotated con add_messages para añadir mensajes al historial en lugar de sobreescribirlos
    messages: Annotated[Sequence[BaseMessage], add_messages]
    system_prompt: Optional[str]
