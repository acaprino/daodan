"""Prenotazioni: creazione ed estensione."""
from . import rooms, slots

BOOKINGS = []


def _check(room, start, end, people):
    if room not in rooms.ROOMS:
        raise ValueError("sala sconosciuta")
    if not 0 <= start < end <= 24:
        raise ValueError("orario non valido")
    if end - start > rooms.MAX_HOURS:
        raise ValueError("durata oltre il massimo")
    if people > rooms.ROOMS[room]["capacity"]:
        raise ValueError("troppe persone")


def create(room, day, start, end, owner, people=1):
    _check(room, start, end, people)
    new = {
        "id": len(BOOKINGS) + 1,
        "room": room,
        "day": day,
        "start": start,
        "end": end,
        "owner": owner,
        "people": people,
    }
    for other in BOOKINGS:
        if other["room"] == room and other["day"] == day and slots.overlap(new, other):
            raise ValueError("sala occupata")
    BOOKINGS.append(new)
    return new


def extend(booking_id):
    """Allunga di un'ora, se la regola e la sala lo permettono."""
    booking = next(b for b in BOOKINGS if b["id"] == booking_id)
    longer = {**booking, "end": booking["end"] + 1}
    _check(longer["room"], longer["start"], longer["end"], longer["people"])
    for other in BOOKINGS:
        if other is booking:
            continue
        if other["room"] == longer["room"] and other["day"] == longer["day"] and slots.overlap(longer, other):
            raise ValueError("sala occupata")
    booking["end"] = longer["end"]
    return booking
