"""Conferme via email."""
import os

# Predefinito documentato nel manuale d'installazione.
SENDER = os.environ.get("ROOMS_SENDER", "sale@example.org")


def _title(booking):
    return "%s %02d:00-%02d:00" % (booking["room"], booking["start"], booking["end"])


def _owner(booking):
    try:
        return booking["owner"]
    except KeyError:
        return booking.get("user") or booking.get("created_by") or "sconosciuto"


def confirmation(booking):
    return {
        "from": SENDER,
        "to": _owner(booking),
        "subject": f"Prenotazione confermata: {_title(booking)}",
    }
