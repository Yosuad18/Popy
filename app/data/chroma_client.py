"""ChromaDB Cloud client singleton with Qwen embedding function."""

import os
from dotenv import load_dotenv

import chromadb
from chromadb.utils.embedding_functions import ChromaCloudQwenEmbeddingFunction
from chromadb.utils.embedding_functions.chroma_cloud_qwen_embedding_function import ChromaCloudQwenEmbeddingModel

load_dotenv()

_qwen_ef = None
_client = None


def get_qwen_embedding_function() -> ChromaCloudQwenEmbeddingFunction:
    """Returns a singleton Chroma Cloud Qwen embedding function."""
    global _qwen_ef
    if _qwen_ef is None:
        _qwen_ef = ChromaCloudQwenEmbeddingFunction(
            model=ChromaCloudQwenEmbeddingModel.QWEN3_EMBEDDING_0p6B,
            task="nl_to_code",
        )
    return _qwen_ef


def get_chroma_client() -> chromadb.ClientAPI:
    """Returns a singleton ChromaDB Cloud client."""
    global _client
    if _client is None:
        _client = chromadb.CloudClient(
            tenant=os.getenv("CHROMA_TENANT"),
            database=os.getenv("CHROMA_DATABASE"),
            api_key=os.getenv("CHROMA_API_KEY"),
        )
    return _client


def get_collection(name: str = "ecommerce"):
    """Returns or creates a collection with Qwen embeddings."""
    client = get_chroma_client()
    embedding_function = get_qwen_embedding_function()
    return client.get_or_create_collection(name=name, embedding_function=embedding_function)