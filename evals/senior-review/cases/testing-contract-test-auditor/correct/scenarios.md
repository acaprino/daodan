# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## null-error-version

Same v1/v2/error contract.
Version-policy inputs have an integer version field; integer versions other than 1 and 2 must raise ValueError. All admitted events are JSON objects; a present error field is an object whose code must be a string. Missing or non-string error codes must raise ValueError. These are independent virtual source/test declarations, not a runnable collected project.

```python
import json
def validate_event(value):
    if "error" in value and not isinstance(value["error"].get("code"),str):raise ValueError("error code")
    if value["version"] not in (1,2):raise ValueError("version")
    return value

def encode(value):
    return json.dumps(validate_event(value)).encode("utf8")

def decode(raw):
    return validate_event(json.loads(raw.decode("utf8")))
def test_contract():
    cases = [
        ({"version":1}, b'{"version":1}'),
        ({"version":2,"note":None}, b'{"version":2,"note":null}'),
        ({"version":2,"error":{"code":"denied"}}, b'{"version":2,"error":{"code":"denied"}}')]
    for value, independent_wire in cases:
        assert json.loads(encode(value).decode("utf8")) == value
        assert decode(independent_wire) == value
    for independent_wire in [b'{"version":2,"error":{"code":4}}', b'{"version":2,"error":{}}', b'{"version":3}']:
        try:decode(independent_wire)
        except ValueError:pass
        else:raise AssertionError("invalid wire accepted")
    for invalid_event in [{"version":2,"error":{"code":4}}, {"version":2,"error":{}}, {"version":3}]:
        try:encode(invalid_event)
        except ValueError:pass
        else:raise AssertionError("invalid producer event accepted")
```
