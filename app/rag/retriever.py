"""Retriever RAG contra Chroma Cloud (colección 'ecommerce', embeddings Qwen)."""

import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.data.chroma_client import get_chroma_client, get_qwen_embedding_function

load_dotenv()

COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "ecommerce")
N_RESULTS = 5


def get_collection():
    """Returns the ecommerce collection with Qwen embeddings (Chroma Cloud)."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_qwen_embedding_function(),
    )


def get_product_by_id(product_id: int) -> str:
    """Busca un producto por su product_id en los metadatos de Chroma Cloud."""
    try:
        collection = get_collection()
        results = collection.get(
            where={"product_id": product_id},
            limit=1,
            include=["documents", "metadatas"],
        )
    except Exception as e:
        return f"No pude consultar la base de datos vectorial en este momento. Detalle: {e}"

    documents = results.get("documents") or []
    if not documents:
        return f"No se encontró ningún producto con ID {product_id} en el catálogo."

    return documents[0]


def _extract_product_id(query: str) -> int | None:
    """Detecta si la consulta se refiere a un producto por número de ID."""
    match = re.search(r"(?:producto|product)\s*#?\s*(\d+)", query, re.IGNORECASE)
    if match:
        return int(match.group(1))
    if re.fullmatch(r"\d+", query.strip()):
        return int(query.strip())
    return None


def ask_ecommerce_bot(query: str) -> str:
    """Consulta semántica a Chroma Cloud y responde con el LLM usando solo el contexto recuperado."""
    product_id = _extract_product_id(query)
    if product_id is not None:
        try:
            context = get_product_by_id(product_id)
            if not context.startswith("No "):
                question = f"El usuario preguntó por el producto con ID {product_id}. Contexto del producto:\n{context}\n\nConsulta original: {query}"
                return _answer_with_llm(context, question)
        except Exception:
            pass

    try:
        collection = get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=N_RESULTS,
            include=["documents", "metadatas"],
        )
    except Exception as e:
        return f"No pude consultar la base de datos vectorial en este momento. Detalle: {e}"

    documents = (results.get("documents") or [[]])[0] or []
    if not documents:
        return "No se encontraron coincidencias en el catálogo o base de datos."

    context = "\n---\n".join(documents)
    return _answer_with_llm(context, query)


def _answer_with_llm(context: str, question: str) -> str:
    """Genera la respuesta final con el LLM a partir del contexto recuperado."""
    prompt = ChatPromptTemplate.from_template("""
    Usa ÚNICAMENTE el siguiente contexto recuperado de la base de datos para responder la consulta del usuario.
    Si no hay suficiente información, responde que no dispones de ese dato.

    Contexto:
    {context}

    Consulta:
    {question}
    """)

    api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
    chain = prompt | llm | StrOutputParser()

    return chain.invoke({"context": context, "question": question})
