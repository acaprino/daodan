"""A successful admin rename must be immediately visible to all subsequent reads in this single-process service. Cache contains copies, all writer paths are shown, and calls are sequential; no eventual consistency delay is allowed.
tenant_key: Two tenants may share user ID. Profiles differ by tenant; get_profile reads authoritative data. Cache is shared across tenants.
stale_fill: A fill reads version V, pauses, then commits its result. Invalidation advances current_version even on deletion; only a result matching current version may be published. apply is atomic.
replica_decision: After changing an entitlement, confirmation must reflect the authoritative committed value immediately. Replica may lag by an explicitly permitted second, but that lag is not allowed for the confirmation decision."""

STORE = {1: 'old'}
CACHE = {}
def read(key):
    if key not in CACHE:
        CACHE[key] = STORE[key]
    return CACHE[key]
def rename(key, value):
    STORE[key] = value
    CACHE.pop(key, None)
def admin_rename(key, value):
    rename(key, value)


# Scenario tenant_key
def profile(cache, tenant, user_id, get_profile):
    key = (tenant, user_id)
    if key not in cache:
        cache[key] = get_profile(tenant, user_id)
    return cache[key]


# Scenario stale_fill
def complete_fill(cache, key, captured_version, current_version, value):
    if captured_version == current_version:
        cache[key] = value


# Scenario replica_decision
def entitlement_confirmation(primary, replica, user):
    return primary.read(user)
