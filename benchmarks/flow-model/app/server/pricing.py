"""Prices in cents."""
PRICES = {"tea": 450, "cake": 900}
BUNDLE = {"tea", "cake"}


def unit_price(item: str, items: list[str]) -> int:
    price = PRICES.get(item, 0)
    return apply_discount(price, item, items)


def apply_discount(price: int, item: str, items: list[str]) -> int:
    if BUNDLE <= set(items) and item == "tea":
        return price - unit_price("tea", []) // 10
    return price
