"""Addebiti sul conto del mittente."""

BALANCE = {"acme": 100.0}
PRICE = 7.5


def charge(account):
    if BALANCE[account] < PRICE:
        raise ValueError("credito insufficiente")
    BALANCE[account] -= PRICE
