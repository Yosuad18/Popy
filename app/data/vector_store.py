"""Vector store module for ingesting and searching e-commerce data via ChromaDB Cloud."""

from app.data.chroma_client import get_collection

_collection = None


def get_collection_instance():
    """Returns the singleton ecommerce collection."""
    global _collection
    if _collection is None:
        _collection = get_collection("ecommerce")
    return _collection


def ingest_products():
    """Ingest all products into the ChromaDB collection, skipping existing IDs."""
    from app.data.products import PRODUCTS
    collection = get_collection_instance()
    existing = collection.get(ids=[f"product_{p['id']}" for p in PRODUCTS])
    existing_ids = set(existing.get("ids", []))
    ids, documents, metadatas = [], [], []

    for product in PRODUCTS:
        doc_id = f"product_{product['id']}"
        if doc_id in existing_ids:
            continue
        ids.append(doc_id)
        text = f"{product['name']}. {product['description']}. Category: {product['category']}. Price: ${product['price']}. Stock: {product['stock']}."
        documents.append(text)
        metadatas.append({
            "type": "product",
            "product_id": product["id"],
            "category": product["category"],
            "name": product["name"],
            "price": str(product["price"]),
        })

    if documents:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)


def ingest_knowledge_base():
    """Ingest all knowledge base entries into the ChromaDB collection, skipping existing IDs."""
    from app.data.knowledge_base import KNOWLEDGE_BASE
    collection = get_collection_instance()
    existing = collection.get(ids=[f"kb_{e['topic']}" for e in KNOWLEDGE_BASE])
    existing_ids = set(existing.get("ids", []))
    ids, documents, metadatas = [], [], []

    for entry in KNOWLEDGE_BASE:
        doc_id = f"kb_{entry['topic']}"
        if doc_id in existing_ids:
            continue
        ids.append(doc_id)
        documents.append(entry["content"])
        metadatas.append({
            "type": "knowledge",
            "topic": entry["topic"],
        })

    if documents:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)


def ingest_all():
    """Ingest all products and knowledge base documents into the collection."""
    ingest_products()
    ingest_knowledge_base()


def search(query: str, n: int = 5) -> list[dict]:
    """Search the collection for the top n results matching the query."""
    collection = get_collection_instance()
    results = collection.query(query_texts=query, n_results=n)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    hits = []
    for i in range(len(documents)):
        hits.append({
            "document": documents[i],
            "metadata": metadatas[i],
            "distance": distances[i],
        })
    return hits