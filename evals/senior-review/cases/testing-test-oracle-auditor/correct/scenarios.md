# Independent scenario packet

Static source/history packets. Requirements are authoritative; no-run.

## contradiction

Contract: approved orders without coupons charge their total; coupon TEN reduces it by 10%.

```python
def charge(total,coupon=None): return total*0.9 if coupon=="TEN" else total
def test_plain(): assert charge(100)==100
def test_coupon(): assert charge(100,"TEN")==90
```

## call-echo

Contract: checkout persists the order and returns receipt id/amount. The dictionary is the declared persistence test boundary.

```python
def format_receipt(order): return {"receipt_id":order["id"],"amount":order["amount"]}
def checkout(order,store):
    store[order["id"]]=dict(order)
    return format_receipt(order)
def test_checkout():
    store={}
    receipt=checkout({"id":"7","amount":100},store)
    assert store["7"]=={"id":"7","amount":100}
    assert receipt=={"receipt_id":"7","amount":100}
```

## empty-assertions

Contract: records() returns exactly two records, each with a nonempty id.

```python
def records(): return [{"id":"a"},{"id":"b"}]
def test_records():
    rows=records()
    assert len(rows)==2
    for row in rows: assert row["id"]
```
Supplied report: M1 (`return []`) killed; M2 (`return [dict(id="a"),dict(id="b")]`) survived.
