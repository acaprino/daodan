# resolver-spike

Measures whether an optional type-checker or language-server engine recovers the
call references the Codebase Map's lexical resolver leaves unresolved, at what
cost and with what precision, per language. It is a measurement harness like
`../retrieval-benchmark/`, not an agent-scored case, and it reads a snapshot's
`manifest.sqlite` rather than running the map.

The decision this supports is recorded in §3.2.2 of
`docs/superpowers/specs/2026-10-19-graph-grounded-economy-routing-design.md`;
grading decisions still open are in `../OPEN_POINTS.md`.

## What "an edge" means here

The population is the snapshot's own `sem_references` rows of kind `call` that
the lexical resolver did not resolve, minus `unbound-name` (builtins the resolver
declines to model). For each sampled position the engine is asked for the
definition of the callee, and the answer is graded:

| Grade | Definition reached | Counted as a call edge |
|---|---|---|
| `edge-call` | Method, Constructor, Function | yes |
| `edge-instantiation` | Class | yes |
| `edge-variable-binding` | Variable, Constant, Field, Property, or a position inside a symbol that is not its name | no, a candidate, reported separately |
| `definition-is-type-not-callable` | Enum, Interface, Module, Namespace, Package | no |
| `external-definition` | outside the project | no |

A target is project code only when its file is in the snapshot inventory. The
Python script below predates that rule and keeps a documented defect; see its
docstring.

## Scripts

| Script | Role |
|---|---|
| `manifest_probe.py` | full-population distribution of unresolved call references by language, reason and file |
| `lexical_baseline.py` | share of call references the lexical resolver resolves on its own |
| `jedi_spike.py`, `lsp_spike.py` | stage 1, kept for provenance: they over-count, because a definition request at a receiver returns the receiver |
| `jedi_edges.py` | stage 2 for Python with Jedi, against the project's own virtual environments |
| `lsp_edges.py` | stage 2 for TypeScript, JavaScript, Java, Go and Rust through multilspy, with readiness waits, both document-symbol response shapes and the grading above |
| `handcheck.py` | renders sampled edges with source at both ends, for precision reading |
| `probe_audit.py` | measures how often the callee probe position was wrong |
| `summarize_results.py` | per-run summary with unweighted and reason-weighted extrapolation |
| `sql_parity_spike.py` | the first SQL grammar probe; superseded by `../grammar-parity/` |

Every script resolves the plugin's helper scripts relative to this checkout.

## Running

Engines are installed outside the repository and never into the project under
measurement. Copy a project into a scratch directory before running an engine
that builds (rust-analyzer writes a `target/` directory), and point the build
caches at scratch (`CARGO_HOME`, `CARGO_TARGET_DIR`, `GOPATH`, `GOMODCACHE`,
`GOCACHE`). JDTLS writes `~/.m2` and multilspy writes `~/.multilspy`; neither can
be redirected through multilspy, so declare both.

```
uv run --no-project --script manifest_probe.py --manifest <manifest.sqlite> --language python
uv run --no-project --script jedi_edges.py --manifest <manifest.sqlite> --project <root> \
    --environment <venv> [--environment <venv> ...] --out <result.json>
uv run --no-project --script lsp_edges.py --manifest <manifest.sqlite> --project <server workspace> \
    --language typescript --workspace-rel <manifest prefix> --server-binary <server> --out <result.json>
```

On Windows, multilspy launches the extensionless npm shim for the TypeScript
server and fails with WinError 193; pass `--server-binary` pointing at the
`.cmd` file. PowerShell drops an empty argument, so pass `--workspace-rel=` for
a workspace that is the snapshot root.

## What the campaign of 2026-10-22 found

Measured per language on the projects and public corpora named in the spec, with
every published edge grade hand-checked by reading source at both ends. The
numbers, the ten defects found and fixed in `lsp_edges.py` before it could
measure, and the configuration each engine needs (monorepo workspace selection
for tsserver, a readiness wait for JDTLS, the crate fetch for rust-analyzer,
`go mod download` for gopls) are summarised in the spec. Raw results are
machine-local and are not committed.
