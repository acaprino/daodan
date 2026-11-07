"""Tariffe di spedizione e sconto volume.

L'IVA (VAT) sulla spedizione segue l'aliquota del bene trasportato.
"""

ZONES = {"local": 5.0, "national": 9.0, "eu": 15.0}


def shipping_rate(zone, weight):
    """Tariffa base per zona con sovrappeso oltre 5 kg."""
    base = ZONES.get(zone, 15.0)
    return round(base + 0.5 * max(weight - 5, 0), 2)


def volume_discount(monthly_shipments):
    """Sconto per volume di spedizioni mensili."""
    if monthly_shipments >= 100:
        return 0.10
    if monthly_shipments >= 30:
        return 0.05
    return 0.0


def quote(zone, weight, monthly_shipments):
    """Preventivo spedizione: tariffa meno sconto volume, IVA (VAT) a parte."""
    rate = shipping_rate(zone, weight)
    return round(rate * (1 - volume_discount(monthly_shipments)), 2)
