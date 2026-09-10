# app/rag/retriever.py
import os
import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

def get_retriever():
    # 1. Asegurar la clave de API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY no encontrada en las variables de entorno.")

    # 2. Instanciar cliente e embeddings DENTRO de la función
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key
    )

    chroma_client = chromadb.HttpClient(
        host=os.getenv("CHROMA_SERVER_HOST", "https://api.trychroma.com"),
        headers={"x-chroma-token": os.getenv("CHROMA_API_KEY")},
        tenant=os.getenv("CHROMA_TENANT", "default_tenant"),
        database=os.getenv("CHROMA_DATABASE", "default_database")
    )

    vector_store = Chroma(
        client=chroma_client,
        collection_name="ecommerce_data",
        embedding_function=embeddings
    )

    return vector_store.as_retriever(search_kwargs={"k": 5})

def ask_ecommerce_bot(query: str) -> str:
    retriever = get_retriever()
    docs = retriever.invoke(query)
    
    if not docs:
        return "No se encontraron coincidencias en la base de datos."
    
    return "\n---\n".join([doc.page_content for doc in docs])