# resolver-spike

Measures whether an optional type-checker or language-server engine recovers the
call references the Codebase Map's lexical resolver leaves unresolved, at what
cost and with what precision, per language. It is a measurement harness like
`../context-scope/`, not an agent-scored case, and it reads a snapshot's
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

A production resolver must count a target as project code only when its file is
in the snapshot inventory. The Python script below predates that rule and keeps
a documented defect; see its docstring. The LSP script uses workspace containment
and external-path markers. Publication checked all its sampled edge-grade target
files against the original inventories; see [RESULTS.md](RESULTS.md).

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

The retained per-language outcomes are published in [RESULTS.md](RESULTS.md),
with sample denominators, reason weighting, engine costs, raw-artifact hashes and
the source-audit boundary. Confirmed TypeScript counts survived dependency
stripping in the measured samples; all three TypeScript monorepo-root runs
failed readiness and supply no recovery rate. JavaScript has only small
config/build populations and raw grade counts, with no recorded source audit.
Rust and Go retain the open grading decisions in `../OPEN_POINTS.md`.

The spec records the ten defects found and fixed in `lsp_edges.py` before it
could measure. The results distinguish completed configuration comparisons from
stale pending passages in the original notebook. Raw results remain machine-local
under the exact bench root recorded there and are not committed.

## What shipped from it (2026-10-22)

Python's part became product code in
[`resolve_edges.py`](../../../plugins/codebase-map/skills/map-method/scripts/resolve_edges.py),
and three things this harness measured are load-bearing in it rather than
restated:

- **The environment model.** `create_environment(path, safe=False)` per
  environment, `added_sys_path` over site-packages as the fallback when that
  fails, and `project-only` without a usable offered environment. Selection now
  prefers populated environments over installer-only stubs, then serving scope;
  each file reports its selected environment, interpreter, package count and mode.
  The 31.6% versus 25.2% remains the original campaign's environment comparison,
  not a new measurement of that selection policy.
- **The grading rule.** An engine's answer counts as an edge only when it lands on
  a declaration the snapshot holds, the target file is in the inventory, and the
  name is not ambiguous there. `in_project` by path containment, the documented
  defect of `jedi_edges.py` that made the published gap three times its real size,
  is not carried over: the shipped rule tests inventory membership.
- **The callee position.** The probe lands on the callee name inside the recorded
  span, never on the receiver, and a span that does not contain the callee name is
  skipped as unverified instead of probed at a guess.

The earlier smoke pass used jedi 0.20.1 on this plugin's own 39 Python files: 5,915 unresolved
call references in the inventory, 200 selected, 158 engine requests in `create_environment`
mode, 2 confirmed edges read true at both ends, 141 external definitions (the tree
is stdlib-only), mean 212 ms and p95 533 ms per inference. The `fast_parser`
pitfall recorded above is left alone in the shipped engine, and jedi 0.20's rename
of `Script(source=)` to `Script(code=)` is why the readiness probe constructs the
script positionally.

The continuation separates selected references from actual engine requests,
checks all source hashes before and after inference, and requires an exact
declaration name position for confirmation. Those changes and their verification
are recorded in the [Python delivery report](../../../docs/superpowers/reports/2026-10-22-codebase-map-python-resolver-delivery.md).

What did not ship: every LSP engine (tsserver, JDTLS, rust-analyzer, gopls) stays
in this harness, and OP-1/OP-2 in
[`OPEN_POINTS.md`](../OPEN_POINTS.md) stay open.
