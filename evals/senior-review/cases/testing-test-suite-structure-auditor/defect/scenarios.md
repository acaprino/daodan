# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## layer

Project convention: unit cases isolate ports and take at most 100ms; integration tests own SQL. psycopg.connect below reaches the supplied Postgres service.

```python
# tests/unit/customer.py
import psycopg
def test_insert():
    with psycopg.connect("postgresql://fixture-db/customer") as db:
        db.execute("INSERT INTO customer(id) VALUES (1)")
        assert db.execute("SELECT id FROM customer").fetchone()[0]==1
```
Supplied timing record: candidate C, test_insert, 2s.

## moved-behavior

Contract: rounding regression stays protected. Git history: old_price.py renamed to pricing.py with calculate unchanged; no other test covers it.
```python
from pricing import calculate
import unittest
@unittest.skip("old_price.py deleted")
def test_rounding(): assert calculate("2.675")=="2.68"
```

## focused-collection

CI must collect success and rejection; Vitest supports test.only.
```ts
test.only("success", successCheck);
test("rejection", rejectionCheck);
```

## Admitted behavior owners and runner contracts

The virtual test snippets resolve pricing.calculate to pricing.py, service_create to customer.py, and successCheck/rejectionCheck/linuxCheck to collection.ts in this same admitted target. These are complete owners for the independent snippets. The layer scenario's db fixture starts with an empty customer(id INTEGER) table and rolls back its test transaction; the psycopg example reaches its explicitly declared fixture service. The pytest/unittest declarations and the independent Vitest snippets have their usual declared collection semantics, including skip and only. platform is the supplied CI target platform; the Linux-only scene is not a required success/rejection substitute. Fixture-service and runner declarations are hypothetical input contracts; no tool installation, collection or service run is established.
