"""Retrieved documents and model tool arguments are untrusted. Only the authenticated caller tenant may be read, even when the model provides valid JSON. records is an injected map keyed by tenant and record ID."""

def invoke(authenticated, arguments, records):
    return records[arguments['tenant']][arguments['id']]
