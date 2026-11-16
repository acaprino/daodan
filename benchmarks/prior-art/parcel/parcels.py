"""Spedizioni: registro in memoria."""

MAX_G = 30_000
PARCELS = {}


def clean_zip(raw):
    """CAP in forma canonica: senza spazi, maiuscolo."""
    return raw.replace(" ", "").upper()


def create(parcel_id, name, zip_code, weight_g):
    if not 0 < weight_g <= MAX_G:
        raise ValueError("peso non ammesso")
    PARCELS[parcel_id] = {
        "id": parcel_id,
        "recipient": {"name": name, "zip": clean_zip(zip_code)},
        "weight_g": weight_g,
        "status": "created",
        "events": [],
    }
    return PARCELS[parcel_id]
