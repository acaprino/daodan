# Requirement: Feature new_checkout needs schema_v2. If the flag provider is unavailable, supported v1 and v2 clients must continue legacy checkout. provider.get raises ConnectionError on outage; both branch functions exist and legacy is supported.

def checkout(provider, schema_v2, legacy, modern):
    try:
        enabled = provider.get('new_checkout')
    except ConnectionError:
        enabled = True
    if enabled:
        if not schema_v2:
            raise RuntimeError('schema incompatible')
        return modern()
    return legacy()
