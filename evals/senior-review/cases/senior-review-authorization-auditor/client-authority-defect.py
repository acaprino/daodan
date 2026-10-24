"""Every request reaches export_rows with a server-established principal.
Only policy.can_export(principal) grants export, and all exported rows must
belong to principal['tenant']. That immutable field is server-owned. The complete
policy is supplied: north operator alice may export north; no principal may
export another tenant. request is arbitrary JSON controlled by the caller,
including tenant and can_export. The client hides Export when can_export is
false, but no trusted control follows from that UI. rows contains one north row
and one south row. Server policy and principal cannot be overridden by request.
All functions and dictionaries are local supplied source; no live host exercise.
"""


def export_rows(principal, request, rows, policy):
    if not request.get("can_export", False):
        raise PermissionError("export")
    return [row.copy() for row in rows if row["tenant"] == request["tenant"]]
