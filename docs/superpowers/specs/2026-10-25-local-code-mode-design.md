# Local Code Mode for Codebase Map

## Intent and authority

The user requested an original replication of the Cloudflare Code Mode pattern
inside Daodan after discussing progressive discovery, executable composition and
keeping intermediate tool results outside the model context. Implement that local
capability, using the existing MCP operations and project boundaries. This record
states implementation choices; it does not claim the user selected a runtime or
approved publication to the shared branch.

## Approaches and decision

1. Depend on the Cloudflare SDK and Workers. This supplies a remote execution
   environment but does not directly serve Daodan's local Python operations. The
   SDK's documented Node import limitations add an integration dependency.
2. Add a general cross-plugin MCP gateway. This introduces provider discovery,
   startup configuration and cross-plugin ownership before a second consumer has
   been established.
3. Add an opt-in mode to the existing Codebase Map MCP server. This is the selected
   implementation choice: keep one operation owner, one server registration and
   one authoritative set of schemas. Separate the executor from map semantics so
   a later evidenced consumer can reuse the design without duplicating the map.

## Contract

- Native startup remains the default. `--code-mode` exposes exactly `search` and
  `execute` through the same server identity, instead of the native catalog.
- `search(code)` runs an async JavaScript function over `catalog`, an array of
  permitted MCP tool descriptors, without any operation capabilities. The complete
  catalog remains in the execution process unless selected by returned data.
- `execute(code, tools)` runs an async JavaScript function with a `tools` object.
  Each named function takes one argument object. The requested names must be in
  the server's permitted catalog. Calls use the existing MCP server's public
  `call_tool` API, retaining validation, error translation and publication gates.
- Only operations explicitly annotated read-only are permitted by default.
  `--code-mode-allow-write NAME` grants a specific registered mutation at startup.
  Unknown names, wildcards and grants for non-mutations are rejected. Generated
  code and tool arguments cannot grant authority. An executor with write grants
  is advertised as mutating. The outer call does not provide per-internal-call
  client approval; grants must reflect the host's intended authorization.
- Selected output is JSON. The result also contains broker-owned call receipts and
  size/timing counts. These counts measure bytes or characters, never billed
  tokens. A caught tool failure remains in the receipts. A failed execution
  reports completed operations, so a caller must not blindly replay mutations.
- MapService retains project/run/store confinement, freshness, source verification,
  locks, publication and event ownership. Code Mode starts no LLM or worker team.

## Runtime and limits

Use a separately installed Deno 2.4 or later, on a maintained patched release.
Python orchestration uses the standard library; the existing MCP SDK remains the
transport dependency. Deno is required only when Code Mode is selected. Resolve
its executable from absolute PATH entries or an explicit absolute `--deno` path;
never let a project-local executable or Deno configuration choose the runtime.

Launch a fixed shipped runner in a disposable directory with a clean environment,
all I/O permissions denied, no prompts, no configuration, no npm and no remote
imports. Execute generated code only in a blob Worker. Authenticate runner stdout
frames with a bootstrap token never delivered to the Worker. Treat every request
as untrusted and validate it in Python. Preserve actual broker receipts outside
the generated program's control.

Default limits: 32 KiB code, 30 seconds JavaScript lifetime, 32 internal calls,
128 MiB V8 old-space, 64 KiB selected final JSON value, 8 MiB per intermediate result, 32 MiB
cumulative intermediate results and 16 KiB stderr. Enforce bounded line reads,
unique request IDs, exact operation membership and JSON object arguments. Reject
oversized output explicitly rather than silently truncating evidence.
The selected-value limit excludes broker receipts and statistics; report their
serialized sizes separately so byte counts cannot imply whole-response savings.

On cancellation, protocol failure or deadline, stop new calls and terminate/reap
the Deno process. An already admitted atomic upstream call is allowed to finish
and is accounted for before the request returns. The JS deadline is not a hard
deadline for an existing atomic map operation. Deno permissions and a heap limit
are not complete OS isolation or a total memory/disk quota; do not advertise a
multi-tenant hostile-code service.

## Delivery and evidence

Ship the original executor and runner under map-method/scripts, indexed from the
owning skill. Document startup, required Deno installation, discovery examples,
write grants, result receipts, errors and limitations. Preserve the existing
host-specific MCP registration mechanisms and compile all five host packages.

Validate genuine discovery and composition over the real MCP transport, retained
argument/path/publication failures, forbidden capabilities, time/output/call
limits, cancellation and state separation. Exercise all generated packages as
files; keep those checks distinct from installed host execution. Compare native
and Code Mode interface/result sizes on the same fixture without claiming token
or task-quality savings from character counts.

## Provenance

Original implementation inspired by Cloudflare's Code Mode design:
https://blog.cloudflare.com/code-mode-mcp/ and
https://github.com/cloudflare/agents/tree/321814b6c13f72cff82161e7eb20312574ac9b7a/packages/codemode
(MIT). No upstream implementation or skill text is copied. Deno is a separately
installed MIT-licensed runtime, not vendored into the marketplace.
