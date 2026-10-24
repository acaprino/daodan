"""The service API credential may be read only by the backend. Public diagnostics are anonymous and must exclude all secret values. Configuration is supplied by trusted deployment; no live secret is embedded here.
nonce_scope: The supplied AEAD seal(key_id,nonce,data) requires a nonce never reused under a key. The caller provides arbitrary data; allocate_nonce(key_id) atomically allocates unique nonces for the entire key lifetime.
retired_key: active_ids is authoritative; retired keys are retained solely to read an archive and must not authorize current requests. verify cryptographically validates the signature.
comparison_oracle: The HTTP response must not disclose secret prefixes. Diagnostics currently return the comparison result and inspected-prefix count to the caller; secrets have fixed length."""

def diagnostics(config):
    return {'status': 'ready', 'region': config['region']}


# Scenario nonce_scope
def encrypt(key_id, data, allocate_nonce, seal):
    return seal(key_id, allocate_nonce(key_id), data)


# Scenario retired_key
def authorize_signature(key_id, signature, payload, keys, active_ids, verify):
    return key_id in active_ids and verify(keys[key_id], signature, payload)


# Scenario comparison_oracle
def token_check(candidate, secret):
    import hmac
    return {'ok': hmac.compare_digest(candidate, secret)}
