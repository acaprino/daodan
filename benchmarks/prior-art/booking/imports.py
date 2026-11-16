"""Importazione delle prenotazioni dal vecchio foglio di calcolo."""
from . import bookings, slots


def load(rows):
    loaded = []
    for row in rows:
        bookings._check(row["room"], row["start"], row["end"], row["people"])
        new = {
            "id": len(bookings.BOOKINGS) + 1,
            "room": row["room"],
            "day": row["day"],
            "start": row["start"],
            "end": row["end"],
            "owner": row["owner"],
            "people": row["people"],
        }
        for other in bookings.BOOKINGS:
            if other["room"] == new["room"] and other["day"] == new["day"] and slots.overlap(new, other):
                raise ValueError("sala occupata")
        bookings.BOOKINGS.append(new)
        loaded.append(new)
    return loaded
