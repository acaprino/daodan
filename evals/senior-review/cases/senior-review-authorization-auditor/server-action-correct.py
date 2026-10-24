"""Effective host v1 exposes every PUBLIC_ACTIONS entry at a public action
endpoint. dispatch_action is its entire adapter: it never executes PAGE_LOADERS.
The page and public action can be invoked separately with arbitrary requests.
trusted_session(request) is the authoritative server session resolver; it returns
None for anonymous requests or a principal with an immutable tenant. It cannot
be forged by client fields. Only authenticated callers may delete an invoice,
and only within their tenant. Missing invoice IDs return False without mutation.
rows is the server-owned invoice dictionary; key 7 belongs to tenant north.
Function injection is server wiring, never client input. No runtime is supplied.
"""


def invoices_page(request, trusted_session):
    if trusted_session(request) is None:
        raise PermissionError("login")
    return "invoices page"


def delete_invoice(request, invoice_id, rows, trusted_session):
    principal = trusted_session(request)
    if principal is None:
        raise PermissionError("login")
    row = rows.get(invoice_id)
    if row is None:
        return False
    if row["tenant"] != principal["tenant"]:
        raise PermissionError("tenant")
    del rows[invoice_id]
    return True


PUBLIC_ACTIONS = {"delete_invoice": delete_invoice}
PAGE_LOADERS = {"invoices": invoices_page}


def dispatch_action(name, request, invoice_id, rows, trusted_session):
    return PUBLIC_ACTIONS[name](request, invoice_id, rows, trusted_session)
