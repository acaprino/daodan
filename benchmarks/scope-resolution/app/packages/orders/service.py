"""Servizio ordini: orchestrazione checkout e richieste di rimborso.

Ogni totale include l'IVA (VAT). La pipeline di validazione è
configurabile: il costruttore accetta una classe alternativa.
Il default esegue una sola fase.
"""
from . import inventory, ledger, notifications, pricing


class DefaultPipeline:
    """Pipeline di validazione di default (una sola fase)."""

    def step(self, order):
        order["validated"] = True
        return order


class OrderService:
    def __init__(self, pipeline_cls=None):
        # pipeline_cls permette di sostituire la validazione
        setattr(self, "_pipeline", (pipeline_cls or DefaultPipeline)())

    def checkout(self, order):
        """Percorso completo: scorte, totale con IVA (VAT), ledger, notifica."""
        inventory.reserve_stock(order["sku"], order["qty"])
        total = pricing.compute_total(order)
        self._pipeline.step(order)
        ledger.record(order, total)
        notifications.send_via(order.get("channel", "email_receipt"), order)
        return total

    def refund_request(self, order):
        """Registra una richiesta di rimborso (storno IVA/VAT)."""
        return ledger.record_refund(order)
