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

# Platform Engineering Audit

Audit a codebase against the platform-engineering rulebook: a platform-level review, a cross-platform security audit, an Electron or Tauri hardening check, or an SPA, PWA, mobile, or desktop compliance review. Runs the `platform-reviewer` role on its own for targeted cross-platform audits. Shape: detect platforms, dispatch the plugin's reviewer in an isolated context, write the report.

Caller: `/daodan:check-health`, which runs this audit when the project ships an SPA, PWA, mobile, Electron or Tauri app. Inside `/daodan:review-changes` and `/daodan:review-branch`, senior-review dispatches `platform-engineering:platform-reviewer` with inputs it prepares, not through this procedure: never run both on the same target.

Not this audit: generic code quality with no platform dimension (use `/daodan:review-changes`).

## Inputs

- **TARGET**: what the caller passes.
  - The project, or nothing: the project root (formerly the current directory).
  - A path (file or directory): that path.
  - A diff (uncommitted changes, or a commit, range or branch the caller resolved): the reviewer's target is that diff; the role accepts a PR diff, file paths, a directory or a branch name.
  - Free text: read for the platform and focus signals below; the target stays the project root.
- **Platforms**: signal read from the target. Default: auto-detect (Step 1) and report the detected platforms before reviewing. When the caller's text names platforms (`spa`, `pwa`, `mobile`, `electron`, `tauri`), review those.
- **Focus**: method decision. Default: all three pillars. When the caller's text restricts the audit to `security`, `arch` (architecture) or `perf` (performance), review that pillar only.
- **Run directory**: the caller's run directory, written `<run>` below. The report goes to `<run>/platform-review/REPORT.md`.
- **Authorization**: none asked. The audit never edits the project (critical rule 4).

## CRITICAL RULES

1. **Detect platform first**. Scan `package.json`, `Cargo.toml`, `manifest.json`, `tauri.conf.json`, build configs to identify the platform mix. When platforms are auto-detected (the default), report the detected platforms before reviewing.
2. **Run in parallel when multiple platforms are present**. A single repo may ship SPA + mobile + Tauri; load all applicable rulebooks.
3. **Write output to `<run>/platform-review/REPORT.md`** for persistence.
4. **Never auto-fix**. Report findings; user decides what to apply.

## Procedure

### 1. Scope detection

Read the Inputs:
- target path (default: the project root)
- platforms: forced by the caller's text, or left to auto-detect
- focus: `security` | `arch` | `perf` (default: all three)

Detect platforms:
- SPA: React/Vue/Svelte + no service worker
- PWA: `manifest.webmanifest` + service worker registered
- Mobile: Expo / React Native, Capacitor, NativeScript, Flutter
- Electron: `electron` in `package.json`
- Tauri: `@tauri-apps/api` + `src-tauri/`

### 2. Dispatch the agent

Dispatch `platform-engineering:platform-reviewer` in its required isolated context through the host harness with the target, detected platforms, and focus. The agent loads the relevant references from `skills/platform-engineering/references/`:

- Security: `server-validation.md`, `auth-tokens.md`, `passkeys-webauthn.md`, `api-security.md`, `xss-csp.md`, `secrets-management.md`, `platform-security.md`
- Architecture: `client-server-architecture.md`, `api-design.md`, `offline-first.md`, `infrastructure.md`
- Performance: `frontend-performance.md`, `backend-and-platform-performance.md`

For Electron / Tauri specifically, the agent also loads platform-security.md for the hardening checklist (fuses, asar integrity, capabilities, allowlists).

### 3. Output report

`<run>/platform-review/REPORT.md`:

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

- Deeper per-dimension code review -> `/daodan:review-changes`, or `/daodan:review-branch` for a branch
- Tauri-specific hardening -> `tauri-development:tauri-desktop` agent
- React performance inside a platform context -> `/daodan:check-health`, which runs the React audit when the project has React
- Security-specific audit only -> `senior-review:security-auditor` agent
