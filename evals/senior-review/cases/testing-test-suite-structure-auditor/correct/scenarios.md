# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## layer

Project convention: unit isolates ports; integration proves SQL under a 10s budget.
```python
# tests/unit/customer.py
def test_service():
    rows=[]
    service_create(rows.append,1)
    assert rows==[1]
# tests/integration/customer_sql.py
def test_insert(db):
    db.execute("INSERT INTO customer(id) VALUES (1)")
    assert db.execute("SELECT id FROM customer").fetchone()[0]==1
```
Supplied timing: integration test_insert 2s; unit test_service 1ms.

## moved-behavior

History: old_price.py renamed to pricing.py; rounding requirement unchanged.
```python
from pricing import calculate
def test_rounding(): assert calculate("2.675")=="2.68"
```

## focused-collection

CI must collect success and rejection. The separate linux_kernel test concerns Linux-only behavior.
```ts
test("success", successCheck);
test("rejection", rejectionCheck);
test.skipIf(platform!=="linux")("linux_kernel", linuxCheck);
```

## Admitted behavior owners and runner contracts

The virtual test snippets resolve pricing.calculate to pricing.py, service_create to customer.py, and successCheck/rejectionCheck/linuxCheck to collection.ts in this same admitted target. These are complete owners for the independent snippets. The layer scenario's db fixture starts with an empty customer(id INTEGER) table and rolls back its test transaction; the psycopg example reaches its explicitly declared fixture service. The pytest/unittest declarations and the independent Vitest snippets have their usual declared collection semantics, including skip and only. platform is the supplied CI target platform; the Linux-only scene is not a required success/rejection substitute. Fixture-service and runner declarations are hypothetical input contracts; no tool installation, collection or service run is established.
