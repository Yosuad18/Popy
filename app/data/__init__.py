"""E-commerce data: product catalog and knowledge base."""

from app.data.knowledge_base import KNOWLEDGE_BASE, search_knowledge_base
from app.data.products import PRODUCTS, search_products, get_product_by_id
from app.data.vector_store import ingest_all, search

__all__ = [
    "KNOWLEDGE_BASE",
    "PRODUCTS",
    "search_knowledge_base",
    "search_products",
    "get_product_by_id",
    "ingest_all",
    "search",
]
