# Native host protocol probes

One disposable single-plugin package per host, establishing what each native harness
actually supports. They exist so that the adapter capability and coordination bindings in
`adapters/<host>/` encode measured behaviour instead of assumptions. They are fixtures: nothing here
ships, and every disposable marketplace is removed from the host profile after the probe. Pi and
OpenCode are the exceptions to the word marketplace: neither has one, so their fixtures are packages
installed from a path and removed with `pi remove` and `opencode plugin remove`.

Each fixture packages the same probe plugin (`daodan-probe`, version `0.0.1`, source `./plugins/probe`):

- a **single-worker** skill whose entire output contract is `Return exactly DAODAN_PROBE_OK.`
- a **two-worker coordination** entry point that dispatches two workers with nonces `alpha` and `beta`,
  requires isolated worker contexts, asks for parallel execution when available, waits for both
  deliveries and returns `DELIVERED=2/2`.

Per-host specifics:

| host | coordination entry point | role delivery under test |
|---|---|---|
| claude | `commands/probe-team.md` | packaged agent, plus native Agent Teams versus plain isolated subagents |
| copilot | `agents/probe-coordinator.agent.md` | named custom agent, restricted by the `agents` frontmatter allowlist |
| codex | `skills/probe/SKILL.md` | packaged `.codex/agents/probe.toml` role, with inline role body as the fallback |
| pi | `prompts/daodan-probe-team.md` | role registered as a `disable-model-invocation` skill, dispatched with the `subagent` tool from `pi-subagents` |
| opencode | `commands/probe-team.md`, registered as `/probe:probe-team` | agent registered by the loader from `package.json`, dispatched with the native `subagent` tool |

## Structural check

```bash
python scripts/probe_host_marketplaces.py
python -m unittest discover -s tests -p "test_host_probe_fixtures.py" -v
```

## Native smoke probes

Run these in disposable host profiles, browse and install `daodan-probe`, start a fresh session, then
invoke the single-worker and two-worker probes:

```text
claude plugin validate tests/host-probes/claude
copilot plugin marketplace add ./tests/host-probes/copilot
codex plugin marketplace add ./tests/host-probes/codex
pi install ./tests/host-probes/pi
opencode plugin add "$PWD/tests/host-probes/opencode"
```

Pi is the one host with no marketplace to add: it installs a package from a path, so the fixture
root is what you hand it. The Pi probe answers three questions the others do not raise. Whether a
`subagent` tool exists at all, which needs `pi install npm:pi-subagents` first and decides whether
the `contexts.isolate` binding is honest. Whether `/skill:probe-worker` resolves even though the
skill declares `disable-model-invocation`, which is what makes a role reachable there. And whether
the manifest's directory globs pick up a nested skill, which the adapter assumes and nothing local
can prove.

OpenCode V2 is the second host with no marketplace, and the first whose components exist only
because a plugin's JavaScript registers them. Its fixture ships the real loader byte for byte, so the
probe measures the generated package rather than a stand-in. It answers five questions, each of
which a decision in `docs/superpowers/specs/2026-10-02-opencode-host-adapter-design.md` rests on:

1. Whether `opencode plugin add` installs a `github:<owner>/<repo>#<tag>::path:exports/opencode`
   spec and loads its `index.js`, on the CLI and in OpenCode Desktop.
2. Whether a skill with a colon in its ID (`probe:probe`) loads through the `skill` tool, and whether
   the `subagent` tool accepts an agent named `probe:probe-worker`. If either fails, that kind falls
   back to the hyphen form Pi uses.
3. Whether a registered skill appears only in the `@` mention menu and never in the `/` catalog.
4. Whether two `background: true` workers of one phase actually run concurrently.
5. Whether a git-backed spec installs on Windows, where superpowers documents failures under V1.

Expected single-worker result on every host: `DAODAN_PROBE_OK`.
Expected coordinator result: both unique worker nonces plus `DELIVERED=2/2`.

Remove each disposable marketplace after the probe.

## Evidence

```text
host | isolated workers | parallel fan-out | shared tasks | peer messaging | worker allowlist | packaged roles
```

