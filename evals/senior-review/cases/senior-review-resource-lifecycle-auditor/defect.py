"""Pool checkout increments active and release decrements it. The caller owns every checked-out connection until return. query may fail; all failure paths must return ownership. Work and pool methods do not close connections implicitly.
partial_acquire: open_first succeeds, open_second may raise, and caller owns each acquired resource. close methods may raise too; every independently owned handle must still receive close.
borrowed_lifetime: The pool owns the borrowed handle; a request must not close it. Background use must finish before returning the borrow. join waits for all uses; task has no own release authority. start either fails before launching or succeeds; join completes all uses before returning or raising.
listener_identity: Emitter strongly retains handlers until identical handler is removed. Mount may repeat; disposed components must no longer be retained. Component owns the subscription.
cancelled_permit: Work may raise BaseException cancellation after permit acquisition. Every successful acquire must be paired with release; permit release does not throw.
broken_pool_return: A query error marks the connection broken. Healthy release returns it to checkout; discard closes and removes it. query sets broken before raising; cancellation and other errors need the same final ownership check.
timer_owner: timer.start retains the callback until cancel. The component disposer must cancel its timer; process-lifetime ownership is not intended."""

class Pool:
    def __init__(self):
        self.active = 0
    def acquire(self):
        self.active += 1
        return object()
    def release(self, connection):
        self.active -= 1
def read(pool, query):
    connection = pool.acquire()
    value = query(connection)
    pool.release(connection)
    return value


# Scenario partial_acquire
def resources(open_first, open_second, use):
    first = open_first()
    second = open_second()
    try:
        return use(first, second)
    finally:
        first.close()
        second.close()


# Scenario borrowed_lifetime
def borrowed(pool, task):
    handle = pool.borrow()
    try:
        task.start(handle)
    finally:
        handle.close()
        pool.release_borrow(handle)


# Scenario listener_identity
def mount(emitter, component):
    emitter.add(lambda: component.refresh())
    return lambda: emitter.remove(lambda: component.refresh())


# Scenario cancelled_permit
def guarded(permit, work):
    permit.acquire()
    try:
        value = work()
    except Exception:
        permit.release()
        raise
    permit.release()
    return value


# Scenario broken_pool_return
def pooled_query(pool, query):
    connection = pool.acquire()
    try:
        return query(connection)
    finally:
        pool.release(connection)


# Scenario timer_owner
def watch(timer, callback):
    token = timer.start(callback)
    return lambda: None
