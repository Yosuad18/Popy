"""Datasets del restaurante Popy para las colecciones de Chroma Cloud.

Colecciones: menu, usuarios, pedidos, descuentos.
Cada registro expone doc_id determinístico y to_document() con
page_content + metadata para ingerir en Chroma.
"""

from datetime import date
from typing import List

from langchain_core.documents import Document


# ---------------------------------------------------------------------------
# MENÚ (comida, bebidas, postres) — precios en COP
# ---------------------------------------------------------------------------

MENU_ITEMS = [
    {"item_id": 1, "nombre": "Bandeja Paisa", "tipo": "comida", "precio": 18000,
     "descripcion": "Bandeja paisa: frijoles, arroz, carne molida, chicharrón, huevo frito, plátano maduro, aguacate y arepa."},
    {"item_id": 2, "nombre": "Ajiaco Santafereño", "tipo": "comida", "precio": 16000,
     "descripcion": "Ajiaco de pollo con papas criollas, mazorca, crema de leche y alcaparras. Receta bogotana."},
    {"item_id": 3, "nombre": "Sancocho de Gallina", "tipo": "comida", "precio": 15000,
     "descripcion": "Sancocho de gallina con yuca, plátano, papa, mazorca y cilantro. Porción generosa."},
    {"item_id": 4, "nombre": "Empanadas de Carne (x3)", "tipo": "comida", "precio": 6000,
     "descripcion": "Tres empanadas de carne molida con ají colombiano. Fritas al momento."},
    {"item_id": 5, "nombre": "Patacón con Chicharrón", "tipo": "comida", "precio": 13000,
     "descripcion": "Patacón pisado frito con chicharrón crocante, suero costeño y limón."},
    {"item_id": 6, "nombre": "Tamales Tolimenses", "tipo": "comida", "precio": 8000,
     "descripcion": "Tamal tolimense en hoja de plátano con pollo, cerdo, papas y arroz."},
    {"item_id": 7, "nombre": "Changua", "tipo": "comida", "precio": 7000,
     "descripcion": "Sopa de leche con huevo, cebollín y cilantro. Tradición de la madrugada en Bogotá."},
    {"item_id": 8, "nombre": "Arepa de Choclo con Queso", "tipo": "comida", "precio": 4000,
     "descripcion": "Arepa de maíz dulce asada con queso costeño derretido."},
    {"item_id": 9, "nombre": "Jugo Natural de Lulo", "tipo": "bebida", "precio": 5000,
     "descripcion": "Jugo natural de lulo servido frío. Sin conservantes."},
    {"item_id": 10, "nombre": "Limonada de Coco", "tipo": "bebida", "precio": 6000,
     "descripcion": "Limonada cremosa de coco fresco. Refrescante y natural."},
    {"item_id": 11, "nombre": "Tinto Campesino", "tipo": "bebida", "precio": 3000,
     "descripcion": "Tinto colombiano campesino con panela. Caliente o frío."},
    {"item_id": 12, "nombre": "Canelazo", "tipo": "bebida", "precio": 7000,
     "descripcion": "Bebida caliente de agua de canela, panela y clavo. Ideal para la noche."},
    {"item_id": 13, "nombre": "Malteada de Mora", "tipo": "bebida", "precio": 8000,
     "descripcion": "Malteada de mora silvestre con helado de vainilla."},
    {"item_id": 14, "nombre": "Postre de Natas", "tipo": "postre", "precio": 6000,
     "descripcion": "Postre tradicional de natas con canela y azúcar morena."},
    {"item_id": 15, "nombre": "Merengón", "tipo": "postre", "precio": 7000,
     "descripcion": "Merengón con crema de leche, frutas frescas y salsa de fresas."},
]


def menu_documents() -> List[tuple]:
    """Retorna (doc_id, Document) para cada plato/bebida del menú."""
    docs = []
    for item in MENU_ITEMS:
        content = (
            f"Plato del menú: {item['nombre']}. Tipo: {item['tipo']}. "
            f"Precio unitario: ${item['precio']:,} COP. {item['descripcion']}"
        )
        metadata = {
            "entity_type": "menu",
            "item_id": item["item_id"],
            "nombre": item["nombre"],
            "tipo": item["tipo"],
            "precio": item["precio"],
        }
        docs.append((
            f"menu_{item['nombre'].lower().replace(' ', '_').replace('(', '').replace(')', '')}",
            Document(page_content=content, metadata=metadata),
        ))
    return docs


# ---------------------------------------------------------------------------
# USUARIOS — CC/NIT, nombres, apellidos, edad, género (analítica interna)
# ---------------------------------------------------------------------------

USUARIOS = [
    {"identificacion": "1061789456", "nombres": "Carlos Andrés", "apellidos": "Mendoza Rojas", "edad": 28, "genero": "M"},
    {"identificacion": "1002987654", "nombres": "Laura Marcela", "apellidos": "Gómez Pérez", "edad": 24, "genero": "F"},
    {"identificacion": "1122334455", "nombres": "Andrés Felipe", "apellidos": "Pérez Torres", "edad": 35, "genero": "M"},
    {"identificacion": "79123456", "nombres": "María Elena", "apellidos": "Rojas Díaz", "edad": 41, "genero": "F"},
]


def usuarios_documents() -> List[tuple]:
    docs = []
    for u in USUARIOS:
        content = (
            f"Usuario: {u['nombres']} {u['apellidos']}. "
            f"Identificación (CC/NIT): {u['identificacion']}. "
            f"Edad: {u['edad']} años. Género: {u['genero']}."
        )
        metadata = {
            "entity_type": "usuario",
            "identificacion": u["identificacion"],
            "nombres": u["nombres"],
            "apellidos": u["apellidos"],
            "edad": u["edad"],
            "genero": u["genero"],
        }
        docs.append((f"usuario_{u['identificacion']}", Document(page_content=content, metadata=metadata)))
    return docs


