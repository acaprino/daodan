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

# CI/CD for Tauri Applications

Provider-agnostic notes on what makes a Tauri pipeline different from a generic Node app build.

## When to use

Designing or auditing a CI pipeline that produces Tauri installers/bundles. For mobile-specific CI (signing, store upload, 16KB page size), continue to `ci-cd-mobile.md`.

## OS matrix (cannot be flattened)

| Target | Runner OS | Notes |
|--------|-----------|-------|
| Windows (.msi/.nsis) | Windows | WebView2 bundled or bootstrapped at install |
| macOS (.dmg/.app) | macOS | codesign + notarization required for distribution |
| Linux (.AppImage/.deb) | Ubuntu | needs `libwebkit2gtk-4.1-dev` |
| Android (.apk/.aab) | Ubuntu | Android SDK + NDK; can build on Linux |
| iOS (.ipa) | macOS | Xcode required, no Linux/Windows alternative |

Always run platforms in parallel jobs -- a serial matrix wastes hours.

## Gotchas

- **Don't ship debug builds by accident.** Without an explicit release profile, binaries are 10-50x larger and noticeably slower. Set in `Cargo.toml`:
  ```toml
  [profile.release]
  lto = true
  opt-level = "s"      # "3" if you optimize for speed over size
  codegen-units = 1
  strip = true
  panic = "abort"
  ```
- **Cache `src-tauri/target/` aggressively.** Key on `Cargo.lock` hash + Rust toolchain version + OS. Cache size 500MB-2GB; Rust rebuilds without it take 20+ minutes.
- **Signing secrets as base64.** Store keystores, .p12, .p8 as base64-encoded CI secrets (`base64 -i file | tr -d '\n'`) and decode at build time to a temp path. Never commit credentials.
- **`tauri-apps/tauri-action`** is the path of least resistance on GitHub Actions for desktop builds (auto-uploads to a draft release). On other CIs you call `tauri build` directly and upload `src-tauri/target/release/bundle/*` yourself.
- **Updater signing key.** `TAURI_SIGNING_PRIVATE_KEY` + `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` are required if you ship the updater plugin -- builds without them succeed but produce unsigned `.json` manifests that the updater will refuse.

## Artifact paths cheat sheet

| Platform | Bundle output |
|----------|---------------|
| Windows / macOS / Linux | `src-tauri/target/release/bundle/` |
| Android | `src-tauri/gen/android/app/build/outputs/` |
| iOS | `src-tauri/gen/apple/build/` |

## Official docs

- Tauri CI/CD guide: https://v2.tauri.app/distribute/pipelines/
- `tauri-action`: https://github.com/tauri-apps/tauri-action
- Code signing per platform: https://v2.tauri.app/distribute/sign/
- Auto-updater + key generation: https://v2.tauri.app/plugin/updater/

## Related

- `ci-cd-mobile.md` -- Android keystore, App Store Connect API, store upload, 16KB page size
- `build-deploy-desktop.md` -- desktop signing/notarization details
- `build-deploy-mobile.md` -- Android/iOS bundle gotchas the CI inherits
