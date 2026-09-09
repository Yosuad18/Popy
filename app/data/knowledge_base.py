"""Knowledge base with store policies, FAQs, and support topics for the e-commerce chatbot."""

from typing import List, Dict


KNOWLEDGE_BASE: List[Dict] = [
    {
        "topic": "shipping",
        "keywords": ["envio", "envios", "shipping", "entrega", "delivery", "urgente", "demora", "cuanto tarda", "llega", "costo de envio"],
        "content": (
            "Shipping & Delivery:\n"
            "- Orders are processed within 24 hours.\n"
            "- Standard shipping: 3-5 business days ($4.99).\n"
            "- Express shipping: 1-2 business days ($9.99).\n"
            "- Free standard shipping on orders over $50.\n"
            "- You will receive a tracking number by email once your order ships."
        ),
    },
    {
        "topic": "returns",
        "keywords": ["devolucion", "devoluciones", "return", "returns", "reembolso", "refund", "cambio", "garantia", "cambiar"],
        "content": (
            "Returns & Refunds:\n"
            "- 30-day return policy on all unused items with original packaging.\n"
            "- Refunds are processed within 5-7 business days of receiving the return.\n"
            "- Defective or damaged items are refunded in full.\n"
            "- To start a return, contact support with your order number.\n"
            "- Return shipping is free for defective items."
        ),
    },
    {
        "topic": "payments",
        "keywords": ["pago", "pagos", "payment", "pay", "tarjeta", "card", "paypal", "credito", "debito", "contra entrega", "transferencia"],
        "content": (
            "Payment Methods:\n"
            "- We accept Visa, Mastercard, and American Express.\n"
            "- PayPal is supported at checkout.\n"
            "- Apple Pay and Google Pay are available.\n"
            "- Bank transfer is available for orders over $100.\n"
            "- Cash on delivery is available in select areas."
        ),
    },
    {
        "topic": "orders",
        "keywords": ["orden", "ordenes", "order", "orders", "pedido", "pedidos", "estado de pedido", "seguimiento", "tracking", "cancelar"],
        "content": (
            "Orders & Tracking:\n"
            "- Check your order status anytime by asking about your order number.\n"
            "- Orders can be canceled within 2 hours of placement.\n"
            "- Tracking updates are sent via email and SMS.\n"
            "- If your order hasn't arrived in 10 business days, contact support."
        ),
    },
    {
        "topic": "account",
        "keywords": ["cuenta", "account", "registro", "register", "crear cuenta", "iniciar sesion", "login", "pass" "contraseña"],
        "content": (
            "Account Help:\n"
            "- Create an account to track orders, save addresses, and earn rewards.\n"
            "- Use 'Forgot password' on the login page to reset your password.\n"
            "- You can checkout as a guest without an account.\n"
            "- Account data can be deleted at any time by contacting support."
        ),
    },
    {
        "topic": "contact",
        "keywords": ["contacto", "contact", "soporte", "support", "ayuda", "help", "ayudame", "telefono", "email", "whatsapp"],
        "content": (
            "Contact & Support:\n"
            "- Email: support@tiendaonline.com\n"
            "- WhatsApp: +1 (555) 123-4567\n"
            "- Live chat available Monday to Friday, 9am-6pm.\n"
            "- Average response time: under 2 hours on business days.\n"
            "- Visit our help center for self-service articles."
        ),
    },
    {
        "topic": "products",
        "keywords": ["producto", "productos", "products", "catalogo", "catalog", "inventario", "stock", "disponibilidad", "precio"],
        "content": (
            "Product Information:\n"
            "- Browse categories: Electronics, Clothing, Home & Kitchen, Sports, and Books.\n"
            "- Ask me to search products by name, category, or price range.\n"
            "- Prices include no hidden fees; taxes are calculated at checkout.\n"
            "- If a product shows out of stock, new stock typically arrives within 1-2 weeks.\n"
            "- All products include a standard 12-month warranty."
        ),
    },
    {
        "topic": "promotions",
        "keywords": ["promocion", "promociones", "descuento", "discount", "cupon", "coupon", "oferta", "offer", "sale", "rebaja", "codigo"],
        "content": (
            "Promotions & Discounts:\n"
            "- New customers get 10% off with code: BIENVENIDO10.\n"
            "- Free shipping on orders over $50.\n"
            "- Weekly deals are announced every Monday in the newsletter.\n"
            "- Refer a friend and both get $5 credit.\n"
            "- Discount codes cannot be combined."
        ),
    },
]


def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for the most relevant entries matching the query."""
    q = query.lower()
    results = []

    for entry in KNOWLEDGE_BASE:
        keywords = entry["keywords"]
        if any(kw in q for kw in keywords):
            results.append(f"[{entry['topic'].upper()}]\n{entry['content']}")

    if results:
        return "\n\n---\n\n".join(results)

    return (
        "No encontré información específica sobre eso. "
        "Puedo ayudarte con: envíos/delivery, devoluciones/refunds, pagos, "
        "estado de pedidos, soporte al cliente, productos, y promociones."
    )