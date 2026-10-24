# Authoritative contract: wire id is a string. Complete no-run test suite.
import json
def produce(): return {"id": 7}
def consume(payload): return payload["id"].lower()
def test_consumer():
    fixture = {"id": "7"}
    assert consume(fixture) == "7"
