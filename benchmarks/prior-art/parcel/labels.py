"""Etichette da stampare."""
from . import parcels

STATUSES = ("created", "in_transit", "delivered")


def _recipient(parcel):
    recipient = parcel["recipient"]
    if isinstance(recipient, str):
        name, _, zip_code = recipient.rpartition(", ")
        return name, parcels.clean_zip(zip_code)
    return recipient["name"], recipient["zip"]


def _history(parcel):
    events = parcel["events"]
    if events is None:
        return []
    if not isinstance(events, list):
        events = [events]
    return events


def text(parcel_id):
    parcel = parcels.PARCELS[parcel_id]
    if parcel["status"] not in STATUSES:
        raise ValueError("stato sconosciuto")
    name, zip_code = _recipient(parcel)
    steps = " > ".join(["created", *_history(parcel)])
    return f"{name} | {zip_code} | {parcel['weight_g'] / 1000:.1f} kg | {steps}"
