# Requirements: total sums prices; the integration boundary stores and retrieves the computed amount.
import sqlite3
import unittest
def total(prices): return sum(prices)
class CartTests(unittest.TestCase):
    def test_total(self): self.assertEqual(total([2, 3]), 5)
    def test_persist_total(self):
        with sqlite3.connect(":memory:") as db:
            db.execute("CREATE TABLE cart (amount INTEGER)")
            db.execute("INSERT INTO cart VALUES (?)", (total([2, 3]),))
            self.assertEqual(db.execute("SELECT amount FROM cart").fetchone()[0], 5)
