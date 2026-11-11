from . import pricing


def amount_for(items: list[str]) -> int:
    return sum(pricing.unit_price(item, items) for item in items)
