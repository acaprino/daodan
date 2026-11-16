"""Affidamento al corriere: addebita e mette in viaggio."""
from . import billing, parcels, tracking


def ship(parcel_id, account):
    parcel = parcels.PARCELS[parcel_id]
    if parcel["status"] != "created":
        raise ValueError("passaggio non ammesso")
    billing.charge(account)
    return tracking.add_event(parcel_id, "in_transit")
