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

# Server-Side Validation

The single most important security rule across every platform: **the client is untrusted territory**. Frontend validation exists only to improve UX. Every check (data type, length, range, format, business logic, authorization) must be enforced server-side. Attackers bypass client-side validation trivially using browser DevTools, intercepting proxies like Burp Suite, or direct API calls via curl.

## MUST

- **Validate all inputs server-side.** This includes prices, quantities, discount codes, user roles, and any value the client submits.
  - DeepStrike (2023): researchers found a payment system that stored invoice data in a JavaScript variable with frontend-only validation. By intercepting and modifying the price in transit, they submitted fraudulent payments -- the server accepted them without question.
  - In another case, researchers bypassed OTP verification by intercepting the API response and flipping "401 Unauthorized" to "200 OK" because the backend never re-verified the code server-side.

## DO

- Implement frontend validation for instant UX feedback (format hints, required-field indicators, character counters), but always duplicate every check on the backend.
- Validate at every trust boundary: client to API, service to service, and before database writes.

## DON'T

- Trust hidden HTML fields, disabled form elements, JavaScript variables, or client-computed values (totals, discounts, eligibility).
- Assume your API's only consumer is your own frontend -- any HTTP client can call your endpoints.

## Platform Context

| Platform | Bypass difficulty |
|----------|------------------|
| **SPA/PWA** | Code fully visible in browser DevTools -- bypass is trivial |
| **Native mobile** | Binaries decompiled with Frida, jadx, MobSF |
| **Electron** | Readable JavaScript in ASAR archives, extractable with a single command |
| **Tauri** | Compiled Rust backend does not protect against manipulated API requests over the network |
