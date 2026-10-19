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
