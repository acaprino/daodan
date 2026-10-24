"""A caller may make at most three transport attempts total per request during outage. Transport raises TimeoutError before any effect. The client and application both retry. The bound is contractual, not a universal tuning threshold.
remaining_deadline: Two sequential remote calls must finish within the caller absolute deadline. call(timeout) spends its entire timeout before returning if the service is slow; clock reports elapsed time and each call respects supplied timeout.
breaker_recovery: An open per-destination breaker must allow one probe after cooldown; isolated destination state is supplied and the transport has its own cancellation/deadline guarantee. No dead connection is permitted to monopolize other destinations.
honest_outcome: Remote timeout is an unknown effect outcome; request ID allows later reconciliation. Returning confirmed success without a receipt is prohibited.
destination_bulkhead: Failed destination A must not consume destination B reserved worker capacity. acquire chooses a supplied finite pool; work may block until its enforced long deadline.
half_open_progress: A half-open connection may make receive wait forever. receive(deadline,cancel_on_timeout=True) guarantees underlying work stops at deadline; caller must not leave work alive after giving up."""

def client(transport):
    for attempt in range(3):
        try:
            return transport()
        except TimeoutError:
            if attempt == 2:
                raise
def request(transport):
    for attempt in range(3):
        try:
            return client(transport)
        except TimeoutError:
            if attempt == 2:
                raise


# Scenario remaining_deadline
def chain(call, clock, deadline):
    allowance = deadline - clock()
    call(timeout=allowance)
    return call(timeout=allowance)


# Scenario breaker_recovery
def allowed(state, now):
    return state['mode'] != 'open'


# Scenario honest_outcome
def remote_status(request_id, call):
    try:
        return {'status': 'complete', 'receipt': call(request_id)}
    except TimeoutError:
        return {'status': 'complete'}


# Scenario destination_bulkhead
def destination_work(pools, destination, work):
    with pools['shared'].acquire():
        return work()


# Scenario half_open_progress
def bounded_receive(connection, deadline):
    return connection.receive()
