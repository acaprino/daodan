"""Gateway pagamenti: registro dei metodi e addebito online.

Ogni metodo di pagamento è una funzione registrata in REGISTRY.
Gli importi ricevuti includono già l'IVA (VAT).
"""


def pay_online(order):
    """Addebito online: l'importo include già l'IVA (VAT)."""
    return {"method": "card", "amount": order.get("total", 0)}


def pay_on_delivery(order):
    """Pagamento alla consegna."""
    return {"method": "cod", "amount": order.get("total", 0)}


REGISTRY = {
    "pay_on_delivery": pay_on_delivery,
    "pay_online": pay_online,
}


def charge(order):
    """Alias per hop: handler risolto dal registro, poi invocato."""
    handler = REGISTRY["pay_online"]
    return handler(order)
