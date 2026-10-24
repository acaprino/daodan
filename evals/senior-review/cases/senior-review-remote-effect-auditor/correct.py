"""The gateway commits a charge before a timeout may be observed. It deduplicates identical stable keys for the full retry horizon. The local result is written only after a response. Retrying the same order must produce one remote charge. No network is used by the supplied in-memory gateway.
lease_fence: A worker may pause beyond lease expiry while a replacement obtains a larger epoch. The remote sink rejects epochs lower than its recorded current epoch. Lease check at start alone cannot revoke already-running work.
saga_compensation: After a failed saga step, refund is required exactly once. refund(key) is provider-idempotent, but may time out after commit. Saga stays recovery-pending until refund receipt is durable; retry uses the same saga ID. The admitted retry_compensation caller below keeps saga['id'] unchanged and explicitly assigns distinct attempt-A and attempt-B ids across the timeout. Its refund callback is RefundProvider.refund; each new provider key commits one observable refund and identical keys return the same receipt throughout the retry horizon. The first call commits then raises TimeoutError, and the retry returns normally.
prepared_recovery: Coordinator decision is durably recorded as commit/abort. Recovered participants in prepared state must consult it and resolve; no autonomous heuristic abort is permitted.
outbox_durability: Outbox events remain pending until external durable receipt. send may raise before or after the remote effect; stable key provides provider deduplication. Local removal is durable.
For saga_compensation, saga is an abstract durable record: each assignment persists before the next statement, including when a later refund call times out. For prepared_recovery, decision_log is the durable decision map and participant state assignments persist. For outbox_durability, outbox is an abstract durable map: pop persists removal, and a successful send return is a durable external receipt. These storage guarantees apply only to these named scenarios, not to ordinary Python dictionaries generally.
late_payment: Payment state paid is monotonic. A delayed pending event or redriven old event cannot regress paid. Events have stable operation identity and applied version; states are pending/paid only."""

class Gateway:
    def __init__(self):
        self.charges = {}
        self.drop_first_response = True
    def charge(self, key, amount):
        self.charges.setdefault(key, amount)
        if self.drop_first_response:
            self.drop_first_response = False
            raise TimeoutError('response lost after commit')
        return key
def pay(order, gateway, results, next_attempt):
    if order['id'] in results:
        return results[order['id']]
    receipt = gateway.charge(order['id'], order['amount'])
    results[order['id']] = receipt
    return receipt


# Scenario lease_fence
def effect(worker_epoch, payload, sink):
    return sink.apply_fenced(worker_epoch, payload)


# Scenario saga_compensation
def compensate(saga, refund):
    receipt = refund(saga['id'])
    saga['receipt'] = receipt
    saga['state'] = 'compensated'
    return receipt


# Both admitted deliveries act on the same durable saga record and id. The
# first attempt can commit remotely and lose its response. Recovery retries
# that refund even if a premature state assignment claimed compensation.
def retry_compensation(saga, refund):
    saga['attempt_id'] = 'attempt-A'
    try:
        return compensate(saga, refund)
    except TimeoutError:
        saga['attempt_id'] = 'attempt-B'
        return compensate(saga, refund)

class RefundProvider:
    def __init__(self):
        self.refunds = {}
        self.drop_first_response = True

    def refund(self, key):
        self.refunds.setdefault(key, 'receipt:' + key)
        if self.drop_first_response:
            self.drop_first_response = False
            raise TimeoutError('refund response lost after commit')
        return self.refunds[key]

# Scenario prepared_recovery
def recover_prepared(participant, decision_log):
    decision = decision_log[participant['transaction']]
    participant['state'] = decision
    return decision


# Scenario outbox_durability
def deliver(outbox, key, send):
    event = outbox[key]
    receipt = send(key, event)
    outbox.pop(key)
    return receipt


# Scenario late_payment
def payment_event(state, event):
    if event['version'] <= state['version'] or state['status'] == 'paid':
        return
    state['status'] = event['status']
    state['version'] = event['version']
