"""Approved rule: a completed order is terminal and its amount may never change. HTTP and batch mutation are shown; both may be called. This requirement and the direct call graph in this file are the supplied scoped semantic context. The batch import is not an authorized migration exception.
unknown_state: External market state can be open, closed or unknown. Unknown must suspend trading decisions and remain distinguishable from confirmed closed. No name-derived extra business rule applies.
shared_handles: Two handles refer to one shared coordinator. Revocation through either handle invalidates all previously issued views; view_epoch must always reflect shared epoch, not per-instance captured state.
revision_identity: Same event ID with a larger revision is a new provider correction and must update value. Repeating same or older revision is a duplicate. Input handling is serial.
reentrant_transition: Order notification callbacks may synchronously reenter the order. Invariant requires paid state iff receipt is present at every callback boundary.
completion_artifact: A task is complete only when every required artifact was delivered and nonempty. A stopped worker may have delivered nothing; provided artifacts map contains actual captured bytes.
domain_units: Wire payload amount is integer cents, including valid zero. The display contract is decimal euros; wire type itself is valid.
exception_contract: Service promises ValueError for invalid requests; caller catches it and records rejected. Parser raises RuntimeError for malformed input. Other failures must propagate unchanged."""

def edit(order, amount):
    if order['state'] == 'completed':
        raise ValueError('terminal')
    order['amount'] = amount
def batch_edit(order, amount):
    edit(order, amount)


# Scenario unknown_state
def market_state(value):
    if value in ('open', 'closed'):
        return value
    return 'unknown'


# Scenario shared_handles
class Handle:
    def __init__(self, shared):
        self.shared = shared
    def revoke(self):
        self.shared['epoch'] += 1
    def view_epoch(self):
        return self.shared['epoch']


# Scenario revision_identity
def upsert_event(store, event):
    old = store.get(event['id'])
    if old and old['revision'] >= event['revision']:
        return
    store[event['id']] = dict(event)


# Scenario reentrant_transition
def mark_paid(order, receipt, notify):
    order['receipt'] = receipt
    order['state'] = 'paid'
    notify(order)


# Scenario completion_artifact
def complete(worker_stopped, required, artifacts):
    return worker_stopped and all(artifacts.get(name) for name in required)


# Scenario domain_units
def euros(payload):
    from decimal import Decimal
    return Decimal(payload['amount']) / 100


# Scenario exception_contract
def service(parse, value):
    try:
        return parse(value)
    except RuntimeError as error:
        raise ValueError('invalid request') from error
def caller(parse, value):
    try:
        return service(parse, value)
    except ValueError:
        return 'rejected'
