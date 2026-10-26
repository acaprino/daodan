---
name: platform-engineering
description: >
  Rulebook of MUST/DO/DON'T rules backed by real-world incident references.
  TRIGGER WHEN: building or reviewing SPA, PWA, mobile (iOS/Android), or desktop (Electron/Tauri)
  apps for security posture, architecture decisions, performance, or compliance with OWASP, Core
  Web Vitals, and OAuth 2.1.
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

# Cross-Platform Development Rulebook

Three pillars govern every application you ship -- Security, Architecture, and Performance. Each rule is tagged with severity (MUST/DO/DON'T) and platform applicability.

## Quick Platform Decision Matrix

| Concern | SPA | PWA | Mobile | Electron | Tauri |
|---------|-----|-----|--------|----------|-------|
| **Auth token storage** | JS memory + httpOnly cookies | JS memory + httpOnly cookies | Platform Keychain/Keystore | OS credential store | OS credential store |
| **OAuth flow** | Auth Code + PKCE | Auth Code + PKCE | System browser + PKCE | Standard PKCE | Standard PKCE |
| **XSS impact** | Session hijack | + persistent SW hijack | WebView bridge access | XSS to RCE | Limited to web context |
| **CSP** | Critical | Critical | WebViews only | Critical | Relevant |
| **Offline strategy** | Optional | IndexedDB + Cache API + SW | Room/CoreData + sync queue | Optional | Optional |
| **Bundle target** | <170KB compressed JS | <170KB compressed JS | <20MB APK/IPA | 80-150MB (Chromium) | <10MB total |
| **API style** | REST or GraphQL | REST (SW caching) | GraphQL (fewer round-trips) | REST (server-side aggregation) | REST |
| **State management** | Zustand/Redux + TanStack Query | IndexedDB + Cache API | ViewModel+StateFlow / SwiftUI | IPC + context isolation | Rust invoke commands |

## When to Load References

- **Security review or audit**: Load `server-validation`, `auth-tokens`, `passkeys-webauthn`, `api-security`, `xss-csp`, `secrets-management`, `platform-security`
- **Architecture decisions**: Load `client-server-architecture`, `api-design`, `offline-first`, `infrastructure`
- **Performance optimization**: Load `frontend-performance`, `backend-and-platform-performance`
- **Full platform review**: Load all 13 references

## Reference Materials

### Security (Part 1)

1. **server-validation.md** -- Server-side validation rules, trust boundaries, real-world bypass incidents
2. **auth-tokens.md** -- Token storage per platform, OAuth 2.1 flows, JWT best practices, secure storage APIs
3. **passkeys-webauthn.md** -- WebAuthn Level 3 / passkey patterns, server-side verification, cross-platform support, cloned-authenticator detection
3. **api-security.md** -- Endpoint auth, rate limiting, CORS, OWASP API risks, Peloton/Parler case studies
4. **xss-csp.md** -- XSS severity by platform, CSP directives, anti-CSRF, sanitization, British Airways incident
5. **secrets-management.md** -- Secret exposure risks, environment variables, vault services, GitGuardian stats
6. **platform-security.md** -- Mobile (Keychain/Keystore, cert pinning), Electron (nodeIntegration, contextIsolation, sandbox), Tauri (deny-by-default), PWA (service worker scope, Cache API risks), security headers matrix

### Architecture (Part 2)

7. **client-server-architecture.md** -- Thin client principle, BFF pattern, server-authoritative design
8. **api-design.md** -- REST vs GraphQL trade-offs by platform, pagination strategies, state management per platform
9. **offline-first.md** -- Conflict resolution strategies (LWW, CRDTs, OT), optimistic UI, sync patterns
10. **infrastructure.md** -- Monolith-first principle, database access patterns, CI/CD pipelines per platform, observability, feature flag lifecycle

### Performance (Part 3)

11. **frontend-performance.md** -- Bundle size optimization, image formats and responsive loading, Core Web Vitals (LCP, INP, CLS) with business impact data
12. **backend-and-platform-performance.md** -- API/DB performance (pagination, indexing, connection pooling), mobile battery/memory, SSR/SSG/ISR rendering strategies, CDN caching patterns
