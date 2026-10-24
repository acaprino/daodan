"""The provider signs timestamp, a dot, and the original raw JSON bytes with HMAC-SHA256. Events older than 300 seconds must be rejected before effects. Authentic retries inside that window are allowed; effect deduplication is supplied by apply_event.
verification_failure: verify authenticates the exact raw bytes and raises on any mismatch; dispatch creates an irreversible business effect. Verification failure must prevent dispatch."""

import hmac, json
def receive(raw, timestamp, signature, key, now, apply_event):
    signed = str(timestamp).encode() + b'.' + raw
    if not hmac.compare_digest(signature, hmac.digest(key, signed, 'sha256')):
        raise PermissionError('signature')
    apply_event(json.loads(raw))


# Scenario verification_failure
def callback(raw, verify, dispatch):
    try:
        verify(raw)
    except ValueError:
        pass
    dispatch(raw)
