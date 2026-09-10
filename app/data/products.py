"""Mock product catalog for the e-commerce chatbot."""

from typing import List, Dict, Optional

from app.data.vector_store import search as vector_search

PRODUCTS: List[Dict] = [
    {
        "id": 1,
        "name": "Wireless Bluetooth Headphones",
        "description": "Noise-cancelling over-ear headphones with 30-hour battery life and premium sound quality.",
        "category": "Electronics",
        "price": 79.99,
        "stock": 45,
    },
    {
        "id": 2,
        "name": "Smartphone Stand with Charger",
        "description": "Adjustable desk stand with built-in 15W wireless fast charger, compatible with all Qi devices.",
        "category": "Electronics",
        "price": 34.99,
        "stock": 120,
    },
    {
        "id": 3,
        "name": "Portable Bluetooth Speaker",
        "description": "Waterproof mini speaker with 360-degree sound, 12-hour playtime, and built-in microphone.",
        "category": "Electronics",
        "price": 49.99,
        "stock": 80,
    },
    {
        "id": 4,
        "name": "USB-C Hub Adapter 7-in-1",
        "description": "Multi-port adapter with HDMI, USB 3.0, SD card reader, and 100W PD charging for laptops.",
        "category": "Electronics",
        "price": 29.99,
        "stock": 200,
    },
    {
        "id": 5,
        "name": "Mechanical Gaming Keyboard",
        "description": "RGB backlit keyboard with Cherry MX Blue switches, programmable keys, and aluminum frame.",
        "category": "Electronics",
        "price": 89.99,
        "stock": 35,
    },
    {
        "id": 6,
        "name": "Classic Cotton T-Shirt",
        "description": "100% organic cotton crew neck t-shirt, available in multiple colors. Comfortable everyday wear.",
        "category": "Clothing",
        "price": 19.99,
        "stock": 300,
    },
    {
        "id": 7,
        "name": "Slim Fit Denim Jeans",
        "description": "Stretch denim jeans with slim fit cut, classic 5-pocket design, and premium wash finish.",
        "category": "Clothing",
        "price": 49.99,
        "stock": 150,
    },
    {
        "id": 8,
        "name": "Waterproof Running Jacket",
        "description": "Lightweight breathable rain jacket with sealed seams, reflective details, and packable design.",
        "category": "Clothing",
        "price": 64.99,
        "stock": 60,
    },
    {
        "id": 9,
        "name": "Leather Crossbody Bag",
        "description": "Genuine leather mini crossbody bag with adjustable strap and multiple compartments.",
        "category": "Clothing",
        "price": 44.99,
        "stock": 75,
    },
    {
        "id": 10,
        "name": "Casual Canvas Sneakers",
        "description": "Low-top canvas sneakers with rubber sole, cushioned insole, and timeless design.",
        "category": "Clothing",
        "price": 39.99,
        "stock": 180,
    },
    {
        "id": 11,
        "name": "Stainless Steel Water Bottle",
        "description": "Double-wall insulated 750ml bottle, keeps drinks cold 24h or hot 12h. BPA-free.",
        "category": "Home & Kitchen",
        "price": 24.99,
        "stock": 250,
    },
    {
        "id": 12,
        "name": "Electric Coffee Grinder",
        "description": "Compact burr grinder with 20 grind settings, stainless steel blades, and 12-cup capacity.",
        "category": "Home & Kitchen",
        "price": 39.99,
        "stock": 90,
    },
    {
        "id": 13,
        "name": "Non-Stick Cookware Set (5 pcs)",
        "description": "Ceramic non-stick frying pan, saucepan, and stockpot set with heat-resistant handles.",
        "category": "Home & Kitchen",
        "price": 89.99,
        "stock": 40,
    },
    {
        "id": 14,
        "name": "LED Desk Lamp with USB Port",
        "description": "Adjustable LED lamp with 5 brightness levels, 3 color modes, and built-in USB charging port.",
        "category": "Home & Kitchen",
        "price": 27.99,
        "stock": 110,
    },
    {
        "id": 15,
        "name": "Memory Foam Pillow (2-pack)",
        "description": "Ergonomic cervical pillows with cooling gel layer, hypoallergenic, and washable cover.",
        "category": "Home & Kitchen",
        "price": 34.99,
        "stock": 70,
    },
    {
        "id": 16,
        "name": "Yoga Mat Non-Slip",
        "description": "6mm thick TPE eco-friendly yoga mat with alignment lines and carrying strap included.",
        "category": "Sports",
        "price": 29.99,
        "stock": 130,
    },
    {
        "id": 17,
        "name": "Adjustable Dumbbell Set",
        "description": "Space-saving adjustable dumbbells from 5 to 25 lbs each, with quick-lock mechanism.",
        "category": "Sports",
        "price": 119.99,
        "stock": 25,
    },
    {
        "id": 18,
        "name": "Insulated Sports Water Bottle",
        "description": "32oz Tritan bottle with one-hand flip lid, time markers, and fruit infuser basket.",
        "category": "Sports",
        "price": 14.99,
        "stock": 200,
    },
    {
        "id": 19,
        "name": "Resistance Bands Set (5 pcs)",
        "description": "5-level loop resistance bands from light to heavy, with door anchor and carrying bag.",
        "category": "Sports",
        "price": 16.99,
        "stock": 175,
    },
    {
        "id": 20,
        "name": "Camping Hammock with Net",
        "description": "Lightweight parachute nylon hammock with mosquito net, tree straps, and carabiners.",
        "category": "Sports",
        "price": 34.99,
        "stock": 55,
    },
    {
        "id": 21,
        "name": "Python Programming for Beginners",
        "description": "Comprehensive guide to Python basics, data structures, OOP, and real-world projects.",
        "category": "Books",
        "price": 22.99,
        "stock": 100,
    },
    {
        "id": 22,
        "name": "The Art of Negotiation",
        "description": "Best-selling book on negotiation strategies for business and everyday life situations.",
        "category": "Books",
        "price": 16.99,
        "stock": 85,
    },
    {
        "id": 23,
        "name": "Cooking Around the World",
        "description": "200+ recipes from 30 countries with step-by-step instructions and stunning photography.",
        "category": "Books",
        "price": 29.99,
        "stock": 60,
    },
    {
        "id": 24,
        "name": "Mindfulness and Meditation Guide",
        "description": "Practical guide to daily mindfulness practices, stress reduction, and mental wellness.",
        "category": "Books",
        "price": 14.99,
        "stock": 95,
    },
]


def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[Dict]:
    """Search products using ChromaDB Cloud vector search, with optional filters."""
    if query:
        results = vector_search(query, n=20)
        products = []
        seen_ids = set()
        for r in results:
            meta = r["metadata"]
            pid = meta.get("product_id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                product = next((p for p in PRODUCTS if p["id"] == pid), None)
                if product:
                    products.append(product)
        results_list = products
    else:
        results_list = PRODUCTS

    if category:
        c = category.lower()
        results_list = [p for p in results_list if c in p["category"].lower()]

    if min_price is not None:
        results_list = [p for p in results_list if p["price"] >= min_price]

    if max_price is not None:
        results_list = [p for p in results_list if p["price"] <= max_price]

    return results_list


def get_product_by_id(product_id: int) -> Optional[Dict]:
    """Return a single product by its ID, or None if not found."""
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None
