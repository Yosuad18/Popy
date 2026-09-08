"""Punto de entrada principal para el agente LangGraph.

Permite ejecutar el agente interactivamente desde la consola o como servicio.
"""

import sys
import uuid
from typing import Optional, Dict, Any
from langchain_core.messages import HumanMessage
from app.agent.graph import graph


# Configurar codificación UTF-8 para consolas Windows si es necesario
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_agent(
    message: str,
    thread_id: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """Ejecuta un ciclo del agente con el mensaje proporcionado.
    
    Args:
        message: El texto del usuario.
        thread_id: Identificador de la sesión/hilo para memoria multi-turno.
        system_prompt: Instrucción opcional del sistema.
        
    Returns:
        Dict con la respuesta del agente y el thread_id utilizado.
    """
    session_id = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    inputs = {
        "messages": [HumanMessage(content=message)],
        "system_prompt": system_prompt,
    }

    final_state = graph.invoke(inputs, config=config)
    messages = final_state.get("messages", [])
    last_content = messages[-1].content if messages else "No response generated."

    return {
        "response": str(last_content),
        "thread_id": session_id,
        "total_messages": len(messages)
    }


def interactive_cli():
    """Modo interactivo en consola para conversar directamente con el agente."""
    session_id = f"cli-{uuid.uuid4().hex[:6]}"
    print("=" * 60)
    print("[LangGraph Agent] - Modo Consola Interactivo")
    print(f"ID de sesion: {session_id}")
    print("Escribe tu pregunta o 'salir' para terminar.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nTú: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("salir", "exit", "quit"):
                print("¡Hasta luego!")
                break

            result = run_agent(message=user_input, thread_id=session_id)
            print(f"\nAgente:\n{result['response']}")

        except (KeyboardInterrupt, EOFError):
            print("\n¡Hasta luego!")
            break


if __name__ == "__main__":
    if "--serve" in sys.argv:
        import uvicorn
        from app.config import settings
        print(f"Iniciando servidor FastAPI en http://{settings.HOST}:{settings.PORT} ...")
        uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
    else:
        interactive_cli()
