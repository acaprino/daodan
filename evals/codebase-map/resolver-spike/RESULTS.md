# Resolver engine measurement results

Campaign: 2026-10-22. Publication from the retained artifacts: 2026-10-22.
This ledger records the LSP measurements that remained unpublished in spec
§3.2.2. Python's measurement and its extraction prerequisite are recorded in
that section and in [python-parser/RESULTS.md](../python-parser/RESULTS.md).
These are static definition queries against snapshots, not runtime, test,
installed-host or integration evidence. No LSP engine is shipped by these results.

## Provenance and verification boundary

The original machine-local root is `C:\Users\alfio\daodan-bench\`, called
`<bench>` below. Raw JSONs, logs, source copies and audit material remain there;
they have not been copied into this repository or changed. The original
`clean/RESULTS.md` is a campaign notebook with unfinished passages and numbers
from several passes. The final JSON files and `clean/run-05-ts-js.final2.log`
settle the results below; notebook prose does not override them.

This publication recomputed verdict totals, shares and reason weighting directly
from the final JSONs with the checked-in `summarize_results.py`. It also opened
each original snapshot read-only and checked every edge-grade target in all
twelve successful LSP result files against the snapshot's `files` inventory:
none was outside it. That is a retrospective check, not a claim that
`lsp_edges.py` enforces inventory membership: that script uses workspace
containment and external-path markers. A production engine must enforce the
inventory rule itself.

Precision reading belongs to the earlier campaign: `clean/RESULTS.md` §9 records
the source-at-both-ends conclusions and names its audit files. This publication
does not repeat that independent source audit. Several audit renderings still
have verdict placeholders, and their generated coverage denominators can count
mandatory dynamic records twice. No blanket precision percentage or complete
record coverage is inferred from those renderings. The two exhaustive OP reads
have explicit verdict totals in `pyparser/op1-verified.txt` and
`pyparser/op2-verified.txt`.

## Method and denominator

The measurable population is unresolved snapshot `call` references, excluding
`unbound-name`. Every LSP run selects at most 25 files with the most such
references and their first 40 positions. Shares below divide engine `edge-call`
records by sampled positions; they are neither the lexical baseline nor the
fraction of all project calls recovered. Candidates are separate. The Go
`edge-instantiation` records are excluded because they are type conversions.

The sample is deterministic and favors dense files, tests and generated code.
Reason weighting applies each sampled reason's recovery rate to that reason's
full population; reasons absent from the sample contribute zero in
`summarize_results.py`. It does not correct file, declaration-form or generated-code
bias and is not a confidence interval. The unweighted rate is not necessarily
above the weighted one: Rust Jupiter rises under weighting.

## Published language measurements

`jd` means Jupiter `jupiter-desktop`; `lv` means Jupiter `logs-viewer-desktop`.
TypeScript rows use their package workspace with dependencies present.

| Language and workspace | Files / sampled positions | Measurable population | Lexical resolved / all calls | Confirmed `edge-call` | Sample share | Reason-weighted share | Candidates |
|---|---:|---:|---:|---:|---:|---:|---:|
| TypeScript, jd `src-react` | 25 / 1,000 | 10,057 | 1,608 / 12,641 | 60 | 6.00% | 5.52% | 96 |
| TypeScript, lv | 25 / 1,000 | 4,366 | 313 / 4,928 | 6 | 0.60% | 0.52% | 94 |
| TypeScript, Phazly `admin-app` | 25 / 1,000 | 3,855 | 1,572 / 5,829 | 20 | 2.00% | 1.87% | 297 |
| Rust, jd `src-tauri` | 25 / 949 | 2,610 | 197 / 3,170 | 204 | 21.50% | 22.44% | 1 |
| Rust, lv `src-tauri` | 21 / 424 | 951 | 58 / 1,218 | 38 | 8.96% | 8.21% | 0 |
| Go, `opentelemetry-go` | 25 / 1,000 | 117,019 | 3,475 / 157,024 | 466 | 46.60% | 45.52% | 199 |
| Java, `commons-lang` | 25 / 1,000 | 57,215 | 4,941 / 88,116 | 288 | 28.80% | 26.50% | 0 |

Rust lv includes all 21 files but only 424 of 951 positions: the per-file cap
excludes 527. The notebook and OP-1 call this a census; it is a census of files,
not of references. The 8.96% is a sampled-position result.

The TypeScript sample is dominated by tests and external test infrastructure.
Its candidates include project callable constants, interface members, mocks,
React setters and destructured callbacks, so their count cannot be added to
confirmed edges. The campaign report records no false confirmed `edge-call`
among its audited distinct claims (TS jd 14, lv 6, Phazly 12; Rust 16 per
workspace; Java 20; Go 15). That reported audit does not establish precision for
every record or candidate.

Go's sample includes 17 generated files among 25, and Java's includes 23 test
classes among 25. Go's 267 raw `edge-instantiation` records all target
`attribute/key.go:8`, `type Key string`: these are conversions and are excluded.
The Rust and Go rates exclude the additional verified records in OP-1 and OP-2;
they are lower bounds within these samples under the chosen grading rule.

### JavaScript: absolute raw grades only

| Workspace | Files / positions | `edge-call` | Candidates | External | Unresolved | Unknown definition kind |
|---|---:|---:|---:|---:|---:|---:|
| Jupiter root | 11 / 109 | 2 | 3 | 36 | 45 | 23 |
| Phazly root | 8 / 87 | 1 | 1 | 11 | 23 | 51 |

These cover each workspace's entire measurable JavaScript population, consisting
of config and build scripts. They do not support a general JavaScript recovery
claim. No source audit of the JavaScript edge grades is recorded, so even the
three raw `edge-call` records are not presented as independently verified edges.
The suspected vendored bundles do not occur in the population.

## Configuration comparisons completed after the notebook text

All three TypeScript monorepo-root runs failed the known-definition readiness
probe after 181 attempts and about 900 seconds each, including Phazly. Each
records `fatal: server never answered a known definition; no measurement taken`.
These are missing measurements with an explained readiness failure, never zero
recovery rates. The proposed Phazly root recovery of eleven cross-package `cn`
calls was not demonstrated. In the package run they remain `outside-workspace`.

The final stripped-dependency comparisons used the same sampled positions:

| TypeScript package | `edge-call`, deps / stripped | Candidates, deps / stripped | External, deps / stripped | Unresolved, deps / stripped | Unknown kind, deps / stripped |
|---|---:|---:|---:|---:|---:|
| Jupiter jd | 60 / 60 | 96 / 67 | 827 / 65 | 13 / 512 | 0 / 292 |
| Jupiter lv | 6 / 6 | 94 / 69 | 890 / 54 | 10 / 439 | 0 / 432 |
| Phazly admin | 20 / 20 | 297 / 297 | 671 / 186 | 1 / 115 | 0 / 371 |

Confirmed counts survived stripping `node_modules` in these three samples;
external attribution and two candidate counts changed. This does not establish
dependency independence for TypeScript generally.

## Engine identity and observed cost

The campaign used multilspy 0.1.1 on CPython 3.11.15. It records gopls v0.24.0
(Go 1.27.3), rust-analyzer's 2023-10-09 release (Rust 1.99.1, overriding the
projects' 1.98.0 pin), and Eclipse JDTLS from vscode-java 1.46.0 with bundled JRE
21.0.8. Its TypeScript/JavaScript server was `typescript-language-server` with
bundled tsserver; exact server/compiler versions are not recorded in the result
payloads, so those measurements do not supply a complete versioned resolver
fingerprint.

Times are from each retained primary JSON, rounded independently. Startup,
readiness and elapsed are the script's fields; elapsed is not a per-query sum.
Warm/cold conditions differ across passes, so the notebook's other timing tables
must not be mixed with these observations.

| Primary run | Startup s | Readiness s | Elapsed s | Mean / p95 ms |
|---|---:|---:|---:|---:|
| TS jd | 0.4 | 5.6 | 19.5 | 11.2 / 35.1 |
| TS lv | 0.2 | 3.6 | 21.5 | 15.5 / 46.9 |
| TS Phazly admin | 0.9 | 41.7 | 371.8 | 317.1 / 977.2 |
| Rust jd | 29.9 | 146.6 | 214.7 | 35.2 / 70.0 |
| Rust lv | 60.3 | 118.4 | 187.9 | 16.1 / 31.8 |
| Go | 0.3 | 17.3 | 423.0 | 379.9 / 2,175.3 |
| Java | 66.0 | 15.4 | 589.7 | 495.3 / 1,103.4 |
| JS Jupiter | 0.3 | 7.2 | 32.6 | 216.0 / 518.9 |
| JS Phazly | 0.2 | 19.6 | 44.5 | 257.9 / 24.5 |

The JS Phazly mean exceeding p95 is the retained observation, not a transposition.
JDTLS needs a real readiness query; Rust's crate import and Go's module downloads
are separate prerequisite costs. The campaign's original environment declaration
remains in `<bench>/clean/RESULTS.md` §11, including the nonredirectable `.m2`
and multilspy caches. This publication starts no engine and installs nothing.

## Decisions still open

[OPEN_POINTS.md](../OPEN_POINTS.md) owns the options and decisions:

- OP-1: all 17 Rust tuple-variant constructor records were read true at both
  ends, with zero false or undecidable. Promotion would change jd from 204/949
  (21.50%) to 221/949 (23.29%); the five derived-method `Struct` records remain
  excluded. Evidence is one workspace and one engine version.
- OP-2: all 174 Go interface-method candidate records were read true at both
  ends. Promotion would change 466/1,000 (46.60%) to 640/1,000 (64.00%). Of
  those 174, 152 occur in generated `semconv` files; 25 other candidates nested
  inside methods remain unexamined. Hierarchical gopls document symbols are an
  unmeasured alternative. Any promoted edge must distinguish a contract target
  from an implementation target.

No option is selected here. The LSP product integration, full resolver identity,
consumer wiring, and required per-language prerequisite work remain separate.

## Raw result identity

Paths in this table are relative to `<bench>/clean/`. Hashes identify the bytes
read for this publication; they do not make machine-local artifacts available
to another clone. Recompute summaries with `summarize_results.py --result PATH`
(repeat `--result` for additional JSONs). Exclude `*.pregrade.json` and earlier
logs from final-number inputs.

| File | SHA-256 |
|---|---|
| `lsp-ts-jupiter-jd-pkg-deps.json` | `469101350267fbbdbb126167bf341d19a649a9cf376a04a7bbae9bd0212de103` |
| `lsp-ts-jupiter-lv-pkg-deps.json` | `1e36a3f5167de87fdb170850b474d179ce865cc68fa45dd4ff68e55c82af3c67` |
| `lsp-ts-phazly-admin-pkg-deps.json` | `08b0be4ddf60ece8007bcd7a9ca28c4870d56c6a7376deec6f8c751f2f60b8a8` |
| `lsp-rust-jupiter-desktop.json` | `8c8297672a4db88fa7868bf5fc7e08e6b0142988b6c863f563d1bb3e88ee479c` |
| `lsp-rust-logs-viewer-desktop.json` | `d0559ab00273b1e519547c7db9df45c331a5ab2c7645be9f9b3aee8d627ee8b4` |
| `lsp-go-opentelemetry.json` | `144e1f9f9f03dd7bda0dde04cfd243eab26b4312ecf6b0819771294dced13720` |
| `lsp-commonslang-java.json` | `6fd1ea5fbd24adfe9adc564dd330d9e01dbbba0baaef03cbec17697a7ec0514f` |
| `lsp-js-jupiter-root-deps.json` | `777c83605cdb626094b3374fdf0c1547c109ed84ee0c318a61104290dc4e96ca` |
| `lsp-js-phazly-root-deps.json` | `da85f6ec891b8e9fc4365c2b85ec63d7577e06b763bb87cf1d5e1e7e09d3cf97` |
| `lsp-ts-jupiter-jd-pkg-nodeps.json` | `417c884c6683df76d6170e4cabba91aea35e99a3adb6d6df9bf2ec208e9de89e` |
| `lsp-ts-jupiter-lv-pkg-nodeps.json` | `8ca39bc4731e7b7d14f95e297832e7b476b2e10e65076d95e9f9543a636ae3dd` |
| `lsp-ts-phazly-admin-pkg-nodeps.json` | `1858314b6453f51296197cb5db7a7f506c8bd07d9b4b8f5b0fbe7b1a28d49f03` |
| `lsp-ts-jupiter-jd-root-deps.json` | `d63c0bb1366977079c3cf6f203db6ee6d90ed7e808852b239407425a98f936db` |
| `lsp-ts-jupiter-lv-root-deps.json` | `c1f32c13773dfed3dd35b04bcc81fbeac254582593c105153374ec231e8ee59f` |
| `lsp-ts-phazly-admin-root-deps.json` | `9f55df8cb391879c17060527a674e5db9ae5c3d666dc05ab5bf5c6af8c30cdfa` |

Additional provenance hashes, relative to `<bench>`:

| File | SHA-256 |
|---|---|
| `clean/RESULTS.md` | `02ab12997d02ac446cf85871796ad3df59485b817f8a717da15bfd22bd20dab9` |
| `clean/summary-final.json` | `1849b7da3f6b511bd2afca418e5b9fd3d874f5d8ba1e2a82975f9dd4851d0d1c` |
| `clean/run-05-ts-js.final2.log` | `a01264e673a5b4e35915292b8c0e1010c2b508fd3f32ec96d7687f77e09d426f` |
| `pyparser/op1-verified.txt` | `3d5ac44d3ebce450541a0d2477149b469178057c703d6fc30ac01b52f2774f33` |
| `pyparser/op2-verified.txt` | `b1d136c9f1088a0abae54790255bd7d6395c42d7845be9218ba6ef3beb1d3f5b` |
