# Requirement: Exactly two replicas serve tenant T; at most 10 requests per tenant may be admitted per UTC window across both replicas. Each request costs one unit. The shared store atomic_admit increments only below its limit and keys include tenant/window.

counters = {}
def admit(store, tenant, window):
    key = (tenant, window)
    if counters.get(key, 0) >= 10:
        return False
    counters[key] = counters.get(key, 0) + 1
    return True
