import os
import uuid
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

load_dotenv()

class Producto(BaseModel):
    nombre: str
    valor: float
    unidades_disponibles: int
    color: str
    marca: str

    def to_document(self) -> Document:
        content = (
            f"Producto: {self.nombre}. Marca: {self.marca}. "
            f"Color: {self.color}. Precio: ${self.valor:.2f}. "
            f"Stock: {self.unidades_disponibles} unidades disponibles."
        )
        metadata = {
            "entity_type": "producto",
            "nombre": self.nombre,
            "valor": self.valor,
            "unidades_disponibles": self.unidades_disponibles,
            "color": self.color,
            "marca": self.marca
        }
        return Document(page_content=content, metadata=metadata)


class Usuario(BaseModel):
    nombre: str
    apellido: str
    cedula: str
    telefono: str
    edad: int
    residencia: str

    def to_document(self) -> Document:
        content = (
            f"Usuario: {self.nombre} {self.apellido}. Cédula: {self.cedula}. "
            f"Edad: {self.edad} años. Ciudad/Residencia: {self.residencia}. "
            f"Teléfono de contacto: {self.telefono}."
        )
        metadata = {
            "entity_type": "usuario",
            "cedula": self.cedula,
            "nombre_completo": f"{self.nombre} {self.apellido}",
            "residencia": self.residencia,
            "edad": self.edad
        }
        return Document(page_content=content, metadata=metadata)


class Repartidor(BaseModel):
    nombre: str
    apellido: str
    cedula: str
    vehiculo: str
    placa: str
    email: str

    def to_document(self) -> Document:
        content = (
            f"Repartidor: {self.nombre} {self.apellido}. Cédula: {self.cedula}. "
            f"Vehículo: {self.vehiculo} con placa {self.placa}. "
            f"Email de contacto: {self.email}."
        )
        metadata = {
            "entity_type": "repartidor",
            "cedula": self.cedula,
            "vehiculo": self.vehiculo,
            "placa": self.placa,
            "email": self.email
        }
        return Document(page_content=content, metadata=metadata)


class MetodoPago(BaseModel):
    entidad: str
    fecha: str  
    valor: float

    def to_document(self) -> Document:
        content = (
            f"Transacción/Método de Pago: Entidad bancaria/financiera {self.entidad}. "
            f"Fecha del pago: {self.fecha}. Valor procesado: ${self.valor:.2f}."
        )
        metadata = {
            "entity_type": "metodo_pago",
            "entidad": self.entidad,
            "fecha": self.fecha,
            "valor": self.valor
        }
        return Document(page_content=content, metadata=metadata)

productos_data = [
    Producto(nombre="Laptop Gamer Legion 5", valor=4500000.0, unidades_disponibles=8, color="Negro", marca="Lenovo"),
    Producto(nombre="Smartphone Galaxy S24", valor=3200000.0, unidades_disponibles=15, color="Titanio", marca="Samsung"),
    Producto(nombre="Teclado Mecánico K3", valor=350000.0, unidades_disponibles=25, color="Gris", marca="Keychron")
]

usuarios_data = [
    Usuario(nombre="Carlos", apellido="Mendoza", cedula="1061789456", telefono="3124567890", edad=28, residencia="Popayán"),
    Usuario(nombre="Laura", apellido="Gómez", cedula="1002987654", telefono="3159876543", edad=24, residencia="Cali")
]

repartidores_data = [
    Repartidor(nombre="Andrés", apellido="Ríos", cedula="987654321", vehiculo="Motocicleta", placa="XYZ12F", email="a.rios@delivery.com"),
    Repartidor(nombre="Felipe", apellido="Torres", cedula="1122334455", vehiculo="Camioneta", placa="ABC789", email="f.torres@delivery.com")
]

metodos_pago_data = [
    MetodoPago(entidad="Bancolombia", fecha="2026-09-10", valor=350000.0),
    MetodoPago(entidad="Nequi", fecha="2026-09-09", valor=3200000.0)
]

def run_ingestion():
    print("🚀 Iniciando proceso de ingesta a Chroma Cloud...")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

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

    documents: List[Document] = []
    
    for item in productos_data + usuarios_data + repartidores_data + metodos_pago_data:
        documents.append(item.to_document())

    doc_ids = [str(uuid.uuid4()) for _ in documents]

    print(f"📦 Subiendo {len(documents)} documentos enriquecidos...")
    vector_store.add_documents(documents=documents, ids=doc_ids)

    print("✅ Ingesta completada con éxito en la colección 'ecommerce_data'.")


if __name__ == "__main__":
    run_ingestion()