"""Stati di una spedizione e loro passaggi."""
from . import parcels

NEXT = {"created": "in_transit", "in_transit": "delivered"}


def add_event(parcel_id, status):
    if parcel_id not in parcels.PARCELS:
        raise ValueError("spedizione sconosciuta")
    parcel = parcels.PARCELS[parcel_id]
    if NEXT.get(parcel["status"]) != status:
        raise ValueError("passaggio non ammesso")
    parcel["status"] = status
    parcel["events"].append(status)
    return parcel
