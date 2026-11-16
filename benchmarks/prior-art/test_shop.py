"""Ogni seme di shop/ esiste e ogni esca è corretta: i test passano sulla fixture così com'è."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shop import api, catalog, orders, pricing, returns, stats  # noqa: E402

STOCK = copy.deepcopy(catalog.PRODUCTS)


class Base(unittest.TestCase):
    def setUp(self):
        catalog.PRODUCTS.clear()
        catalog.PRODUCTS.update(copy.deepcopy(STOCK))
        orders.ORDERS.clear()


class SeedTest(Base):
    def test_s1_the_copied_normalizer_keeps_the_dash_and_the_refund_is_zero(self):
        orders.place("o1", 7, [{"sku": "ab-12", "qty": 2}])
        self.assertNotEqual(returns._clean_sku("ab-12"), catalog.normalize_sku("ab-12"))
        self.assertEqual(returns.refund("o1", ["ab-12"])["amount"], 0.0)
        self.assertEqual(returns.refund("o1", ["ab12"])["amount"], 39.8)

    def test_s2_the_second_total_equals_the_first_on_every_sample(self):
        samples = (
            [],
            [{"price": 19.90, "qty": 3}],
            [{"price": 0.125, "qty": 1}],
            [{"price": 4.50, "qty": 7}, {"price": 0.005, "qty": 1}],
        )
        for lines in samples:
            self.assertEqual(returns._total(lines), pricing.lines_total(lines))

    def test_s3_void_and_cancel_leave_the_same_state(self):
        orders.place("o1", 7, [{"sku": "ZX9", "qty": 3}])
        orders.place("o2", 7, [{"sku": "ZX9", "qty": 3}])
        orders.cancel("o1")
        returns.void("o2")
        self.assertEqual(orders.ORDERS["o1"], orders.ORDERS["o2"])
        self.assertEqual(catalog.PRODUCTS["ZX9"]["stock"], STOCK["ZX9"]["stock"])
        for done in (orders.cancel, returns.void):
            with self.assertRaises(ValueError):
                done("o1")

    def test_s4_entry_and_domain_reject_the_same_quantities(self):
        for qty, accepted in ((0, False), (1, True), (20, True), (21, False)):
            status, _ = api.post_order({"id": f"a{qty}", "customer_id": 7, "lines": [{"sku": "ZX9", "qty": qty}]})
            self.assertEqual(status == 201, accepted)
            self.setUp()
            try:
                orders.place(f"d{qty}", 7, [{"sku": "ZX9", "qty": qty}])
                placed = True
            except ValueError:
                placed = False
            self.assertEqual(placed, accepted)
            self.setUp()

    def test_s5_the_only_producer_writes_one_customer_shape(self):
        order = orders.place("o1", 7, [{"sku": "ZX9", "qty": 1}])
        self.assertEqual(order["customer"], {"id": 7})
        self.assertEqual(returns._customer_id(order["customer"]), 7)


class DecoyTest(Base):
    def test_e1_dashboard_rounding_differs_from_money_rounding_on_purpose(self):
        self.assertEqual(stats.round_avg(0.125), 0.12)
        self.assertEqual(pricing.round_cents(0.125), 0.13)

    def test_e2_the_type_check_stops_what_the_range_check_cannot_judge(self):
        body = {"id": "o1", "customer_id": 7, "lines": [{"sku": "ZX9", "qty": "3"}]}
        self.assertEqual(api.post_order(body), (400, "qty deve essere un intero"))
        with self.assertRaises(TypeError):
            orders.place("o1", 7, body["lines"])


if __name__ == "__main__":
    unittest.main()
