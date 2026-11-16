"""Testi e pulsanti del calendario."""


def label(booking):
    return f"{booking['room']} {booking['start']:02d}:00-{booking['end']:02d}:00"


def can_extend(booking):
    """Mostra il pulsante «Estendi» finché la prenotazione è sotto il massimo."""
    return booking["end"] - booking["start"] < 4
