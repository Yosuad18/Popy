"""Herramientas e-commerce que el agente LangGraph puede invocar."""

from typing import Dict, List
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

# Importamos la función RAG de Chroma Cloud en lugar de los archivos estáticos
from app.rag.retriever import ask_ecommerce_bot

# Almacén de carritos en memoria, keyed por thread_id/sesión
_CART_STORAGE: Dict[str, List[dict]] = {}

# Almacén de pedidos en memoria, keyed por order_id
_ORDER_STORAGE: Dict[str, dict] = {}
_ORDER_COUNTER = 1000


def _get_cart(thread_id: str) -> List[dict]:
    """Returns the cart for the given session, creating it if needed."""
    return _CART_STORAGE.setdefault(thread_id, [])


def _format_product_line(item: dict) -> str:
    """Formats a product line for display."""
    subtotal = item["price"] * item["quantity"]
    return f"   - {item['name']} - ${item['price']:.2f} x {item['quantity']} = ${subtotal:.2f}"


def _cart_total(cart: List[dict]) -> float:
    """Computes the total price of the cart."""
    return sum(item["price"] * item["quantity"] for item in cart)


@tool
def search_catalog(query: str) -> str:
    """Busca productos, usuarios, repartidores y métodos de pago en la base de datos vectorial de Chroma Cloud.
    Ejemplos de búsqueda: 'laptop', 'smartphone', 'teclado', 'repartidor', 'usuario'."""
    q = query.strip()
    if not q:
        return "Por favor especifica qué deseas buscar en la base de datos."
    
    # Consulta semántica directa a Chroma Cloud
    return ask_ecommerce_bot(q)


@tool
def add_to_cart(product_name: str, price: float, quantity: int, config: RunnableConfig) -> str:
    """Añade un producto al carrito de compras del usuario.
    Args:
        product_name: Nombre del producto.
        price: Precio unitario del producto.
        quantity: Cantidad de unidades a añadir.
    """
    if quantity < 1:
        return "La cantidad debe ser al menos 1."

    thread_id = config.get("configurable", {}).get("thread_id", "default")
    cart = _get_cart(thread_id)

    for item in cart:
        if item["name"].lower() == product_name.lower():
            item["quantity"] += quantity
            return f"🛒 '{product_name}' actualizado en el carrito (cantidad total: {item['quantity']})."

    cart.append({
        "name": product_name,
        "price": price,
        "quantity": quantity
    })
    return f"🛒 '{product_name}' añadido al carrito (cantidad: {quantity}). Precio unitario: ${price:.2f}."


@tool
def view_cart(config: RunnableConfig) -> str:
    """Muestra el contenido actual del carrito de compras y el total a pagar."""
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    cart = _get_cart(thread_id)
    if not cart:
        return "Tu carrito está vacío. Busca productos y pídeme añadirlos al carrito."
    
    lines = ["🛒 Tu carrito:"]
    for item in cart:
        lines.append(_format_product_line(item))
    
    total = _cart_total(cart)
    lines.append(f"\nTotal: ${total:.2f}")
    lines.append("¿Deseas eliminar algún artículo o proceder a realizar el pedido?")
    return "\n".join(lines)


@tool
def remove_from_cart(product_name: str, config: RunnableConfig) -> str:
    """Elimina un producto del carrito indicando su nombre."""
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    cart = _get_cart(thread_id)
    for item in cart:
        if item["name"].lower() == product_name.lower():
            cart.remove(item)
            return f"'{product_name}' fue eliminado del carrito."
    return f"El producto '{product_name}' no está en tu carrito."


@tool
def place_order(config: RunnableConfig) -> str:
    """Realiza el pedido con los productos actuales del carrito y genera la confirmación."""
    global _ORDER_COUNTER
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    cart = _get_cart(thread_id)
    if not cart:
        return "No puedes hacer un pedido con el carrito vacío. Primero añade productos."

    total = _cart_total(cart)
    _ORDER_COUNTER += 1
    order_id = f"ORD-{_ORDER_COUNTER}"
    
    _ORDER_STORAGE[order_id] = {
        "order_id": order_id,
        "items": [dict(item) for item in cart],
        "total": round(total, 2),
        "status": "Procesando",
    }
    _CART_STORAGE[thread_id] = []
    
    return (
        f"✅ ¡Pedido {order_id} confirmado!\n"
        f"   Total: ${total:.2f}\n"
        f"   Estado: {_ORDER_STORAGE[order_id]['status']}\n"
        f"   Recibirás la confirmación de envío pronto.\n"
        f"   Tu carrito ahora está vacío."
    )


@tool
def get_order_status(order_id: str) -> str:
    """Consulta el estado de un pedido existente por su número de orden (ej. ORD-1001)."""
    order = _ORDER_STORAGE.get(order_id.strip().upper())
    if not order:
        return f"No se encontró el pedido '{order_id}'. Verifica el número e inténtalo de nuevo."
    
    lines = [
        f"📦 Pedido {order['order_id']}",
        f"   Estado: {order['status']}",
        f"   Total: ${order['total']:.2f}",
        "   Artículos:",
    ]
    for item in order["items"]:
        lines.append(f"    - {item['name']} x {item['quantity']}")
    return "\n".join(lines)


# Lista completa de herramientas exportadas para LangGraph
tools = [
    search_catalog,
    add_to_cart,
    view_cart,
    remove_from_cart,
    place_order,
    get_order_status,
]