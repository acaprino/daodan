"""At most three password-verification attempts per canonical account per
60-second window are permitted across all replicas, including failed attempts.
The public network can reach only gateway_receive; direct backend access is
denied by the effective network policy. Request account, trace_id and password
are attacker controlled. canonical_account resolves spelling aliases to the
same existing account. limiter.atomic_admit(key, limit=3) is a shared atomic
increment-if-below-limit across every gateway replica. The passed window is
server computed and fixed for the four requests under review. Authentication
is not itself a quota check; every call performs one password verification.
All backend routes are exactly the gateway path below. No runtime was supplied.
"""


def backend_login(account, password, authenticate):
    return authenticate(account, password)


def gateway_receive(request, window, limiter, canonical_account, authenticate):
    account = canonical_account(request["account"])
    if not limiter.atomic_admit((request["trace_id"], window), limit=3):
        return "limited"
    return backend_login(account, request["password"], authenticate)
