"""Confronti tra fasce orarie della stessa sala e dello stesso giorno."""


def overlap(a, b):
    """Vero se due fasce semiaperte [start, end) si sovrappongono."""
    return a["start"] < b["end"] and b["start"] < a["end"]


def needs_gap(a, b):
    """Vero se tra due fasce non resta l'ora per le pulizie del catering.

    Estremi inclusi, voluto: due fasce che si toccano non si sovrappongono
    per overlap, ma non lasciano l'ora libera.
    """
    return a["start"] <= b["end"] and b["start"] <= a["end"]
