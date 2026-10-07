# Historical catalog parity and host probes

This record describes the universal migration through marketplace 29.0.0, with 40 kernels. Its table and installed-host observations are historical evidence, not assertions about the current harness. Marketplace 30.0.0 validation is recorded in [the harness validation report](../../docs/superpowers/reports/2026-10-07-daodan-harness-validation.md). Current kernel/catalog parity is enforced by `tests/test_universal_catalog_parity.py` against the actual manifest set.

## Historical compiler parity

Produced by `python scripts/daodan_build.py --check --support`. `native` means the host binds every
required capability directly; `adapted` means at least one is satisfied through a host mechanism the
adapter names. No plugin is `unsupported` on any host, which is the release gate.

| plugin | version | claude | copilot | codex | pi | opencode |
|---|---|---|---|---|---|---|
| `abstraction-architect` | 4.0.0 | native | native | adapted | adapted | native |
| `ai-tooling` | 5.4.2 | native | native | adapted | adapted | native |
| `app-analyzer` | 1.4.2 | native | native | adapted | adapted | native |
| `browser-extensions` | 2.0.0 | native | native | adapted | adapted | native |
| `business` | 1.12.0 | native | native | adapted | adapted | native |
| `clean-code` | 1.3.2 | native | native | adapted | adapted | native |
| `codebase-mapper` | 3.1.1 | native | native | adapted | adapted | native |
| `codebase-xray` | 4.2.1 | native | native | adapted | adapted | native |
| `csp` | 1.4.0 | native | native | adapted | adapted | native |
| `dependency-audit` | 1.1.0 | native | native | native | native | native |
| `digital-marketing` | 3.0.0 | native | native | adapted | adapted | native |
| `docker` | 1.4.0 | native | native | native | native | native |
| `docs` | 1.2.1 | native | native | native | native | native |
| `frontend-review` | 2.1.2 | native | native | native | native | native |
| `grabber-development` | 1.8.2 | native | native | adapted | adapted | native |
| `kotlin-development` | 1.1.0 | native | native | native | native | native |
| `learning` | 1.7.1 | native | native | native | native | native |
| `libgdx-development` | 1.1.0 | native | native | adapted | adapted | native |
| `marketplace-ops` | 2.3.1 | native | native | adapted | adapted | native |
| `messaging` | 2.1.0 | native | native | adapted | adapted | native |
| `obsidian-development` | 1.5.1 | native | native | native | native | native |
| `opentelemetry` | 1.4.1 | native | native | adapted | adapted | native |
| `peer-review` | 2.4.1 | native | adapted | adapted | adapted | adapted |
| `platform-engineering` | 1.3.1 | native | native | adapted | adapted | native |
| `project-setup` | 2.0.1 | native | native | adapted | adapted | native |
| `pwa-expert` | 1.3.3 | native | native | adapted | adapted | native |
| `python-development` | 2.0.0 | native | native | adapted | adapted | native |
| `rag-development` | 1.6.0 | native | native | adapted | adapted | native |
| `react-development` | 1.11.0 | native | native | adapted | adapted | native |
| `repo-hygiene` | 1.2.0 | native | native | adapted | adapted | native |
| `research` | 6.2.3 | native | native | adapted | adapted | native |
| `senior-review` | 12.0.3 | native | native | adapted | adapted | native |
| `stripe` | 2.6.0 | native | native | adapted | adapted | native |
| `system-utils` | 2.1.1 | native | native | native | native | native |
| `tauri-development` | 2.8.0 | native | native | adapted | adapted | native |
| `testing` | 2.3.0 | native | native | adapted | adapted | native |
| `text-humanizer` | 1.2.0 | native | native | adapted | adapted | native |
| `trading-broker-integration` | 2.1.2 | native | native | adapted | adapted | native |
| `typescript-development` | 2.3.0 | native | native | adapted | adapted | native |
| `xterm` | 1.2.0 | native | native | native | native | native |

Codex and Pi both read `adapted` for 31 plugins, for the same reason: their context isolation, role
delivery and parallel dispatch are runtime-subagent mechanisms rather than packaged primitives. On Pi
that mechanism is a companion package the user installs, `pi-subagents`, which is why its coordination
strategies are marked `runtime-optional`. It is a binding difference, not a capability gap: the
contract assertions in `tests/test_review_pipeline_ports.py` and
`tests/test_dependency_audit_ports.py` hold identically on every host.

OpenCode reads `native` for 39 plugins and `adapted` for `peer-review` alone. V2 runs a registered
agent with `mode: subagent` in a fresh child session through its built-in `subagent` tool, so
isolation, named roles and background dispatch are all host primitives there. `peer-review` is the
exception because its MCP server is registered by the package's loader rather than read by the host
from a file, which is what `adapted` records.

## Gates that must stay green

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
python -m unittest discover -s tests
python scripts/lint_dependency_graph.py
python scripts/lint_bundled_paths.py
python scripts/lint_plugin_registration.py
python scripts/lint_fact_anchors.py
```

Result at the completed migration: 40 kernels and 40 packages per host, across Claude, Copilot, Codex
(since marketplace 28.0.0) Pi and (since marketplace 29.0.0) OpenCode, zero unsupported required components, zero stale overrides, and in fact zero overrides at
all. Every host divergence so far was expressible through the generic harness templates, which is the
outcome the override gate exists to make visible rather than to encourage.

## Host smoke results

| host | catalog adds | plugin installs | workflow invocable | skill loads | role dispatch |
|---|---|---|---|---|---|
| claude | yes | yes | yes | yes | yes (isolated, parallel) |
| copilot | not run | structural: 40/40 recognized | not run | not run | not run |
| codex | yes | yes | yes | yes | yes (isolated, parallel, inline delivery) |
| pi | n/a: no marketplace, installs a package | not run | not run | not run | not run |
| opencode | n/a: no marketplace, installs a plugin package | not run | not run | not run | not run |

Claude and Codex are measured end to end; Copilot, Pi and OpenCode are not. See `tests/host-probes/README.md`
for the commands and the raw results. `claude plugin marketplace add ./` then `claude plugin install clean-code@daodan`
installs and enables; `codex plugin marketplace add` lists the plugin from the generated
`.agents/plugins/marketplace.json` and `codex plugin add` installs it. `claude plugin validate .`
passes with zero warnings.

Copilot is measured structurally only: all 40 generated packages are recognized by
`copilot plugin list --plugin-dir`, but the behavioural half needs an OAuth token or a fine-grained
PAT that the classic `gh` token cannot stand in for.

## Release evidence

- Repository renamed to `acaprino/daodan`; the old name redirects.
- Marketplace identity `daodan` at version 26.0.0, 40 plugins, identical across all three catalogs.
- `consistency` and `publish-marketplaces` both green on the cutover head, and the publication job
  reported no drift, so the bot loop converged instead of republishing.

Three defects were found by running the hosts and CI rather than by reasoning about them, all fixed:

1. `strict: false` beside component arrays makes a plugin fail to load ("conflicting manifests").
2. Generated `plugin.json` files carried no `author`, which `claude plugin validate .` warned about
   40 times.
3. The kernel digest hashed absolute paths and raw bytes, so the same source hashed differently on a
   Windows checkout and a Linux runner, and CI reported drift against an identical tree. Deciding
   text by file extension then left four plugins still drifting, because the helper scripts they ship
   fell outside the whitelist. The renderer now asks the content whether it is text.
