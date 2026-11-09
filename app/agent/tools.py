"""Herramientas del restaurante Popy que el agente LangGraph puede invocar."""

from typing import Dict, List
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

# Importamos la función RAG multi-colección de Chroma Cloud
from app.rag.retriever import ask_popy_bot

# Almacén de carritos en memoria, keyed por thread_id/sesión
_CART_STORAGE: Dict[str, List[dict]] = {}

# Almacén de pedidos en memoria, keyed por order_id
_ORDER_STORAGE: Dict[str, dict] = {}
_ORDER_COUNTER = 1000

# Mapeo txn_id de Wompi → order_id (pagos Nequi en curso)
_PAYMENT_TXN_TO_ORDER: Dict[str, str] = {}


def get_order(order_id: str) -> dict | None:
    """Returns the order dict for the given id, or None."""
    return _ORDER_STORAGE.get(order_id)


def mark_order_paid(order_id: str) -> bool:
    """Marks an order as paid. Returns True if the order existed and was updated."""
    order = _ORDER_STORAGE.get(order_id)
    if not order:
        return False
    order["status"] = "Pagado"
    return True


def register_payment_txn(txn_id: str, order_id: str) -> None:
    """Maps a Wompi transaction id to an order id."""
    _PAYMENT_TXN_TO_ORDER[txn_id] = order_id


def order_for_txn(txn_id: str) -> str | None:
    """Returns the order id associated with a Wompi transaction id."""
    return _PAYMENT_TXN_TO_ORDER.get(txn_id)


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
    """Busca en la base de datos vectorial de Popy: menú (comida, bebidas, precios), usuarios (CC, nombres, edad, género), pedidos (detalle, cantidades, total, estado) y descuentos vigentes.
    Ejemplos: 'bandeja paisa', 'precio del ajiaco', 'plato 3', 'pedido ORD-2001', 'descuento de estudiantes', 'usuario Carlos'."""
    q = query.strip()
    if not q:
        return "Por favor especifica qué deseas buscar en la base de datos."

    # Consulta semántica directa a Chroma Cloud
    return ask_popy_bot(q)


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

    order = _ORDER_STORAGE[order_id]
    items_html = "".join(
        f"<li>{item['name']} × {item['quantity']} — "
        f"${item['price'] * item['quantity']:.2f}</li>"
        for item in order["items"]
    )
    total = order["total"]

    # html: → el frontend lo renderiza con dangerouslySetInnerHTML (Message.jsx)
    return (
        "html:"
        f"<div style='font-family:system-ui,sans-serif'>"
        f"<p style='margin:0 0 4px'>✅ <strong>¡Pedido {order_id} confirmado!</strong></p>"
        f"<p style='margin:0 0 6px;color:#6b7280'>Estado: {order['status']}</p>"
        f"<ul style='margin:0 0 8px;padding-left:18px'>{items_html}</ul>"
        f"<p style='margin:0 0 12px;font-size:1.05em'>"
        f"<strong>Total: ${total:.2f}</strong></p>"
        f"<p style='margin:0 0 8px'>Paga con Nequi (sandbox oficial de Wompi):</p>"
        f"<form method='post' action='/pay/nequi' "
        f"style='display:flex;flex-direction:column;gap:8px;max-width:280px'>"
        f"<input type='hidden' name='order_id' value='{order_id}' />"
        f"<label style='font-size:0.85em;color:#374151'>Celular Nequi"
        f"<input type='tel' name='phone_number' value='3991111111' "
        f"pattern='3[0-9]{9}' required maxlength='10' "
        f"placeholder='3XXXXXXXXX' "
        f"style='margin-top:4px;width:100%;padding:8px;border:1px solid #d1d5d5;"
        f"border-radius:8px;font-size:1em' /></label>"
        f"<button type='submit' "
        f"style='background:#C2185B;color:#fff;border:0;border-radius:8px;"
        f"padding:10px 14px;font-size:1em;font-weight:600;cursor:pointer'>"
        f"Pagar con Nequi</button>"
        f"</form>"
        f"<p style='margin:12px 0 4px'>O paga con tarjeta:</p>"
        f"<a href='/pay/card/{order_id}' "
        f"style='display:inline-block;background:#1f2937;color:#fff;"
        f"border-radius:8px;padding:10px 14px;font-size:1em;font-weight:600;"
        f"text-decoration:none'>Pagar con tarjeta</a>"
        f"<p style='margin:12px 0 0;font-size:0.78em;color:#6b7280'>"
        f"Sandbox tarjeta: <code>4242424242424242</code> (respaldo Wompi: "
        f"<code>4111111111111111</code> / <code>5204730000001003</code>), "
        f"cvv ≠ 111, fecha futura. Nequi <code>3991111111</code> aprueba solo."
        f"</p>"
        f"</div>"
    )


@tool
def get_order_status(order_id: str) -> str:
    """Consulta el estado de un pedido por su número de orden (ej. ORD-2001).
    Busca primero en los pedidos de la sesión actual y luego en la base de datos de Chroma."""
    oid = order_id.strip().upper()
    order = _ORDER_STORAGE.get(oid)
    if order:
        lines = [
            f"📦 Pedido {order['order_id']}",
            f"   Estado: {order['status']}",
            f"   Total: ${order['total']:.2f}",
            "   Artículos:",
        ]
        for item in order["items"]:
            lines.append(f"    - {item['name']} x {item['quantity']}")
        return "\n".join(lines)

    # Fallback: buscar en la colección Pedidos de Chroma Cloud
    return ask_popy_bot(f"pedido {oid}: detalle, cantidades, precio total y estado")


# Lista completa de herramientas exportadas para LangGraph
tools = [
    search_catalog,
    add_to_cart,
    view_cart,
    remove_from_cart,
    place_order,
    get_order_status,
]