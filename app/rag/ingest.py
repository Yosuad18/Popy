import re
from typing import List
from pydantic import BaseModel

from langchain_core.documents import Document

from app.data.chroma_client import get_chroma_client, get_qwen_embedding_function

COLLECTION_NAME = "ecommerce"


def _slug(text: str) -> str:
    """Convierte un texto en un slug apto para IDs de Chroma."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


class Producto(BaseModel):
    nombre: str
    valor: float
    unidades_disponibles: int
    color: str
    marca: str

    @property
    def doc_id(self) -> str:
        return f"producto_{_slug(self.nombre)}"

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

    @property
    def doc_id(self) -> str:
        return f"usuario_{self.cedula}"

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

    @property
    def doc_id(self) -> str:
        return f"repartidor_{self.cedula}"

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

    @property
    def doc_id(self) -> str:
        return f"pago_{_slug(self.entidad)}_{_slug(self.fecha)}"

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
    """Ingiere los datos demo en español a la colección 'ecommerce' (IDs fijos, sin duplicados)."""
    print("🚀 Iniciando proceso de ingesta a Chroma Cloud...")

    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_qwen_embedding_function(),
    )

    items: List[BaseModel] = (
        productos_data + usuarios_data + repartidores_data + metodos_pago_data
    )
    doc_ids = [item.doc_id for item in items]

    existing = collection.get(ids=doc_ids)
    existing_ids = set(existing.get("ids", []))

    ids, documents, metadatas = [], [], []
    for item in items:
        if item.doc_id in existing_ids:
            continue
        doc = item.to_document()
        ids.append(item.doc_id)
        documents.append(doc.page_content)
        metadatas.append(doc.metadata)

    if not documents:
        print(f"✅ Nada que hacer: los {len(doc_ids)} documentos ya existen en '{COLLECTION_NAME}'.")
        return

    print(f"📦 Subiendo {len(documents)} documentos nuevos a '{COLLECTION_NAME}'...")
    collection.add(ids=ids, documents=documents, metadatas=metadatas)

    print(f"✅ Ingesta completada. Colección '{COLLECTION_NAME}': {collection.count()} documentos totales.")


if __name__ == "__main__":
    run_ingestion()