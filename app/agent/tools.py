"""Herramientas e-commerce que el agente LangGraph puede invocar."""

from typing import Dict, List
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from app.data.products import search_products, get_product_by_id, PRODUCTS
from app.data.knowledge_base import search_knowledge_base

# Almacén de carritos en memoria, keyed por thread_id/sesión
_CART_STORAGE: Dict[str, List[dict]] = {}

# Almacén de pedidos en memoria, keyed por order_id
_ORDER_STORAGE: Dict[str, dict] = {}
_ORDER_COUNTER = 1000


def _get_cart(thread_id: str) -> List[dict]:
    """Returns the cart for the given session, creating it if needed."""
    return _CART_STORAGE.setdefault(thread_id, [])


def _format_product_line(product: dict, quantity: int) -> str:
    """Formats a product line for display."""
    subtotal = product["price"] * quantity
    return f"  {product['id']}. {product['name']} - ${product['price']:.2f} x {quantity} = ${subtotal:.2f}"


def _cart_total(cart: List[dict]) -> float:
    """Computes the total price of the cart."""
    total = 0.0
    for item in cart:
        product = get_product_by_id(item["product_id"])
        if product:
            total += product["price"] * item["quantity"]
    return total


@tool
def search_catalog(query: str) -> str:
    """Busca productos en el catálogo por nombre, descripción o categoría.
    Ejemplos: 'audífonos', 'camisetas', 'electrónica', 'libros', 'cafetera'."""
    q = query.strip()
    if not q:
        return "Por favor especifica qué productos estás buscando."
    results = search_products(query=q)
    if not results:
        return f"No se encontraron productos para '{query}'. Prueba con otras palabras: electrónica, ropa, hogar, deportes, libros."
    lines = [f"Se encontraron {len(results)} producto(s) para '{query}':"]
    for p in results[:10]:
        lines.append(f"  [{p['id']}] {p['name']} - ${p['price']:.2f} ({p['category']})")
    if len(results) > 10:
        lines.append(f"  ... y {len(results) - 10} más. Pide más detalles de un producto por su ID.")
    lines.append("\nPara ver el detalle de un producto dime su ID, ejemplo: 'detalle del producto 3'.")
    return "\n".join(lines)


@tool
def filter_products(
    category: str = "",
    min_price: float = 0.0,
    max_price: float = 0.0
) -> str:
    """Filtra el catálogo por categoría y rango de precio.
    Categorías: Electronics, Clothing, Home & Kitchen, Sports, Books."""
    if not category and min_price == 0 and max_price == 0:
        return f"Hay {len(PRODUCTS)} productos en el catálogo. Dime una categoría (Electrónica, Ropa, Hogar, Deportes, Libros) o un rango de precio."
    results = search_products(
        category=category or None,
        min_price=min_price if min_price > 0 else None,
        max_price=max_price if max_price > 0 else None,
    )
    if not results:
        return "No hay productos que coincidan con esos filtros."
    lines = [f"Productos encontrados: {len(results)}"]
    for p in results[:10]:
        lines.append(f"  [{p['id']}] {p['name']} - ${p['price']:.2f} ({p['category']})")
    return "\n".join(lines)


@tool
def get_product_details(product_id: int) -> str:
    """Muestra la información completa de un producto por su ID numérico."""
    product = get_product_by_id(product_id)
    if not product:
        available = ", ".join(str(p["id"]) for p in PRODUCTS[:10])
        return f"Producto {product_id} no encontrado. IDs disponibles: {available}, ..."
    return (
        f"📦 {product['name']}\n"
        f"  ID: {product['id']}\n"
        f"  Categoría: {product['category']}\n"
        f"  Precio: ${product['price']:.2f}\n"
        f"  Stock disponible: {product['stock']} unidades\n"
        f"  Descripción: {product['description']}"
    )


