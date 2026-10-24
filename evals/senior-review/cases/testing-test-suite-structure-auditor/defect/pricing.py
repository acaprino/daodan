from decimal import Decimal, ROUND_HALF_UP

def calculate(raw):
    return format(Decimal(raw).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")
