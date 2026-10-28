<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. Network search and network fetch
use the runtime's registered web search tool when the Codex configuration enables
it. A user question uses the runtime's registered question tool when one exists;
otherwise ask it in the reply and wait for the answer. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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
