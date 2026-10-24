"""Authenticated callers may read invoices only for their tenant, including batch export. The principal is server established; invoice IDs are caller input.
privileged_fields: Self-service profile updates may change display only. Stored role and tenant are server controlled.
pooled_rls: Connection tenant is the effective RLS scope for rows. A pooled connection may carry the prior caller tenant; checkout must bind the new authenticated tenant before query."""

INVOICES = {7: {'tenant': 'north', 'amount': 20}, 8: {'tenant': 'south', 'amount': 30}}
def invoice(principal, invoice_id):
    row = INVOICES[invoice_id]
    if row['tenant'] != principal['tenant']:
        raise PermissionError('tenant')
    return row.copy()
def export(principal, ids):
    return [INVOICES[i].copy() for i in ids]


# Scenario privileged_fields
def update_profile(row, fields):
    row.update(fields)


# Scenario pooled_rls
def pooled_read(connection, principal, rows):
    return [r for r in rows if r['tenant'] == connection['tenant']]
