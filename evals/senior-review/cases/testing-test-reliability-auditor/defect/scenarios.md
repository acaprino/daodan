# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## attempt-provenance

Required gate retains every attempt; no-run.
```json
{"candidate":"C","config":"Linux-PG16","seed":42,"attempts":[{"n":1,"result":"failed","assertion":"response within timeout"},{"n":2,"result":"passed"}]}
```
Submitted delivery:
```json
{"candidate":"C","status":"passed","attempts":[2],"intermittence":"none"}
```

## resource-cleanup

Two test workers run concurrently; server.start returns after readiness; assert failure raises.
```python
def test_server(server):
    server.start(port=9000,db="/tmp/shared.db")
    assert server.response()=="ready"
    server.stop()
    server.join()
```
No fixture teardown exists. Seed and clock are not recorded in the supplied command.

## measurement-freshness

Current candidate C must meet 5s; no-run. Only report supplied:
```json
{"candidate":"B","duration_seconds":4,"coverage_percent":90,"protected_modules":["orders"]}
```
Delivery:
```json
{"candidate":"C","verified_seconds":4,"coverage":"complete"}
```
Required payment behavior has no mapped test in the supplied complete test inventory.