| host | isolated workers | parallel fan-out | shared tasks | peer messaging | worker allowlist | packaged roles |
|---|---|---|---|---|---|---|
| claude | yes | yes | conditional | conditional | n/a | yes |
| copilot | partial | partial | partial | partial | partial | yes (structural) |
| codex | yes | yes | no | no | n/a | no (inline succeeded) |
| pi | unmeasured | unmeasured | no | no | n/a | unmeasured |
| opencode | unmeasured | unmeasured | no | no | n/a | unmeasured |

**Claude and Codex are measured; Copilot, Pi and OpenCode are not.** The Claude row comes from two headless runs
against the fixture package, loaded with `--plugin-dir` so nothing was registered in a real profile:

```bash
cd <scratch> && claude -p "Use the daodan-probe 'probe' skill and follow it exactly."   --plugin-dir tests/host-probes/claude/plugins/probe --permission-mode bypassPermissions
# -> DAODAN_PROBE_OK

cd <scratch> && claude -p "<two-worker coordination probe>"   --plugin-dir tests/host-probes/claude/plugins/probe --permission-mode bypassPermissions
# -> NONCE=alpha / NONCE=beta / DELIVERED=2/2 / ISOLATED=yes PARALLEL=yes
```

`shared tasks` and `peer messaging` read `conditional` because they belong to the native team layer,
which is off by default; the probe satisfied the contract without them, which is the point of the
`parallel-subagents` baseline. `packaged roles = yes`: the coordinator dispatched the packaged
`probe-worker` by name.

Two defects came out of running this rather than assuming it, both now fixed:

1. **`strict: false` alongside component arrays is rejected by the host.** The install failed with
   "conflicting manifests: both plugin.json and marketplace entry specify components". The fixtures now
   declare `strict: true`. The generated catalogs never carried the key, so they were unaffected.
2. **Generated `plugin.json` files had no `author`.** `claude plugin validate .` warned on all 40.
   The manifest templates now emit the marketplace owner, and validation is clean.

The Codex row comes from `codex plugin marketplace add ./tests/host-probes/codex`, `codex plugin add
daodan-probe@daodan-probe-codex`, then two `codex exec` runs; the disposable marketplace and plugin
were removed afterwards and `~/.codex/config.toml` was byte-identical to its pre-probe backup.

```text
# single worker -> DAODAN_PROBE_OK
# coordinator   -> NONCE=alpha / NONCE=beta / DELIVERED=2/2
#                  ROLE_DELIVERY=inline ISOLATED=yes PARALLEL=yes
```

`packaged roles = no` for Codex, and inline delivery succeeded, which is exactly the condition the
release baseline allows. It confirms `adapters/codex/coordination.toml`, which already declared
`role_delivery = "inline-prompt"`: the assumption was right, and is now evidence. Codex reads
`.agents/plugins/marketplace.json` and lists the plugin from it, so the generated Codex catalog shape
is confirmed too.

Copilot is measured **structurally but not behaviourally**, and the reason is authentication rather
than the plan. The CLI recognises every package the compiler produces:

```bash
for d in exports/copilot/plugins/*/; do
  copilot plugin list --plugin-dir "$PWD/$d"
done
# -> recognized=40 rejected=0
```

That is real evidence about the generated package shape: all 40 load as external plugins, so the
Copilot layout, manifest and component paths in `adapters/copilot/layout.toml` are confirmed.

What could not be run is the behavioural probe, because Copilot accepts only an OAuth token or a
fine-grained PAT, and the classic token `gh` holds is rejected. Obtaining one means an interactive
`/login` in the CLI, which is the one thing here that genuinely needs the account owner. Until then
the `partial` rows above stay partial and `adapters/copilot/coordination.toml` carries the spec's
documented assumptions: the worker allowlist in particular (`agents:` frontmatter actually restricting
dispatch) is asserted by no evidence yet.

One machine-level obstacle was cleared along the way and is worth recording, because it will recur:
the Copilot CLI extracts its platform package into `%LOCALAPPDATA%\copilot\pkg` on `C:`, that path is
not configurable, and with 253 MB free every launch died with `ENOSPC` before argument parsing.
`npm cache clean --force` freed 4.2 GB and the CLI started working.

Release baseline, applied when the table is filled in:

- `isolated workers = yes` is required for every host.
- `parallel fan-out`, `shared tasks` and `peer messaging` may be `conditional` or `no`.
- Copilot must report `worker allowlist = yes`.
- Codex may report `packaged roles = no` only when inline role delivery succeeds.
