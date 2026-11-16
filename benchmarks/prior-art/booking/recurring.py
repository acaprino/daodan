"""Prenotazioni ricorrenti: la stessa fascia in più giorni."""
from . import bookings, rooms, slots


def book_weekly(room, days, start, end, owner, people=1, catering=False):
    if room not in rooms.ROOMS:
        raise ValueError("sala sconosciuta")
    if end - start > rooms.MAX_HOURS:
        raise ValueError("durata oltre il massimo")
    made = []
    for day in days:
        slot = {"start": start, "end": end}
        if catering and any(
            other["room"] == room and other["day"] == day and slots.needs_gap(slot, other)
            for other in bookings.BOOKINGS
        ):
            raise ValueError("serve un'ora libera per le pulizie")
        made.append(bookings.create(room, day, start, end, owner, people))
    return made
