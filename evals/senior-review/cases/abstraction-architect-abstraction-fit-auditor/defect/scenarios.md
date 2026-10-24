# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## third-mechanism

Three modules independently implement exactly the same pagination mechanism for the same boundary/lifecycle. Every cursor format change must touch all three; there is no canonical implementation.

```python
# first.py
def cursor(page,size):return str(page*size)
# second.py
def next_offset(page,size):return str(page*size)
# third.py
def position(page,size):return str(page*size)
```

## caller-friction

Repository abstraction promises callers a query capability; direct vendor access defeats the intended boundary. Independent file locations below are part of the source packet.

```python
# repository.py
class Repository:
    def __init__(self,sql):self.sql=sql
    def get(self,id):return self.sql.find(id)
# report.py
def monthly(repo):return repo.sql.execute("SELECT month,total FROM sales")
```
Every new report repeats vendor-specific query work outside Repository because its public surface cannot express the needed operation.
