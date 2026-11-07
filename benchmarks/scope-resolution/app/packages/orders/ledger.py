"""Registro contabile: voci ordine con lockfile e breakdown IVA (VAT)."""
import os
from pathlib import Path

LEDGER_PATH = Path("ledger.log")
LOCK_PATH = Path("ledger.lock")


def _acquire_lock():
    return os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)


def record(order, total):
    """Registra ordine e totale (IVA/VAT inclusa) nel ledger."""
    fd = _acquire_lock()
    try:
        with LEDGER_PATH.open("a", encoding="utf-8") as stream:
            stream.write(f"{order.get('id', '?')}\t{total}\n")
    finally:
        os.close(fd)
        LOCK_PATH.unlink(missing_ok=True)
    return total


def record_refund(order):
    """Registra uno storno (rimborso) con la quota IVA/VAT."""
    fd = _acquire_lock()
    try:
        with LEDGER_PATH.open("a", encoding="utf-8") as stream:
            stream.write(f"{order.get('id', '?')}\tREFUND\n")
    finally:
        os.close(fd)
        LOCK_PATH.unlink(missing_ok=True)
    return order
