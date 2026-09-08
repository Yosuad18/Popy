"""Herramientas que el agente LangGraph puede invocar."""

import datetime
import ast
import operator
from typing import Dict
from langchain_core.tools import tool

# Almacén de notas en memoria para el agente
_NOTES_STORAGE: Dict[str, str] = {}


@tool
def get_current_time() -> str:
    """Retorna la fecha y hora actual en formato estándar (YYYY-MM-DD HH:MM:SS).
    Útil cuando el usuario pregunta la hora, fecha o día actual.
    """
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


# Operadores permitidos para evaluación matemática segura
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Solo se permiten constantes numéricas")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            left = _safe_eval_node(node.left)
            right = _safe_eval_node(node.right)
            return _ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"Operador {op_type.__name__} no permitido")
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            operand = _safe_eval_node(node.operand)
            return _ALLOWED_OPERATORS[op_type](operand)
        raise ValueError(f"Operador {op_type.__name__} no permitido")
    else:
        raise ValueError(f"Expresión {type(node).__name__} no permitida")


@tool
def calculate(expression: str) -> str:
    """Calcula expresiones aritméticas de forma segura (por ejemplo: '24 * 7' o '(10 + 5) / 2')."""
    try:
        clean_expr = expression.strip()
        parsed = ast.parse(clean_expr, mode='eval')
        result = _safe_eval_node(parsed.body)
        return str(result)
    except Exception as exc:
        return f"Error al calcular '{expression}': {str(exc)}"


@tool
def get_weather(city: str) -> str:
    """Consulta el clima y pronostico actual de una ciudad dada."""
    clean_city = city.strip().title()
    # Simulación inteligente de clima con datos realistas
    weather_samples = {
        "Bogota": "17°C, Nublado con probabilidad de lluvias ligeras (Humedad: 75%)",
        "Madrid": "24°C, Soleado y despejado (Humedad: 40%)",
        "Ciudad De Mexico": "22°C, Parcialmente nublado (Humedad: 55%)",
        "Buenos Aires": "19°C, Despejado (Humedad: 60%)",
        "Lima": "20°C, Niebla matutina templada (Humedad: 82%)",
        "Medellin": "25°C, Agradable y soleado (Humedad: 65%)",
    }
    info = weather_samples.get(clean_city, f"22°C, Clima templado y condiciones favorables en {clean_city}")
    return f"Clima actual en {clean_city}: {info}."


@tool
def save_note(title: str, content: str) -> str:
    """Guarda una nota o dato clave en el cuaderno de memoria del agente."""
    key = title.strip().lower()
    _NOTES_STORAGE[key] = content.strip()
    return f"Nota '{title}' guardada exitosamente."


@tool
def get_notes() -> str:
    """Lista todas las notas y recordatorios guardados en la memoria del agente."""
    if not _NOTES_STORAGE:
        return "No hay notas guardadas en este momento."
    items = [f"- {title.capitalize()}: {body}" for title, body in _NOTES_STORAGE.items()]
    return "Notas guardadas:\n" + "\n".join(items)


@tool
def search_knowledge(query: str) -> str:
    """Busca en la base de conocimientos integrada información sobre FastAPI, LangGraph y LangChain."""
    q = query.lower()
    knowledge_base = {
        "langgraph": (
            "LangGraph es una biblioteca para construir aplicaciones multi-agente con estado y ciclos. "
            "Extiende LangChain permitiendo modelar flujos de trabajo como grafos dirigidos (StateGraph) "
            "con persistencia de sesiones mediante checkpointers (ej. MemorySaver)."
        ),
        "fastapi": (
            "FastAPI es un framework web moderno y rápido para construir APIs con Python 3.8+ "
            "basado en anotaciones de tipo estándar y Pydantic, con soporte nativo para async/await y OpenAPI/Swagger."
        ),
        "langchain": (
            "LangChain es un framework para desarrollar aplicaciones impulsadas por modelos de lenguaje (LLMs), "
            "ofreciendo abstracciones para prompts, modelos, herramientas, memoria y cadenas de razonamiento."
        ),
        "pydantic": (
            "Pydantic es la biblioteca de validación de datos más utilizada en Python, "
            "permitiendo definir esquemas tipados robustos con serialización rápida basada en Rust (pydantic-core)."
        ),
    }

    results = []
    for topic, text in knowledge_base.items():
        if topic in q or any(word in text.lower() for word in q.split()):
            results.append(f"[{topic.upper()}]: {text}")

    if results:
        return "\n\n".join(results)
    return f"No se encontró información específica para '{query}'. Temas disponibles: LangGraph, FastAPI, LangChain, Pydantic."


# Lista completa de herramientas exportadas
tools = [get_current_time, calculate, get_weather, save_note, get_notes, search_knowledge]