@tool
def add_to_cart(product_id: int, quantity: int, config: RunnableConfig) -> str:
    """Añade un producto al carrito de compras del usuario.
    Args: product_id (ID numérico del producto), quantity (cantidad deseada)."""
    product = get_product_by_id(product_id)
    if not product:
        return f"Producto {product_id} no encontrado. Verifica el ID con el buscador de catálogo."

    if quantity < 1:
        return "La cantidad debe ser al menos 1."

    if product["stock"] < quantity:
        return f"Stock insuficiente: solo quedan {product['stock']} unidades de '{product['name']}'."

    thread_id = config.get("configurable", {}).get("thread_id", "default")
    cart = _get_cart(thread_id)

    for item in cart:
        if item["product_id"] == product_id:
            if product["stock"] < item["quantity"] + quantity:
                return f"Stock insuficiente para añadir {quantity} más. Ya tienes {item['quantity']} en el carrito."
            item["quantity"] += quantity
            return f"🛒 '{product['name']}' añadido al carrito (cantidad total: {item['quantity']}). Precio unitario: ${product['price']:.2f}."

    cart.append({"product_id": product_id, "quantity": quantity})
    return f"🛒 '{product['name']}' añadido al carrito (cantidad: {quantity}). Precio unitario: ${product['price']:.2f}."


@tool
def view_cart(config: RunnableConfig) -> str:
    """Muestra el contenido actual del carrito de compras y el total a pagar."""
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    cart = _get_cart(thread_id)
    if not cart:
        return "Tu carrito está vacío. Busca productos y pídeme añadirlos, por ejemplo: 'añade el producto 6 al carrito'."
    lines = ["🛒 Tu carrito:"]
    for item in cart:
        product = get_product_by_id(item["product_id"])
        if product:
            lines.append(_format_product_line(product, item["quantity"]))
    total = _cart_total(cart)
    lines.append(f"\nTotal: ${total:.2f}")
    lines.append("¿Deseas eliminar algún artículo o proceder al pago?")
    return "\n".join(lines)


@tool
def remove_from_cart(product_id: int, config: RunnableConfig) -> str:
    """Elimina un producto del carrito por su ID numérico."""
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    cart = _get_cart(thread_id)
    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            product = get_product_by_id(product_id)
            name = product["name"] if product else f"Producto {product_id}"
            return f"'{name}' eliminado del carrito."
    return f"El producto {product_id} no está en tu carrito."


@tool
def place_order(config: RunnableConfig) -> str:
    """Realiza el pedido con los productos actuales del carrito y simula la creación de la orden."""
    global _ORDER_COUNTER
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    cart = _get_cart(thread_id)
    if not cart:
        return "No puedes hacer un pedido con el carrito vacío. Primero añade productos."

    for item in cart:
        product = get_product_by_id(item["product_id"])
        if product and product["stock"] < item["quantity"]:
            return f"Stock insuficiente para '{product['name']}'. Solo quedan {product['stock']} unidades."

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
        f"  Total: ${total:.2f}\n"
        f"  Estado: {_ORDER_STORAGE[order_id]['status']}\n"
        f"  Recibirás el número de guía por email dentro de 24 horas.\n"
        f"  Tu carrito ahora está vacío."
    )


@tool
def get_order_status(order_id: str) -> str:
    """Consulta el estado de un pedido existente por su número de orden (ej. ORD-1001)."""
    order = _ORDER_STORAGE.get(order_id.strip().upper())
    if not order:
        return f"No se encontró el pedido '{order_id}'. Verifica el número e inténtalo de nuevo."
    lines = [
        f"📦 Pedido {order['order_id']}",
        f"  Estado: {order['status']}",
        f"  Total: ${order['total']:.2f}",
        "  Artículos:",
    ]
    for item in order["items"]:
        product = get_product_by_id(item["product_id"])
        if product:
            lines.append(f"    {product['name']} x {item['quantity']}")
    return "\n".join(lines)


@tool
def search_knowledge(query: str) -> str:
    """Busca en la base de conocimientos de la tienda: envíos, devoluciones, pagos,
    estado de pedidos, soporte, promociones y políticas para responder preguntas del cliente."""
    return search_knowledge_base(query)


# Lista completa de herramientas e-commerce exportadas
tools = [
    search_catalog,
    filter_products,
    get_product_details,
    add_to_cart,
    view_cart,
    remove_from_cart,
    place_order,
    get_order_status,
    search_knowledge,
]