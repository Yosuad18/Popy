"""Ingesta y búsqueda multi-colección en Chroma Cloud (Popy restaurante)."""

from typing import List, Dict, Any

from app.data.chroma_client import get_chroma_client, get_qwen_embedding_function
from app.data.restaurant_data import COLLECTIONS


def get_collection_instance(name: str):
    """Returns or creates a restaurant collection with Qwen embeddings."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        embedding_function=get_qwen_embedding_function(),
    )


def ingest_all() -> None:
    """Ingiere los 4 datasets del restaurante, omitiendo IDs ya existentes."""
    client = get_chroma_client()
    qwen_ef = get_qwen_embedding_function()

    for collection_name, docs_fn in COLLECTIONS.items():
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=qwen_ef,
        )
        pairs = docs_fn()
        doc_ids = [doc_id for doc_id, _ in pairs]

        existing = collection.get(ids=doc_ids)
        existing_ids = set(existing.get("ids", []))

        ids, documents, metadatas = [], [], []
        for doc_id, doc in pairs:
            if doc_id in existing_ids:
                continue
            ids.append(doc_id)
            documents.append(doc.page_content)
            metadatas.append(doc.metadata)

        if ids:
            collection.add(ids=ids, documents=documents, metadatas=metadatas)
            print(f"[Popy] Colección '{collection_name}': +{len(ids)} docs (total {collection.count()})")
        else:
            print(f"[Popy] Colección '{collection_name}': sin cambios ({collection.count()} docs)")


def search(query: str, n: int = 3, collections: List[str] | None = None) -> List[Dict[str, Any]]:
    """Busca en una o varias colecciones y mezcla los resultados por distancia."""
    names = collections or list(COLLECTIONS.keys())
    client = get_chroma_client()
    qwen_ef = get_qwen_embedding_function()

    hits: List[Dict[str, Any]] = []
    for name in names:
        collection = client.get_or_create_collection(name=name, embedding_function=qwen_ef)
        results = collection.query(
            query_texts=[query],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        docs = (results.get("documents") or [[]])[0] or []
        metas = (results.get("metadatas") or [[]])[0] or []
        dists = (results.get("distances") or [[]])[0] or []
        for doc, meta, dist in zip(docs, metas, dists):
            hits.append({"collection": name, "document": doc, "metadata": meta, "distance": dist})

    hits.sort(key=lambda h: h["distance"])
    return hits
