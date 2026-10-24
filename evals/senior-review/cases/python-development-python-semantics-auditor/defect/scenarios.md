# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## default-evaluation

Each event without an explicit timestamp receives the clock value at its call; explicit timestamps are honored.

```python
import time
def event(at=time.time()): return at
```

## short-circuit-and-binding

A missing user returns false without calling valid(); normalize uses Python builtin list.

```python
def allowed(user,valid):
    checked=valid(user)
    return user is not None and checked
def normalize(values):
    list=[]
    return list(values)
```

## exception-and-return

Read failures propagate; decode failures return None. An explicit false payload is distinct from missing None.

```python
def load(read,decode):
    try:return decode(read())
    except ValueError:return None
def present(value): return bool(value)
```
Both read and decode may raise ValueError. Caller treats present as the test for missing None.
