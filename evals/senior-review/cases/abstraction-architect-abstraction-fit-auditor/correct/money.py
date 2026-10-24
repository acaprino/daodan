from decimal import Decimal
class MoneyParser:
    @staticmethod
    def parse(value): return int(Decimal(value.strip()) * 100)
