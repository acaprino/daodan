---
name: platform-engineering
description: >
  Platform mechanisms and compatibility for browser, PWA, mobile, Electron and Tauri applications.
  TRIGGER WHEN: building or reviewing supported browsers/devices, native integration, offline lifecycle, packaging, or platform-specific trust boundaries.
---

# Platform engineering

Bind advice to the application's declared target platforms, versions, distribution
and required behavior. Read relevant source and effective configuration before
applying a rule. Historical reference examples, numeric budgets and preferred
technologies are leads; verify applicable version behavior and requirements before
treating them as obligations. Missing measurements remain unknown.

The autonomous `platform-reviewer` checks client platform compatibility and
mechanisms. It reports adjacent security, generic performance or backend
operability leads to the caller for routing through the existing review process.
It does not claim those separate dimensions were reviewed.

## Load references on demand

Choose only sections needed for the actual mechanism:

| Mechanism | References inside this skill |
|---|---|
| Browser/native identity and credential boundary | `auth-tokens.md`, `passkeys-webauthn.md`, `platform-security.md` |
| Browser execution and content boundaries | `xss-csp.md`, `server-validation.md`, `api-security.md`, `secrets-management.md` |
| Client/server and transport design | `client-server-architecture.md`, `api-design.md` |
| Offline synchronization and caches | `offline-first.md` |
| Platform delivery and configuration | `infrastructure.md`, `platform-security.md` |
| Platform-specific rendering, power and resource constraints | `frontend-performance.md`, `backend-and-platform-performance.md` |

References never grant execution or mutation. Audit is read-only and does not
run a profiling query, launch a device or exercise an application without the
caller's corresponding authorization. State verified target/version, mechanism,
requirement, counterevidence and coverage in findings; neither a checklist item
nor a preferred package establishes a defect.

For the targeted platform audit under `/daodan:check-health`, read
`references/audit.md`. Inside a senior-review run, use the prepared brief and
dispatch this plugin's reviewer once; do not start the standalone audit as well.
