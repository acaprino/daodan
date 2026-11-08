"""Signed bearer tokens: a user id, an expiry and an HMAC over both."""
import base64
import hashlib
import hmac
import time


class AuthError(Exception):
    """The request carries no valid token."""


def _sign(secret: bytes, payload: str) -> str:
    digest = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def issue_token(secret: bytes, user: str, ttl_seconds: int, now: float | None = None) -> str:
    if not user.isalnum():
        raise ValueError("user ids are alphanumeric")
    expires = int((time.time() if now is None else now) + ttl_seconds)
    payload = f"{user}.{expires}"
    return f"{payload}.{_sign(secret, payload)}"


def verify_token(secret: bytes, token: str, now: float | None = None) -> str:
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("malformed token")
    user, expires, signature = parts
    if not hmac.compare_digest(signature, _sign(secret, f"{user}.{expires}")):
        raise AuthError("bad signature")
    if not expires.isdigit() or int(expires) < (time.time() if now is None else now):
        raise AuthError("expired token")
    if not user.isalnum():
        raise AuthError("malformed user")
    return user


def require_user(secret: bytes, headers: dict[str, str]) -> str:
    """The user of a request whose header names are lower case."""
    scheme, _, token = headers.get("authorization", "").partition(" ")
    if scheme != "Bearer" or not token:
        raise AuthError("missing bearer token")
    return verify_token(secret, token)
