# Independent scenario packet

Each section is independent; the file labels identify synthetic source paths. Requirements are authoritative for this fixture only. Review statically, without executing or editing.

## redundant-representations

One internal Customer concept has one lifecycle, owner and trust boundary. All three representations below must change together for every field addition; no serialization or external boundary exists.

`customer.py`: Customer(name,email); `customer_copy.py`: CustomerCopy(name,email); `mapping.py`: manual name/email copy both directions, maintained with every field change. All consumers interchange both types in the same domain.

## maintained-derived-state

Cart items and total concern one authoritative cart. Multiple code paths mutate both and a repair job exists solely to fix divergence.

```python
# cart.py
def add(cart,item):cart.items.append(item);cart.total+=item.price
def remove(cart,item):cart.items.remove(item)
# repairs.py
def repair(cart):cart.total=sum(item.price for item in cart.items)
```

