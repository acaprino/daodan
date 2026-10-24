# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## redundant-representations

The internal Customer is current mutable domain state. Published CustomerEvent records are immutable external facts with their own owner and lifecycle; they must retain their publication-time representation.

Customer is canonical. A separately owned external CustomerEvent freezes the fields present at publication and intentionally has a different lifecycle; mapping occurs only at that event boundary.

## maintained-derived-state

Cart items are the authoritative current contents; total must reflect their current sum. Reporting snapshots are immutable historical records.

```python
# cart.py
class Cart:
    def __init__(self): self.items=[]
    @property
    def total(self): return sum(item.price for item in self.items)
```
A separate reporting snapshot is immutable and intentionally historical.

