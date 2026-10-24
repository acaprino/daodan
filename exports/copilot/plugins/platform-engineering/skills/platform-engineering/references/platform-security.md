<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# Platform-Specific Security

Review evidence governs these implementation recommendations: establish the supported version, effective configuration, trust boundary and required outcome before retaining a finding. Historical incidents and default/example settings are leads, not proof about the current target. Check current official documentation for version-dependent behavior; do not install or execute examples during review.

## Mobile Security

### MUST

- **Use iOS Keychain and Android Keystore** for all sensitive data storage.
- Enforce TLS 1.2+ via App Transport Security (iOS, enabled by default) and Network Security Config (Android).
- Implement **certificate pinning** for critical API endpoints using public key (SPKI) pins with backup pins and a documented rotation runbook.

### DO

- Implement root/jailbreak detection for high-security applications (banking, healthcare) using layered detection methods.
- Enable ProGuard/R8 obfuscation on Android.
- Implement biometric authentication via system APIs (LocalAuthentication on iOS, BiometricPrompt on Android) -- never store biometric data directly.
- Use `FLAG_SECURE` on Android to prevent screenshots of sensitive screens.
- Exclude sensitive data from device backups.

### DON'T

- Embed secrets in app binaries -- extractable via MobSF, Frida, and jadx.
- Use embedded WebViews for OAuth login.
- Rely solely on client-side jailbreak detection -- combine with server-side risk scoring.
- Reference: OWASP MASVS L1/L2 and the MAS Testing Guide.

## Desktop Security - Electron

### MUST

- **Set `nodeIntegration: false`, `contextIsolation: true`, and `sandbox: true`** in all renderer processes. These are defaults in modern Electron but must be verified. Without contextIsolation, web page scripts can access Electron internals. Without sandbox, renderer processes have broad OS access. Define a strict CSP.

### Incident History

- **CVE-2018-1000136:** `nodeIntegration` re-enabled via `<webview>` tags, affecting Atom, VS Code, Slack, Discord -- XSS became RCE on all affected apps.
- **CVE-2021-43908:** XSS in a VS Code webview chained with path traversal for full remote code execution.
- **2024 audit of 112 popular Electron apps:** found "overwhelmingly poor" security, with a majority enabling insecure features.
- **electron-updater signature bypass (CVE-2020-15174):** MITM attackers delivered unsigned malicious updates because signature verification had a "fail-open" condition.

### MUST

- **Code-sign your application** on all platforms (Windows Authenticode, macOS Developer ID + Notarization) and cryptographically verify auto-update signatures before installation.

### DO

- Use preload scripts with `contextBridge.exposeInMainWorld()` to create a controlled API surface.
- Validate all IPC messages in the main process as untrusted input.
- Keep Electron/Chromium updated -- bundled Chromium doesn't auto-update, so track security releases and treat them as ship-blocking.
- **Configure Electron Fuses** via `electron/fuses` or `@electron/fuses` CLI to disable at-build-time the dangerous features that attackers use to achieve RCE or supply-chain compromise. Fuses are flipped into the compiled Electron binary and cannot be re-enabled without re-shipping.

### Recommended Fuses configuration

```javascript
// forge.config.ts (Electron Forge) or scripts/flip-fuses.js
const { flipFuses, FuseVersion, FuseV1Options } = require('@electron/fuses');

await flipFuses(
  require('electron'), // path to electron binary
  {
    version: FuseVersion.V1,
    [FuseV1Options.RunAsNode]: false,                       // disable ELECTRON_RUN_AS_NODE
    [FuseV1Options.EnableCookieEncryption]: true,           // encrypt cookies on disk
    [FuseV1Options.EnableNodeOptionsEnvironmentVariable]: false,  // block NODE_OPTIONS injection
    [FuseV1Options.EnableNodeCliInspectArguments]: false,   // block --inspect flag
    [FuseV1Options.EnableEmbeddedAsarIntegrityValidation]: true,  // verify asar integrity on load
    [FuseV1Options.OnlyLoadAppFromAsar]: true,              // refuse to load from disk outside asar
    [FuseV1Options.LoadBrowserProcessSpecificV8Snapshot]: false,
    [FuseV1Options.GrantFileProtocolExtraPrivileges]: false,
  },
);
```

### asar Integrity

