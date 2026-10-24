# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## attempt-provenance

No-run; same supplied CI attempts.
```json
{"candidate":"C","config":"Linux-PG16","seed":42,"attempts":[{"n":1,"result":"failed","assertion":"response within timeout"},{"n":2,"result":"passed"}]}
```
Delivery:
```json
{"candidate":"C","status":"open","attempts":[1,2],"intermittence":"observed","cause":"unknown"}
```

## resource-cleanup

owned_temp provides a distinct directory per worker; port=0 binds an OS-assigned port.
```python
def test_server(server,owned_temp,record):
    record(seed=42,clock="fixed")
    server.start(port=0,db=owned_temp/"db")
    try: assert server.response()=="ready"
    finally:
        server.stop()
        server.join()
```

## measurement-freshness

No-run; only B measurements exist.
```json
{"candidate":"C","timing":"not measured","prior_candidate":"B","prior_seconds":4,"prior_freshness":"stale","required_gap":"payment protection","status":"open"}
```
