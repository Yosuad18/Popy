import os
import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def get_retriever():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY no configurada.")

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
        return "No se encontraron coincidencias en el catálogo o base de datos."
    
    context = "\n---\n".join([doc.page_content for doc in docs])

    prompt = ChatPromptTemplate.from_template("""
    Usa ÚNICAMENTE el siguiente contexto recuperado de la base de datos para responder la consulta del usuario.
    Si no hay suficiente información, responde que no dispones de ese dato.

    Contexto:
    {context}

    Consulta:
    {question}
    """)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | llm | StrOutputParser()
    
    return chain.invoke({"context": context, "question": query})