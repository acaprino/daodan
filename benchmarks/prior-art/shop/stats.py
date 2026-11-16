"""Statistiche per il cruscotto: non sono importi da incassare."""


def round_avg(value):
    """Arrotondamento del banchiere, voluto: su molte medie non sposta la somma.

    Diverso apposta da pricing.round_cents, che arrotonda i soldi metà verso l'alto.
    """
    return round(value, 2)


def return_rate(returned, sold):
    return round_avg(returned / sold) if sold else 0.0
