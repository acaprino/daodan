"""Prezzi: gli importi si arrotondano una volta sola, alla fine."""
from decimal import ROUND_HALF_UP, Decimal

FREE_SHIPPING_MIN = 50.00
SHIPPING = 6.90


def round_cents(amount):
    """Arrotonda al centesimo, metà verso l'alto: è la regola dei soldi."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def lines_total(lines):
    """Totale delle righe: quantità per prezzo."""
    return round_cents(sum(Decimal(str(line["price"])) * line["qty"] for line in lines))


def shipping_for(subtotal):
    return 0.0 if subtotal >= FREE_SHIPPING_MIN else SHIPPING
