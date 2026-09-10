from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. Conectar a la misma colección donde hiciste la ingesta
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = Chroma(
    client=chroma_client, # Tu cliente configurado de Chroma Cloud
    collection_name="ecommerce_data",
    embedding_function=embeddings
)

# 2. Crear el retriever
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# 3. Prompt estricto para evitar alucinaciones
system_prompt = """
Eres un asistente de e-commerce. Responde a la pregunta del usuario utilizando ÚNICAMENTE la siguiente información de contexto recuperada de la base de datos.
Si la información no está en el contexto, di claramente "No encontré información sobre eso en la base de datos".

Contexto:
{context}

Pregunta: {question}
"""

prompt = ChatPromptTemplate.from_template(system_prompt)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 4. Cadena RAG
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Al preguntar esto, ahora usará los datos reales (Laptop Legion 5, Smartphone S24, etc.)
# respuesta = rag_chain.invoke("¿Qué productos tienes disponibles?")