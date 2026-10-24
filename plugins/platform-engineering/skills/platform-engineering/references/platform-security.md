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
