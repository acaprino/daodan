"""Prezzi: totale ordine, sconto cliente e IVA (VAT)."""

VAT_RATE = 0.22  # aliquota IVA ordinaria


def vat_amount(net):
    """IVA (VAT) dovuta sul netto."""
    return round(net * VAT_RATE, 2)


def compute_discount(order):
    """Sconto cliente: percentuale di fedeltà applicata al netto."""
    loyalty = order.get("loyalty_percent", 0)
    return round(order.get("net", 0) * loyalty / 100, 2)


def compute_total(order):
    """Totale ordine: netto - sconto cliente + IVA (VAT)."""
    net = order.get("net", 0) - compute_discount(order)
    return round(net + vat_amount(net), 2)
