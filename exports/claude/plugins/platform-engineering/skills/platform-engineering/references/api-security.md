<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when a required one is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# API Endpoint Security

Every API endpoint your application exposes is discoverable. Assuming obscurity provides protection is a recipe for catastrophe.

## MUST

- **Authenticate and authorize every API endpoint.** Enforce server-side access control on every route. Never expose admin endpoints without VPN/IP restrictions and strong authentication layered on top.

- **Implement rate limiting** on all endpoints, especially authentication, search, data export, and password reset. Without rate limiting, attackers can brute-force credentials, scrape data at scale, or denial-of-service your backend.

- **Configure CORS restrictively.** Whitelist only specific, known origins. Never use `Access-Control-Allow-Origin: *` with credentials. On SPA/PWA, all API calls are visible in the browser's Network tab -- CORS is your primary line of defense against cross-origin abuse.

## Case Studies

- **Peloton (2021):** API was entirely unauthenticated, exposing user IDs, locations, workout statistics, age, and gender for all 3+ million subscribers -- including users with private profiles. When Peloton added authentication, they initially failed to add authorization, so any authenticated user could still access any other user's data (OWASP API1: Broken Object Level Authorization).

- **Parler (January 2021):** Complete data scrape because its API lacked rate limiting and used sequential post IDs that made enumeration trivial. Also failed to strip EXIF metadata from uploaded photos, exposing GPS coordinates for millions of users.

## DO

- Minimize data in API responses -- return only what the client needs, not everything the database provides (OWASP API3: Excessive Data Exposure).
- Use API gateways for centralized auth, rate limiting, and monitoring.
- Validate request payloads against a schema (OpenAPI/JSON Schema).
- Version your APIs and deprecate insecure older versions.

## DON'T

- Return verbose error messages exposing stack traces, database schemas, or internal paths.
- Expose GraphQL introspection in production.
- Rely on obscurity -- "nobody will find this endpoint" is not a security strategy.

## Official docs

- OWASP API Security Top 10 (2023): https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- OWASP API Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
- MDN CORS: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- OpenAPI Specification: https://www.openapis.org/
- JSON Schema validation: https://json-schema.org/
- Peloton incident writeup (Pen Test Partners): https://www.pentestpartners.com/security-blog/peloton-account-takeover/
- Parler scrape postmortem: https://en.wikipedia.org/wiki/Parler#Data_breach
