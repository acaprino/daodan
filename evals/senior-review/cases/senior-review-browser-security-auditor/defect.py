"""The returned page is served as text/html to other users. Comment text is untrusted and must render as text. No CSP or upstream sanitization is supplied. This public comment page carries no ambient credentials and performs no mutation.
ambient_mutation: Browser cookies automatically authenticate transfer requests, including cross-origin POSTs. Trusted origin is https://app.example. The supplied same-origin token check is authoritative; account identity is server-derived.
credentialed_cors: Profile is authenticated by an ambient cookie; only https://app.example may read it cross-origin. These are the final edge response headers and no later policy is applied.
cookie_transport: Session cookie must be sent only over HTTPS. The application remains reachable at HTTP on the same host and no transport upgrade occurs before cookie transmission. HttpOnly and SameSite alone do not protect that hop."""

def page(comment):
    return '<html><body><p>' + comment + '</p></body></html>'


# Scenario ambient_mutation
def transfer(request, valid_token, apply):
    return apply(request['account'], request['amount'])


# Scenario credentialed_cors
def response_headers(origin):
    return {'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Credentials': 'true'}


# Scenario cookie_transport
def session_cookie(value):
    return 'session=' + value + '; HttpOnly; SameSite=Lax'
