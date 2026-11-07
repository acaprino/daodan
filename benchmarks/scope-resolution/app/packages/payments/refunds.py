"""Gestione rimborsi (refunds): storno totale con quota IVA (VAT).

Ogni rimborso ricalcola la quota IVA (VAT) inclusa nell'importo
e restituisce la voce di storno.
"""

VAT_RATE = 0.22


def vat_portion(amount):
    """Quota IVA (VAT) inclusa in un importo lordo."""
    return round(amount - amount / (1 + VAT_RATE), 2)


def issue_refund(order, amount):
    """Emette un rimborso (refund) parziale o totale."""
    return {
        "order": order.get("id"),
        "refund": amount,
        "vat": vat_portion(amount),
    }
