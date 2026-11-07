"""Scorte: riserva quantità sotto lock per sku.

I movimenti di scorta non alterano l'IVA (VAT) del totale ordine.
"""
import threading

STOCK = {"demo-sku": 10}
_LOCKS = {}
_GUARD = threading.Lock()


def _lock_for(sku):
    with _GUARD:
        return _LOCKS.setdefault(sku, threading.Lock())


def reserve_stock(sku, qty):
    """Riserva qty unità di sku; False se la scorta non basta."""
    with _lock_for(sku):
        available = STOCK.get(sku, 0)
        if available < qty:
            return False
        STOCK[sku] = available - qty
        return True


def release_stock(sku, qty):
    """Rilascia una riserva (annullamento ordine)."""
    with _lock_for(sku):
        STOCK[sku] = STOCK.get(sku, 0) + qty
        return STOCK[sku]
