# Canary eval: `dependency-audit` on every host

`dependency-audit` is the simple canary of the universal marketplace: one skill, one entry, one
context, no fan-out and no semantic override. It is what proves the compiler produces one
installable package per host with one identity and one observable contract, before the review
pipeline is attempted.

## What is asserted mechanically

`tests/test_dependency_audit_ports.py` runs in the normal suite and asserts:

- every host reports `dependency-audit` at the same version as the kernel, from its plugin manifest where it has one and from `.daodan-provenance.json` on Pi, which has none
- all three packages carry the four skill resources byte-for-byte
- every host reaches the audit through `/daodan:check-health` (since marketplace 38.0.0 the
  plugin has no command of its own): the entry renders at its native path on all five hosts,
  and the lifecycle assess unit it loads names `dependency-audit:dependency-audit` when
  manifests exist
- the audit method, `skills/dependency-audit/references/audit.md`, states each audit contract
  outcome, its steps in order and the single report in the run directory
- no host needed a semantic override (`overrides: []` in every provenance file)

Rebuild and verify with:

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
python -m unittest discover -s tests -p "test_dependency_audit_ports.py" -v
```

## Contract results

The behavioural half requires installing the package from each disposable marketplace and running the
audit against a fixture project. That means driving real Claude Code, Copilot and Codex sessions,
which is the same manual step the host protocol probes need.

| host | package installs | workflow invocable | dependencies discovered | direct/transitive classified | licenses analyzed | supply-chain evidenced | report written | remediation non-destructive |
|---|---|---|---|---|---|---|---|---|
| claude | yes | yes | 5 | yes | yes | yes | yes | yes |
| copilot | recognized | not run | - | - | - | - | - | - |
| codex | yes | yes | 5 | yes | yes | yes | yes | yes |

Both measured hosts ran against `tests/fixtures/daodan/dependency-project`, a two-ecosystem fixture
(npm and pip) pinned to deliberately old versions and never installed, and both closed with

```text
CONTRACT: discovered=5 classified=yes licenses=yes supplychain=yes report=yes destructive=no
```

Claude ran the package with `--plugin-dir`; Codex installed it from the generated catalog
(`codex plugin marketplace add ./`, `codex plugin add dependency-audit@daodan`) and the disposable
registration was removed afterwards. Both honoured the plugin's own directives: evidence tiers on
every claim, coverage gaps stated rather than papered over, and no manifest or lockfile touched.

Copilot is recognized by `copilot plugin list --plugin-dir` but not run, for the token reason
recorded in `tests/host-probes/README.md`.

**Running this found a defect the design had specified wrongly.** The Codex catalog entry was
specified as `{"source": "local", "path": "./exports/codex/plugins/<name>"}`. Codex registers such a
marketplace and then reports every plugin in it as `not found`; it takes a repository-relative path
string in `source`, exactly like the other two hosts. `catalogs.py` now emits that, and the catalog
test pins it with the reason.
