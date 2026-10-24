# Requirement: Exactly two replicas serve tenant T; at most 10 requests per tenant may be admitted per UTC window across both replicas. Each request costs one unit. The shared store atomic_admit increments only below its limit and keys include tenant/window.

def admit(store, tenant, window):
    return store.atomic_admit((tenant, window), limit=10)