- **Enable `EnableEmbeddedAsarIntegrityValidation` + `OnlyLoadAppFromAsar` fuses.** They bind runtime archive verification to the packaged header hash and constrain app search paths; preserve the separate executable-signing and packaging trust assumptions.
- [Electron ASAR integrity](https://www.electronjs.org/docs/latest/tutorial/asar-integrity) documents macOS support from 16 and Windows support from 30. Verify the actual Electron/asar versions, platform and packaging hooks.
- Without asar integrity, an attacker with filesystem write access can swap `app.asar` with a malicious version (e.g., adding a keylogger) -- code signing on the installer does NOT prevent post-install tampering.
- electron-builder integration: set `"asarIntegrity": true` in `build` config; it calculates hashes at build time.

### DON'T

- Load remote content with `nodeIntegration` enabled.
- Use `shell.openExternal()` with unvalidated URLs.
- Expose broad IPC channels that call `child_process`, `fs`, or `require`.
- Ship with `webSecurity: false`.

## Desktop Security - Tauri

### MUST

- **Keep exposed commands minimal.** Verify the registered commands, permissions and window-scoped capability bindings for the installed Tauri version. A framework choice alone does not prove the application’s security.

### Tauri trust boundaries

Inspect frontend/build dependencies, native plugins, sidecars and unsafe/foreign code as applicable. No framework eliminates supply-chain or memory-safety risk; package size is not a security guarantee. See [Tauri security](https://v2.tauri.app/security/).

## PWA Security

### MUST

- **Use a supported secure context.** Production service workers require HTTPS; browsers also allow designated trustworthy local origins such as localhost. See [service-worker setup](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API/Using_Service_Workers).
- Limit service worker scope to the narrowest necessary path.
- Never cache sensitive data (auth tokens, PII) in the Cache API -- it persists and is accessible to any script on the origin.
  - TU Wien research: since the Cache API is accessible from the entire origin, malicious scripts can achieve persistent person-in-the-middle capabilities against cached content, bypassing security headers including CSP.

### DO

- Implement cache versioning and expiration.
- Use SRI for all third-party scripts.
- Validate data before caching to prevent cache poisoning.
- Verify worker updates preserve the required old/new controlled-client journeys; forced activation is not universally correct.

## Security Headers Matrix

| Header | SPA | PWA | Mobile | Electron | Tauri |
|--------|-----|-----|--------|----------|-------|
| **CSP** | Critical | Critical | WebViews only | Critical | Relevant |
| **HSTS** (`max-age=31536000; includeSubDomains; preload`) | Critical | Critical | Backend only | Backend only | Backend only |
| **X-Frame-Options** (`DENY`) | Critical | Critical | N/A | Important | N/A |
| **X-Content-Type-Options** (`nosniff`) | Important | Important | N/A | Important | N/A |
| **Referrer-Policy** (`strict-origin-when-cross-origin`) | Important | Important | N/A | Important | N/A |
| **Permissions-Policy** | Important | Important | N/A | Important | N/A |

## Official docs

- OWASP MASVS (mobile): https://mas.owasp.org/MASVS/
- OWASP MAS Testing Guide: https://mas.owasp.org/MASTG/
- iOS Keychain Services: https://developer.apple.com/documentation/security/keychain_services
- Android Keystore: https://developer.android.com/training/articles/keystore
- Android Network Security Config: https://developer.android.com/training/articles/security-config
- iOS App Transport Security: https://developer.apple.com/documentation/security/preventing_insecure_network_connections
- iOS LocalAuthentication (biometrics): https://developer.apple.com/documentation/localauthentication
- Android BiometricPrompt: https://developer.android.com/reference/androidx/biometric/BiometricPrompt
- Electron Security checklist: https://www.electronjs.org/docs/latest/tutorial/security
- Electron Fuses: https://www.electronjs.org/docs/latest/tutorial/fuses (`@electron/fuses`: https://github.com/electron/fuses)
- electron-builder asar integrity: https://www.electron.build/configuration/configuration#asarintegrity
- Tauri Security: https://v2.tauri.app/security/
- MDN HSTS: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security
- MDN Permissions-Policy: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy
- securityheaders.com (testing): https://securityheaders.com/
- TU Wien Cache API research (PWA persistent MITM): https://github.com/SBA-Research/cache-api-research
