# Independent scenario packet

Static source/history packets. Requirements are authoritative; no-run.

## contradiction

Contract: an approved order without a coupon charges its total. Neither test uses a coupon.

```python
# product.py
def charge(total): return total * 0.9
# unit/test_charge.py
from product import charge
def test_plain_order(): assert charge(100) == 100
# integration/test_invoice.py
from product import charge
def test_invoice(): assert charge(100) == 90
```

Supplied candidate history for integration/test_invoice.py:
```diff
- assert charge(100) == 100
+ assert charge(100) == 90
```
No requirement or coupon configuration changed in that candidate.

## call-echo

Contract: checkout persists the order and returns its receipt. The save adapter is the persistence boundary; formatting is production logic.

```python
# checkout.py
def checkout(order):
    save(order)
    return format_receipt(order)
# test_checkout.py
from unittest.mock import patch
from checkout import checkout
def test_checkout():
    order={"id":"7","amount":100}
    with patch("checkout.save") as save, patch("checkout.format_receipt") as fmt:
        checkout(order)
        save.assert_called_once_with(order)
        fmt.assert_called_once_with(order)
```

## empty-assertions

Contract: records() returns exactly two records, each with a nonempty id.

```python
# records.py
def records(): return [{"id":"a"},{"id":"b"}]
# test_records.py
def test_records():
    for row in records(): assert row["id"]
```

Supplied mutation report for this exact source:
```json
[{"id":"M1","replacement":"return []","reachable":true,"result":"survived"},{"id":"M2","replacement":"return [dict(id="a"),dict(id="b")]","reachable":true,"result":"survived"}]
```
