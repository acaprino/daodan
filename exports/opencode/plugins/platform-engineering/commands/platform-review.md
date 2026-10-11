---
description: 'Audit a codebase against the platform-engineering rulebook. TRIGGER WHEN: the user asks for a platform-level review, cross-platform security audit, Electron or Tauri hardening check, or an SPA, PWA, mobile, or desktop compliance review. DO NOT TRIGGER WHEN: reviewing generic code quality with no platform dimension (use /senior-review:code-review).'
---

<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# platform-review

<!-- Generated by the Daodan compiler for opencode. Edit the kernel, never this file. -->

## Execution harness

Selected topology: **parallel-subagents**, with role delivery by **named-agent**, and declared
isolation **required**.

Dispatch one worker per entry in the plan below with the `subagent` tool. Name the role as the
agent, using the qualified identity in the bindings below, and give it a short `description` and the full
task as `prompt`. Each agent runs in a fresh child session, so isolation is native here.
For a local role the qualified form is `agent: "platform-engineering:<role>"`; external roles
use their owner's prefix from the bindings, never the coordinator's prefix.

Under `parallel-subagents`, dispatch every worker of one phase with `background: true`, then wait
for every completion notice before the phase closes; do not poll. Under `serial-isolated`, dispatch
them one at a time in the foreground.

Every role below is registered as an agent by this package. A `subagent` call that answers with an
unknown agent means the install is broken: stop and report it, never continue with a shorter
report.

Coordinator completion ownership: keep the method's owned run and delivery ledger,
including each expected worker, attempt, report path and required check evidence.
Validate report artifacts before recording delivered. An empty final message or
worker stop remains missing delivery: inspect or resume when permitted, otherwise
record failed with the uncovered scope. Follow the declared join and phase gates;
a recorded failure is accounted for, never converted into a successful delivery.
Continue authorized work and recovery until the requested result and its checks
exist or a concrete blocker is recorded. Preserve the exclusive final report owner
and the ledger schema; a tool exit or a promise cannot satisfy completion.

Harness obligations, none of them optional:

- Every dispatched worker runs in its own context and reads only coordinator-declared inputs.
  Independent reviewers never read peer results before their own delivery.
- Follow the dispatch plan below in phase order. A phase starts only after every phase it needs has
  closed, and a phase closes only when every worker it dispatched is recorded `delivered` or
  `failed`. A worker reports delivered or failed in its final message; there is no shared task
  list, so the coordinator keeps that record itself.
- Dispatch only roles from this set, as the phase graph or loaded method requires: `platform-reviewer`
- Workers may write only intermediate reports explicitly assigned by the coordinator.
  The final report artifact has one exclusive owner in its declaring phase.

Dispatch plan:

1. `scope`: runs in the orchestrating context; produces `artifact:scope`.
2. `review`: one `platform-reviewer` in an isolated context; needs `scope`; consumes `artifact:scope`; produces `artifact:platform-review-report`.

Role bindings:

- `platform-reviewer`: dispatch the installed `platform-engineering:platform-reviewer` agent by its qualified identity.

The phase graph and the record schemas are in `contracts/platform-review.workflow.toml`.

## Method

# Platform Engineering Review

Standalone invocation of the `platform-reviewer` agent. Previously only reachable via `/senior-review:code-review` (Agent D). This command surfaces it directly for targeted cross-platform audits.

## CRITICAL RULES

1. **Detect platform first**. Scan `package.json`, `Cargo.toml`, `manifest.json`, `tauri.conf.json`, build configs to identify the platform mix. If `--platform auto` is set (default), report the detected platforms before reviewing.
2. **Run in parallel when multiple platforms are present**. A single repo may ship SPA + mobile + Tauri; load all applicable rulebooks.
3. **Write output to `.platform-review/REPORT.md`** for persistence.
4. **Never auto-fix**. Report findings; user decides what to apply.

## Procedure

### 1. Scope detection

Parse `$ARGUMENTS`:
- target path (default: current directory)
- `--platform`: force a specific platform or let auto-detect handle it
- `--focus`: restrict to `security` | `arch` | `perf` (default: all three)

Detect platforms:
- SPA: React/Vue/Svelte + no service worker
- PWA: `manifest.webmanifest` + service worker registered
- Mobile: Expo / React Native, Capacitor, NativeScript, Flutter
- Electron: `electron` in `package.json`
- Tauri: `@tauri-apps/api` + `src-tauri/`

### 2. Spawn the agent

Invoke `platform-engineering:platform-reviewer` with the target, detected platforms, and focus flag. The agent loads the relevant references from `skills/platform-engineering/references/`:

- Security: `server-validation.md`, `auth-tokens.md`, `passkeys-webauthn.md`, `api-security.md`, `xss-csp.md`, `secrets-management.md`, `platform-security.md`
- Architecture: `client-server-architecture.md`, `api-design.md`, `offline-first.md`, `infrastructure.md`
- Performance: `frontend-performance.md`, `backend-and-platform-performance.md`

For Electron / Tauri specifically, the agent also loads platform-security.md for the hardening checklist (fuses, asar integrity, capabilities, allowlists).

### 3. Output report

`.platform-review/REPORT.md`:

```markdown
# Platform Review: <target> (<date>)

## Detected platforms
- SPA | PWA | Mobile | Electron | Tauri

## Summary
- Critical issues: N
- High: N
- Medium: N

## Findings

### [CRITICAL]
- <file:line> <issue>. Rule: <rule violated>. Fix: <fix>

### [HIGH]
- ...

### [MEDIUM]
- ...

## Hardening checklist (Electron / Tauri if applicable)
- [ ] fuses.yml configured with hardened defaults
- [ ] asar-integrity enabled for signed releases
- [ ] Capabilities scoped per window (Tauri)
- [ ] CSP includes 'strict-dynamic' + nonces
- [ ] Auto-updater signature verification

## Auth posture
- [ ] No JWT in localStorage (SPA/PWA)
- [ ] Refresh tokens in httpOnly + Secure + SameSite=Strict cookies
- [ ] PKCE for OAuth on SPA/Mobile/Desktop
- [ ] Platform-native secure storage for mobile/desktop tokens
- [ ] WebAuthn / passkeys implemented for new auth flows (recommended for 2025+)

## Recommendations ordered by impact
1. ...
```

## Synergies

- Deeper per-dimension code review -> `/senior-review:code-review`
- Tauri-specific hardening -> `tauri-development:tauri-desktop` agent
- React performance inside a platform context -> `/react-development:review-react`
- Security-specific audit only -> `senior-review:security-auditor` agent
