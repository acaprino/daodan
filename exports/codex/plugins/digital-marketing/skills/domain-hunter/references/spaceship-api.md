<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

<!-- upstream: ReScienceLab/opc-skills - skills/domain-hunter/references/spaceship-api.md -->
# Spaceship API Reference

Credentials are read from the environment:
- `SPACESHIP_API_KEY`
- `SPACESHIP_API_SECRET`

Base URL: `https://spaceship.dev/api`

## Authentication

All requests require these headers:
```bash
-H "X-Api-Key: $SPACESHIP_API_KEY"
-H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

Set both variables in the shell before any call.

POSIX shell:
```bash
export SPACESHIP_API_KEY="your_key"
export SPACESHIP_API_SECRET="your_secret"
```

PowerShell:
```powershell
$env:SPACESHIP_API_KEY = "your_key"
$env:SPACESHIP_API_SECRET = "your_secret"
```

**Pre-flight check.** Verify both are non-empty before the first call. An empty variable produces a 401 that reads like a permissions problem and sends you hunting the wrong bug.

```bash
if [ -z "$SPACESHIP_API_KEY" ] || [ -z "$SPACESHIP_API_SECRET" ]; then
  echo "ERROR: SPACESHIP_API_KEY and SPACESHIP_API_SECRET must both be set" >&2
  exit 1
fi
```

```powershell
if (-not $env:SPACESHIP_API_KEY -or -not $env:SPACESHIP_API_SECRET) {
  throw "SPACESHIP_API_KEY and SPACESHIP_API_SECRET must both be set"
}
```

## Domains API

### List Domains
```bash
curl -s -X GET "https://spaceship.dev/api/v1/domains?take=100&skip=0" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Check Domain Availability (Batch)
```bash
curl -s -X POST "https://spaceship.dev/api/v1/domains/available" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"domains": ["example.com", "test.ai"]}'
```
Response: `result` = "available" | "taken" | "reserved"

### Check Single Domain Availability
```bash
curl -s -X GET "https://spaceship.dev/api/v1/domains/{domain}/available" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Get Domain Info
```bash
curl -s -X GET "https://spaceship.dev/api/v1/domains/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Register Domain (Purchase)
```bash
curl -s -D - -X POST "https://spaceship.dev/api/v1/domains/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "autoRenew": true,
    "years": 1,
    "privacyProtection": {
      "level": "high",
      "userConsent": true
    },
    "contacts": {
      "registrant": "CONTACT_ID",
      "admin": "CONTACT_ID",
      "tech": "CONTACT_ID",
      "billing": "CONTACT_ID"
    }
  }'
```
**Note:** Returns 202 Accepted. The operation id comes back in the `spaceship-async-operationid` **response header**, so the request must keep headers (`-D -` or `-i`). A plain `curl -s` throws them away and leaves you with no way to poll.

Capture the id for the poll step:
```bash
OPERATION_ID=$(curl -s -D - -o /dev/null -X POST "https://spaceship.dev/api/v1/domains/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{...}' \
  | tr -d '\r' | awk 'tolower($1) == "spaceship-async-operationid:" {print $2}')
```

**WARNING:** Never retry a paid POST (register, renew, transfer) whose outcome you do not know. Poll the async operation first. A blind retry can double-charge the account.

### Update Nameservers (Configure to Cloudflare)
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/nameservers" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "custom",
    "hosts": ["ns1.cloudflare.com", "ns2.cloudflare.com"]
  }'
```

### Update Auto-Renewal
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/autorenew" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"isEnabled": true}'
```

### Renew Domain
```bash
curl -s -X POST "https://spaceship.dev/api/v1/domains/{domain}/renew" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"years": 1}'
```

### Update Privacy Protection
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/privacy" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "high",
    "userConsent": true
  }'
```
Levels: "high" | "medium" | "none"

### Update Domain Contacts
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/contacts" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "registrant": "CONTACT_ID",
    "admin": "CONTACT_ID",
    "tech": "CONTACT_ID",
    "billing": "CONTACT_ID"
  }'
```

### Get Auth Code (for Transfer Out)
```bash
curl -s -X GET "https://spaceship.dev/api/v1/domains/{domain}/auth-code" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Update Transfer Lock
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/domains/{domain}/transfer-lock" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"isEnabled": true}'
```

### Transfer In Domain
```bash
curl -s -D - -X POST "https://spaceship.dev/api/v1/domains/{domain}/transfer" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "authCode": "AUTH_CODE_FROM_CURRENT_REGISTRAR",
    "autoRenew": true,
    "privacyProtection": {
      "level": "high",
      "userConsent": true
    },
    "contacts": {
      "registrant": "CONTACT_ID",
      "admin": "CONTACT_ID",
      "tech": "CONTACT_ID",
      "billing": "CONTACT_ID"
    }
  }'
```
**Note:** Async and paid, same as registration. Keep the headers (`-D -` or `-i`) and read `spaceship-async-operationid` from them, then poll. Never re-POST a transfer whose outcome is unknown.

