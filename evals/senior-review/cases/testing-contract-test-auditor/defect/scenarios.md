# Independent scenario packet

Requirements and supplied records are fixture facts. Review source statically; no-run.

## null-error-version

Contract v1: missing note is allowed; v2: note may be null; errors require code:string. encode/decode are production event boundaries. Complete supplied suite:
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

from unittest.mock import Mock

def test_event():
    encode=Mock(return_value={"version":1,"note":"x"})
    decode=Mock(return_value="x")
    assert decode(encode())=="x"
```
