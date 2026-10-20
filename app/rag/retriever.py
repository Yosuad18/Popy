"""Retriever RAG multi-colección contra Chroma Cloud (Popy restaurante).

Colecciones: menu, usuarios, pedidos, descuentos (embeddings Qwen).
Los descuentos se filtran programáticamente por fecha de vigencia.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.data.chroma_client import get_chroma_client, get_qwen_embedding_function
from app.data.restaurant_data import COLLECTIONS, today_iso

load_dotenv()

N_RESULTS_PER_COLLECTION = 3


def get_collection(name: str):
    """Returns a restaurant collection with Qwen embeddings (Chroma Cloud)."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        embedding_function=get_qwen_embedding_function(),
    )


def _query_collection(name: str, query: str, where: dict | None = None) -> list[dict]:
    """Consulta una colección y retorna hits con collection/document/metadata/distance."""
    collection = get_collection(name)
    kwargs = {
        "query_texts": [query],
        "n_results": N_RESULTS_PER_COLLECTION,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    results = collection.query(**kwargs)

    docs = (results.get("documents") or [[]])[0] or []
    metas = (results.get("metadatas") or [[]])[0] or []
    dists = (results.get("distances") or [[]])[0] or []
    return [
        {"collection": name, "document": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(docs, metas, dists)
    ]


def _collect_hits(query: str) -> list[dict]:
    """Consulta las 4 colecciones; descuentos solo con vigencia actual (filtro en Python)."""
    today = today_iso()
    all_hits: list[dict] = []

    for name in COLLECTIONS.keys():
        try:
            if name == "Descuentos":
                # Chroma $lte/$gte solo acepta números; filtramos fechas ISO en Python
                collection = get_collection(name)
                results = collection.get(include=["documents", "metadatas"])
                docs = results.get("documents") or []
                metas = results.get("metadatas") or []
                for doc, meta in zip(docs, metas):
                    if meta.get("fecha_inicio", "") <= today <= meta.get("fecha_fin", "9999-99-99"):
                        all_hits.append({
                            "collection": name,
                            "document": doc,
                            "metadata": meta,
                            "distance": 0.0,
                        })
            else:
                all_hits.extend(_query_collection(name, query))
        except Exception:
            continue

    all_hits.sort(key=lambda h: h["distance"])
    return all_hits


def get_menu_item_by_id(item_id: int) -> str:
    """Busca un plato/bebida del menú por su item_id."""
    try:
        collection = get_collection("Menu")
        results = collection.get(
            where={"item_id": item_id},
            limit=1,
            include=["documents"],
        )
    except Exception as e:
        return f"No pude consultar el menú en este momento. Detalle: {e}"

    documents = results.get("documents") or []
    if not documents:
        return f"No se encontró ningún plato con el número {item_id} en el menú."
    return f"Plato número {item_id} del menú: {documents[0]}"


def _extract_item_id(query: str) -> int | None:
    """Detecta si la consulta se refiere a un plato por número (ej. 'plato 3', 'producto 3')."""
    import re
    match = re.search(r"(?:plato|producto|item|men[uú])\s*#?\s*(\d+)", query, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def ask_popy_bot(query: str) -> str:
    """Consulta semántica a las colecciones de Chroma Cloud y responde con el LLM."""
    item_id = _extract_item_id(query)
    if item_id is not None:
        try:
            context = get_menu_item_by_id(item_id)
            if not context.startswith("No "):
                question = (
                    f"El usuario preguntó por el plato con número {item_id}. "
                    f"Contexto del plato:\n{context}\n\nConsulta original: {query}"
                )
                return _answer_with_llm(context, question)
        except Exception:
            pass

    hits = _collect_hits(query)
    if not hits:
        return "No se encontraron coincidencias en el menú, usuarios, pedidos o descuentos."

    context_parts = []
    for h in hits:
        tag = h["collection"].upper()
        context_parts.append(f"[{tag}]\n{h['document']}")
    context = "\n---\n".join(context_parts)

    return _answer_with_llm(context, query)


def _answer_with_llm(context: str, question: str) -> str:
    """Genera la respuesta final con el LLM a partir del contexto recuperado."""
    prompt = ChatPromptTemplate.from_template("""
    Usa ÚNICAMENTE el siguiente contexto recuperado de la base de datos (menú, usuarios, pedidos y descuentos vigentes de Popy) para responder la consulta del usuario.
    Si no hay suficiente información en el contexto, responde amablemente que no dispones de ese dato. No inventes precios, promociones ni datos de usuarios.

    Contexto:
    {context}

    Consulta:
    {question}
    """)

    api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
    chain = prompt | llm | StrOutputParser()

    return chain.invoke({"context": context, "question": question})
