# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## default-evaluation

Each event without an explicit timestamp receives the clock value at its call; explicit timestamps are honored.

```python
import time
def event(at=None): return time.time() if at is None else at
```

## short-circuit-and-binding

A missing user returns false without calling valid(); normalize uses Python builtin list.

```python
def allowed(user,valid): return user is not None and valid(user)
def normalize(values): return list(values)
```
valid(None) raises by its declared contract.

## exception-and-return

Read failures propagate; decode failures return None. An explicit false payload is distinct from missing None.

```python
def load(read,decode):
    raw=read()
    try:return decode(raw)
    except ValueError:return None
def present(value): return value is not None
```
