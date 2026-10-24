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
    order['amount'] = amount


# Scenario unknown_state
def market_state(value):
    return 'open' if value == 'open' else 'closed'


# Scenario shared_handles
class Handle:
    def __init__(self, shared):
        self.shared = shared
        self.epoch = shared['epoch']
    def revoke(self):
        self.shared['epoch'] += 1
        self.epoch = self.shared['epoch']
    def view_epoch(self):
        return self.epoch


# Scenario revision_identity
def upsert_event(store, event):
    if event['id'] in store:
        return
    store[event['id']] = dict(event)


# Scenario reentrant_transition
def mark_paid(order, receipt, notify):
    order['state'] = 'paid'
    notify(order)
    order['receipt'] = receipt


# Scenario completion_artifact
def complete(worker_stopped, required, artifacts):
    return worker_stopped


# Scenario domain_units
def euros(payload):
    return payload['amount']


# Scenario exception_contract
def service(parse, value):
    return parse(value)
def caller(parse, value):
    try:
        return service(parse, value)
    except ValueError:
        return 'rejected'
