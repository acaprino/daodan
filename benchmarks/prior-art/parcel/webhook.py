"""Notifiche del corriere: ogni chiamata porta un passaggio di stato."""
from . import parcels, tracking


def on_event(payload):
    parcel_id = payload["parcel"]
    if parcel_id not in parcels.PARCELS:
        raise ValueError("spedizione sconosciuta")
    status = payload["status"]
    if status not in tracking.NEXT.values():
        raise ValueError("passaggio non ammesso")
    return tracking.add_event(parcel_id, status)
