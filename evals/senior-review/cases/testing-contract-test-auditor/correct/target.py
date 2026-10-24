# Authoritative contract: wire id is a string. Complete no-run test suite.
import json
def produce(): return {"id": "7"}
def consume(payload): return payload["id"].lower()
def test_boundary():
    wire = json.loads(json.dumps(produce()))
    assert isinstance(wire["id"], str)
    assert consume(wire) == "7"