# ---------------------------------------------------------------------------
# PEDIDOS — detalle, cantidades exactas, precio total, estado, fecha
# ---------------------------------------------------------------------------

PEDIDOS = [
    {"order_id": "ORD-2001", "cliente_cc": "1061789456",
     "detalle": "2x Bandeja Paisa, 1x Jugo de lulo",
     "cantidades": {"Bandeja Paisa": 2, "Jugo de lulo": 1},
     "total": 41000, "estado": "entregado", "fecha": "2026-10-15"},
    {"order_id": "ORD-2002", "cliente_cc": "1002987654",
     "detalle": "1x Ajiaco Santafereño, 1x Limonada de coco",
     "cantidades": {"Ajiaco Santafereño": 1, "Limonada de coco": 1},
     "total": 22000, "estado": "entregado", "fecha": "2026-10-16"},
    {"order_id": "ORD-2003", "cliente_cc": "1122334455",
     "detalle": "3x Empanadas de Carne, 2x Tinto Campesino",
     "cantidades": {"Empanadas de Carne": 3, "Tinto Campesino": 2},
     "total": 24000, "estado": "en preparación", "fecha": "2026-10-20"},
    {"order_id": "ORD-2004", "cliente_cc": "79123456",
     "detalle": "1x Sancocho de Gallina, 1x Canelazo, 1x Postre de Natas",
     "cantidades": {"Sancocho de Gallina": 1, "Canelazo": 1, "Postre de Natas": 1},
     "total": 28000, "estado": "enviado", "fecha": "2026-10-19"},
    {"order_id": "ORD-2005", "cliente_cc": "1061789456",
     "detalle": "1x Patacón con Chicharrón, 1x Malteada de Mora",
     "cantidades": {"Patacón con Chicharrón": 1, "Malteada de Mora": 1},
     "total": 21000, "estado": "en preparación", "fecha": "2026-10-20"},
]


def pedidos_documents() -> List[tuple]:
    docs = []
    for p in PEDIDOS:
        content = (
            f"Pedido {p['order_id']} del cliente con CC {p['cliente_cc']}. "
            f"Detalle: {p['detalle']}. Precio total: ${p['total']:,} COP. "
            f"Estado: {p['estado']}. Fecha: {p['fecha']}."
        )
        metadata = {
            "entity_type": "pedido",
            "order_id": p["order_id"],
            "cliente_cc": p["cliente_cc"],
            "detalle": p["detalle"],
            "total": p["total"],
            "estado": p["estado"],
            "fecha": p["fecha"],
        }
        docs.append((f"pedido_{p['order_id'].lower().replace('-', '_')}", Document(page_content=content, metadata=metadata)))
    return docs


# ---------------------------------------------------------------------------
# DESCUENTOS — promociones con fecha_inicio y fecha_fin (ISO)
# ---------------------------------------------------------------------------

DESCUENTOS = [
    {"codigo": "EMPO2X1", "titulo": "2x1 en Empanadas (martes)",
     "descripcion": "Todos los martes: compra una empanada y llévate otra gratis.",
     "fecha_inicio": "2026-10-01", "fecha_fin": "2026-12-31"},
    {"codigo": "ESTUDIANTE10", "titulo": "10% para estudiantes",
     "descripcion": "10% de descuento presentando carnet de estudiante vigente.",
     "fecha_inicio": "2026-09-01", "fecha_fin": "2026-12-15"},
    {"codigo": "HAPPY20", "titulo": "Happy Hour 20% en bebidas",
     "descripcion": "20% de descuento en todas las bebidas de 4:00 p.m. a 6:00 p.m.",
     "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31"},
    {"codigo": "COMBO2000", "titulo": "Combo Almuerzo $20.000",
     "descripcion": "Bandeja Paisa + Jugo Natural de Lulo por $20.000 (ahorras $3.000).",
     "fecha_inicio": "2026-10-01", "fecha_fin": "2026-11-30"},
    {"codigo": "VERANO15", "titulo": "15% de descuento de verano",
     "descripcion": "Promoción de verano: 15% en todo el menú.",
     "fecha_inicio": "2026-06-01", "fecha_fin": "2026-08-31"},
]


def descuentos_documents() -> List[tuple]:
    docs = []
    for d in DESCUENTOS:
        content = (
            f"Descuento: {d['titulo']}. Código: {d['codigo']}. {d['descripcion']} "
            f"Vigencia: del {d['fecha_inicio']} al {d['fecha_fin']}."
        )
        metadata = {
            "entity_type": "descuento",
            "codigo": d["codigo"],
            "titulo": d["titulo"],
            "fecha_inicio": d["fecha_inicio"],
            "fecha_fin": d["fecha_fin"],
        }
        docs.append((f"desc_{d['codigo'].lower()}", Document(page_content=content, metadata=metadata)))
    return docs


# ---------------------------------------------------------------------------
# Registro central de colecciones para la ingesta
# ---------------------------------------------------------------------------

COLLECTIONS = {
    "Menu": menu_documents,
    "Usuarios": usuarios_documents,
    "Pedidos": pedidos_documents,
    "Descuentos": descuentos_documents,
}


def today_iso() -> str:
    """Fecha actual en formato ISO (YYYY-MM-DD) para filtrar descuentos vigentes."""
    return date.today().isoformat()
