"""Notifiche cliente: il canale arriva dalla configurazione come stringa.

Il gestore è letto dalla variabile d'ambiente ORDER_NOTIFY_HANDLERS
(formato "canale=modulo:funzione,...") e caricato con importlib.
La ricevuta riporta l'IVA (VAT).
"""
import importlib
import os


def _handler_for(channel):
    """Risolve 'modulo:funzione' dalla configurazione d'ambiente per il canale."""
    mapping = dict(item.split("=", 1) for item in os.environ["ORDER_NOTIFY_HANDLERS"].split(","))
    module_name, func_name = mapping[channel].split(":")
    return getattr(importlib.import_module(module_name), func_name)


def send_via(channel, order):
    """Invia la notifica sul canale configurato (es. 'email_receipt'), IVA inclusa."""
    sender = _handler_for(channel)
    return sender(order)