## Contacts API

### Save Contact
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/contacts/{contactId}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "organization": "Company Inc",
    "email": "john@example.com",
    "phone": "+1.5551234567",
    "address1": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "postalCode": "94102",
    "country": "US"
  }'
```

### Get Contact
```bash
curl -s -X GET "https://spaceship.dev/api/v1/contacts/{contactId}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

## DNS Records API

### Get DNS Records
```bash
curl -s -X GET "https://spaceship.dev/api/v1/dns-records/{domain}?take=100&skip=0" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```

### Save DNS Records
```bash
curl -s -X PUT "https://spaceship.dev/api/v1/dns-records/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "A", "name": "@", "address": "1.2.3.4", "ttl": 3600},
      {"type": "CNAME", "name": "www", "target": "example.com", "ttl": 3600},
      {"type": "TXT", "name": "@", "content": "v=spf1 ...", "ttl": 3600},
      {"type": "MX", "name": "@", "mailHost": "mail.example.com", "priority": 10, "ttl": 3600}
    ]
  }'
```

### Delete DNS Records
```bash
curl -s -X DELETE "https://spaceship.dev/api/v1/dns-records/{domain}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "A", "name": "@", "address": "1.2.3.4"}
    ]
  }'
```

## Async Operations

Domain registration, transfer, etc. are async operations, returning `spaceship-async-operationid` header. Send those requests with `-D -` or `-i`, otherwise curl discards the header and the operation becomes unpollable.

### Get Operation Status
```bash
curl -s -X GET "https://spaceship.dev/api/v1/async-operations/{operationId}" \
  -H "X-Api-Key: $SPACESHIP_API_KEY" \
  -H "X-Api-Secret: $SPACESHIP_API_SECRET"
```
Status: "pending" | "success" | "failed"

## API Permissions

| Scope | Description |
|-------|-------------|
| domains:read | Read domain information |
| domains:write | Manage domain settings |
| domains:transfer | Domain transfer in/out |
| domains:billing | Domain purchase and renewal |
| contacts:read | Read contacts |
| contacts:write | Save contacts |
| dnsrecords:read | Read DNS records |
| dnsrecords:write | Write DNS records |
| asyncoperations:read | Query async operations |

## Rate Limits

| Operation | Limit |
|-----------|-------|
| List domains | 300 req / 300s per user |
| Check availability (batch) | 30 req / 30s per user |
| Check availability (single) | 5 req / 300s per domain |
| Get domain info | 5 req / 300s per domain |
| Register domain | 30 req / 30s per user |
| Update nameservers | 5 req / 300s per domain |
| Async operations | 60 req / 300s per user |

## Common Workflows

### 1. Purchase Domain + Configure Cloudflare NS

```bash
# 1. Check availability
curl -s -X GET "https://spaceship.dev/api/v1/domains/example.com/available" ...

# 2. Get existing contact ID from another domain
curl -s -X GET "https://spaceship.dev/api/v1/domains?take=1&skip=0" ... | jq '.items[0].contacts.registrant'

# 3. Register domain, keeping the response headers so the operation id survives
OPERATION_ID=$(curl -s -D - -o /dev/null -X POST "https://spaceship.dev/api/v1/domains/example.com" ... -d '{...}' \
  | tr -d '\r' | awk 'tolower($1) == "spaceship-async-operationid:" {print $2}')

# 4. Poll for completion. Do NOT re-POST step 3 if this is unclear: that risks a double charge
curl -s -X GET "https://spaceship.dev/api/v1/async-operations/$OPERATION_ID" ...

# 5. Update nameservers to Cloudflare
curl -s -X PUT "https://spaceship.dev/api/v1/domains/example.com/nameservers" \
  ... -d '{"provider": "custom", "hosts": ["ns1.cloudflare.com", "ns2.cloudflare.com"]}'
```

### 2. Transfer Domain to Spaceship

```bash
# 1. Get auth code from current registrar
# 2. Unlock domain at current registrar
# 3. Initiate transfer, keeping the response headers so the operation id survives
OPERATION_ID=$(curl -s -D - -o /dev/null -X POST "https://spaceship.dev/api/v1/domains/example.com/transfer" ... \
  | tr -d '\r' | awk 'tolower($1) == "spaceship-async-operationid:" {print $2}')

# 4. Poll async operation for status. Never re-run step 3 to "check": poll instead
curl -s -X GET "https://spaceship.dev/api/v1/async-operations/$OPERATION_ID" ...
```
