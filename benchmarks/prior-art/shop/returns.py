"""Resi: rimborso di righe già pagate e annullamento di un ordine aperto."""
from decimal import ROUND_HALF_UP, Decimal

from . import catalog, orders


def _clean_sku(raw):
    return raw.strip().upper()


def _total(lines):
    amount = sum((Decimal(str(line["price"])) * line["qty"] for line in lines), Decimal(0))
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _customer_id(customer):
    if isinstance(customer, dict):
        return customer.get("id") or customer.get("customer_id")
    if hasattr(customer, "id"):
        return customer.id
    return customer


def refund(order_id, skus):
    """Importo da rimborsare per le righe indicate."""
    order = orders.ORDERS[order_id]
    wanted = {_clean_sku(sku) for sku in skus}
    lines = [line for line in order["lines"] if line["sku"] in wanted]
    return {"customer": _customer_id(order["customer"]), "amount": _total(lines)}


def void(order_id):
    """Annulla un ordine non ancora spedito."""
    order = orders.ORDERS[order_id]
    if order["status"] != "placed":
        raise ValueError("solo un ordine aperto si annulla")
    for line in order["lines"]:
        catalog.PRODUCTS[line["sku"]]["stock"] += line["qty"]
    order["status"] = "cancelled"
