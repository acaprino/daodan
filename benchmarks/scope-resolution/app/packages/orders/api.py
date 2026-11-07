"""Entry point degli eventi ordine: registrazione callback e dispatch.

Il dispatcher solleva KeyError col nome dell'evento quando manca la
registrazione. Le callback ricevono il payload così com'è.
Il totale ordine include l'IVA (VAT)
calcolata dal modulo pricing.
"""
from .service import OrderService

EVENT_REGISTRY = {}


def on_event(name, handler):
    """Registra una callback per il nome evento e la restituisce."""
    EVENT_REGISTRY[name] = handler
    return handler


class Dispatcher:
    """Instrada gli eventi alle callback registrate."""

    def __init__(self, service):
        self._service = service

    def _invoke(self, name, payload):
        handler = EVENT_REGISTRY[name]
        return handler(payload)

    def handle(self, name, payload):
        """Punto di ingresso pubblico del dispatch."""
        return self._invoke(name, payload)


def register_defaults():
    """Registra checkout e refund_request e restituisce il dispatcher."""
    service = OrderService()
    on_event("checkout", service.checkout)
    on_event("refund_request", service.refund_request)
    return Dispatcher(service)
