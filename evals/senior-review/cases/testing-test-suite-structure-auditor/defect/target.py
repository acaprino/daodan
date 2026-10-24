# Requirement: total sums prices. No historical bugfix distinction exists between these unit cases.
import unittest
def total(prices): return sum(prices)
class CartTests(unittest.TestCase):
    def test_total(self): self.assertEqual(total([2, 3]), 5)
    def test_checkout_amount(self): self.assertEqual(total([2, 3]), 5)
