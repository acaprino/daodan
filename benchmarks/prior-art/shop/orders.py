"""Ordini: creazione e annullamento."""
from . import catalog, pricing

MAX_QTY = 20
ORDERS = {}


def place(order_id, customer_id, lines):
    stored = []
    for line in lines:
        if not 1 <= line["qty"] <= MAX_QTY:
            raise ValueError(f"quantità non ammessa: {line['qty']}")
        sku = catalog.normalize_sku(line["sku"])
        product = catalog.PRODUCTS[sku]
        if product["stock"] < line["qty"]:
            raise ValueError(f"scorta insufficiente: {sku}")
        stored.append({"sku": sku, "qty": line["qty"], "price": product["price"]})
    for line in stored:
        catalog.PRODUCTS[line["sku"]]["stock"] -= line["qty"]
    subtotal = pricing.lines_total(stored)
    order = {
        "customer": {"id": customer_id},
        "lines": stored,
        "status": "placed",
        "total": pricing.round_cents(subtotal + pricing.shipping_for(subtotal)),
    }
    ORDERS[order_id] = order
    return order


def cancel(order_id):
    """Annulla un ordine aperto e rimette a scorta ogni riga."""
    order = ORDERS[order_id]
    if order["status"] != "placed":
        raise ValueError("solo un ordine aperto si annulla")
    for line in order["lines"]:
        catalog.PRODUCTS[line["sku"]]["stock"] += line["qty"]
    order["status"] = "cancelled"
