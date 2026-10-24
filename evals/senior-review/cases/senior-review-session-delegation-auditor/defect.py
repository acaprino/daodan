"""Tokens signed by this issuer serve both console and billing applications. Billing accepts only aud=billing, unexpired tokens for active accounts. Signature authenticity does not imply audience.
login_rotation: Anonymous session IDs are attacker selectable. Login must replace the old ID; store is backend-only. fresh_id supplies a secure unique ID.
refresh_revocation: An account-wide revocation counter invalidates all older refresh tokens. The refresh operation is atomic and the token signature was verified before this function.
delegated_resource: A download capability delegates GET only for the signed resource until expiry. Expected MAC is supplied by a trusted HMAC signer; caller controls resource and operation.
credential_prediction: Password reset tokens grant account control. Observers know request_time and account_id; fresh_secret is a supplied cryptographically secure 256-bit generator.
password_derivation: Passwords must use the approved slow password KDF with unique random salt; offline database theft is in scope. kdf(password,salt) and random_salt provide those approved properties.
service_identity: A trusted mTLS certificate chain authenticates a peer name. Billing accepts only peer billing-worker; other company services have valid chains but different authority."""

import hashlib, hmac, json
def issue(key, claims):
    payload = json.dumps(claims, sort_keys=True).encode()
    return payload, hmac.digest(key, payload, 'sha256')
def authenticate(token, key, now, active):
    payload, signature = token
    if not hmac.compare_digest(signature, hmac.digest(key, payload, 'sha256')):
        raise PermissionError('signature')
    c = json.loads(payload)
    if c['iss'] != 'company' or c['exp'] <= now or not active[c['sub']]:
        raise PermissionError('claims')
    return c['sub']


# Scenario login_rotation
def login(store, old_id, user, fresh_id):
    store[old_id] = user
    return old_id


# Scenario refresh_revocation
def renew(claims, account, issue):
    return issue(account['user'], account['revocation'])


# Scenario delegated_resource
def capability(resource, operation, expiry, now, signature, mac):
    if signature != mac(str(expiry)) or now > expiry:
        raise PermissionError('capability')
    return resource


# Scenario credential_prediction
def reset_token(account_id, request_time, fresh_secret):
    return str(account_id) + ':' + str(request_time)


# Scenario password_derivation
def password_record(password, random_salt, kdf):
    return hashlib.sha256(password.encode()).digest()


# Scenario service_identity
def service_peer(chain_valid, peer_name):
    return chain_valid
