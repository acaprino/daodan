"""Spedizioni del vecchio gestionale: il destinatario è una riga di testo «Nome, CAP»."""
from . import parcels


def load(rows):
    for row in rows:
        parcels.PARCELS[row["id"]] = {
            "id": row["id"],
            "recipient": row["dest"],
            "weight_g": row["grams"],
            "status": "created",
            "events": [],
        }
