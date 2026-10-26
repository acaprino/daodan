<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# Desktop Build & Deployment

Bundling, code signing, notarization, and the auto-updater. Most surface lives in v2.tauri.app; this file is the gotchas + the updater pubkey/endpoint shape + the GitHub releases convention.

## When to use

Producing distributable installers (.msi/.nsis on Windows, .dmg/.app on macOS, .AppImage/.deb/.rpm on Linux) and wiring the Tauri auto-updater. For mobile builds, see `build-deploy-mobile.md`.

## Format matrix

| Platform | Format | Toolchain |
|----------|--------|-----------|
| Windows | `.msi` (WiX) / `.nsis` | WiX Toolset 3.x / NSIS |
| macOS | `.dmg`, `.app` | Xcode CLT |
| Linux | `.AppImage` / `.deb` / `.rpm` | various |

Build commands:
- `cargo tauri build` (default release)
- `cargo tauri build --target x86_64-pc-windows-msvc`
- `cargo tauri build --bundles nsis` (specific format)
- `cargo tauri build --target universal-apple-darwin` (macOS universal)

## Gotchas

- **NSIS `installMode` choice matters**: `currentUser` (no admin, AppData), `perMachine` (admin, Program Files), or `both` (user picks). Default is fine; pick `currentUser` for consumer apps to skip UAC.
- **macOS notarization needs `APPLE_ID`, `APPLE_PASSWORD` (app-specific!), and `APPLE_TEAM_ID`** as env vars. Tauri runs notarization automatically during `cargo tauri build` when these are set. Without notarization, Gatekeeper blocks the app on first run.
- **Universal binary** (`--target universal-apple-darwin`) builds both Intel and Apple Silicon, but doubles build time. Most projects ship two separate `.dmg` files instead.
- **Linux `.deb` / `.rpm` MUST declare `libwebkit2gtk-4.1-0` (or `webkit2gtk4.1`) as a dep** -- otherwise the package installs but the app refuses to launch with a missing-library error.
- **AppImage `chmod +x` after download.** Linux distros don't auto-mark downloads as executable.
- **WiX Toolset 3.x must be on PATH** -- WiX 4 is NOT supported by Tauri yet (as of early 2026).
- **Updater pubkey embedded in the binary**: change it = ALL existing installations stop accepting updates from this release forward. Generate once with `cargo tauri signer generate -w ~/.tauri/myapp.key` and store the public key in `tauri.conf.json` permanently.
- **Updater requires `bundle.createUpdaterArtifacts: "v2Compatible"`** in `tauri.conf.json`, otherwise no `.sig` files are produced and the updater silently never finds an update.
- **Updater endpoint URL placeholders**: `{{target}}` (`windows-x86_64`, `darwin-aarch64`, etc.), `{{arch}}`, `{{current_version}}` -- the server must respond with the JSON shape below.

## Cargo.toml release profile (mirror in CI/`ci-cd.md`)

```toml
[profile.release]
codegen-units = 1
lto = true
opt-level = 3
strip = true
panic = "abort"
```

For size-optimized builds (mobile/embedded), use `opt-level = "s"` instead.

## Auto-updater (the parts worth keeping local)

### Setup
```bash
npm run tauri add updater
cargo tauri signer generate -w ~/.tauri/myapp.key
```

### `tauri.conf.json`
```json
{
  "bundle": { "createUpdaterArtifacts": "v2Compatible" },
  "plugins": {
    "updater": {
      "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ...",
      "endpoints": [
        "https://releases.myapp.com/{{target}}/{{arch}}/{{current_version}}"
      ]
    }
  }
}
```

### Update server response shape (the canonical JSON you must serve)

```json
{
  "version": "1.1.0",
  "notes": "Bug fixes and improvements",
  "pub_date": "2025-01-15T12:00:00Z",
  "platforms": {
    "windows-x86_64":  { "signature": "...", "url": "https://.../MyApp_1.1.0_x64-setup.nsis.zip" },
    "darwin-x86_64":   { "signature": "...", "url": "https://.../MyApp_1.1.0_x64.app.tar.gz" },
    "darwin-aarch64":  { "signature": "...", "url": "https://.../MyApp_1.1.0_aarch64.app.tar.gz" },
    "linux-x86_64":    { "signature": "...", "url": "https://.../MyApp_1.1.0_amd64.AppImage.tar.gz" }
  }
}
```

`signature` is produced by `cargo tauri build` alongside each artifact (the `.sig` file). Embed it as a string.

### Capabilities
```json
"permissions": ["updater:default", "process:allow-restart"]
```

### GitHub Releases as the update server (the zero-infrastructure path)

Use `tauri-action` to publish releases with update artifacts:

```yaml
- uses: tauri-apps/tauri-action@v0
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
    TAURI_SIGNING_PRIVATE_KEY_PASSWORD: ${{ secrets.TAURI_SIGNING_KEY_PASSWORD }}
  with:
    tagName: v__VERSION__
    releaseName: 'v__VERSION__'
    releaseDraft: true
```

Endpoint URL convention for GitHub releases:
```
https://github.com/OWNER/REPO/releases/latest/download/latest.json
```

`tauri-action` writes a `latest.json` file in the release with the correct shape -- no extra server code needed.

## Bundle resources

```json
{ "bundle": { "resources": ["assets/**/*", "config/default.toml", "models/model.onnx"] } }
```

Access at runtime:
```rust
use tauri::Manager;
let path = app.path().resource_dir()?.join("assets/data.json");
```

## Code signing one-liners

### Windows (signtool)
```bash
signtool sign /sha1 THUMBPRINT /fd sha256 \
  /tr http://timestamp.digicert.com /td sha256 \
  target/release/bundle/nsis/MyApp_1.0.0_x64-setup.exe
```

### macOS (env-driven, Tauri auto-runs)
```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
export APPLE_ID="your@email.com"
export APPLE_PASSWORD="app-specific-password"      # NOT your Apple ID password
export APPLE_TEAM_ID="TEAM_ID"
cargo tauri build
```

## Common build failures

| Problem | Fix |
|---------|-----|
| WiX not found | Install WiX Toolset 3.x, add to PATH |
| NSIS not found | Install NSIS, add to PATH |
| macOS signing fails | Verify identity with `security find-identity -v` |
| Notarization fails | Check Apple ID + app-specific password + team ID |
| AppImage won't run | `chmod +x MyApp.AppImage`, check FUSE installed |
| Update signature mismatch | Regenerate; ensure `pubkey` in config matches the key used to sign |
| Resources not found | Use `app.path().resource_dir()`; verify `bundle.resources` paths |
| Large bundle | Enable LTO, `strip = true`, audit `bundle.resources` |

## Official docs

- Distribution overview: https://v2.tauri.app/distribute/
- Per-platform signing: https://v2.tauri.app/distribute/sign/ (Windows, macOS, Linux)
- macOS notarization: https://v2.tauri.app/distribute/sign/macos/#notarization
- WiX MSI: https://v2.tauri.app/distribute/windows-installer/#wix
- NSIS: https://v2.tauri.app/distribute/windows-installer/#nsis
- AppImage / deb / rpm: https://v2.tauri.app/distribute/linux/
- Updater plugin: https://v2.tauri.app/plugin/updater/
- Updater key generation: https://v2.tauri.app/plugin/updater/#signing-updates
- `tauri-action`: https://github.com/tauri-apps/tauri-action

## Related

- `ci-cd.md` -- pipeline patterns, signing secrets as base64
- `build-deploy-mobile.md` -- Android/iOS builds and store submission
- `setup.md` -- toolchain prerequisites
- `rust-patterns.md` -- the release-profile recommendations
