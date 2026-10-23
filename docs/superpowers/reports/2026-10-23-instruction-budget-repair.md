# Instruction budget and graph compatibility repair

Date: 2026-10-23. Base: `1602f97490df0bb07937fbe5a9f50948aaae2124`.

The 20 instruction-budget failures blocking P2, P3 and P4 are resolved. A full
repository diagnostic also exposed five host compatibility failures and eight
graph parity failures. Those are repaired, with no remaining reported failure
in the isolated commit candidate.

## Instruction loads

The 20 budget failures came from four oversized instruction units and 16
aggregate step checks. The repair shortens instructions while preserving their
obligations. Component-authoring details move verbatim to a reference loaded
when authoring components; the always-loaded skill retains that explicit hook.

| Unit | Baseline words | Candidate words | Candidate cap |
| --- | ---: | ---: | ---: |
| Project protocol skill | 1909 | 1673 | 1682 |
| Lifecycle interview | 495 | 397 | 400 |
| Verification panel | 640 | 493 | 500 |
| Team review preparation | 3474 | 3049 | 3050 |
| Conditional component-authoring reference | Included in protocol | 208 | 208 |

No existing limit is raised. The authoring path has its own combined-load check.
Independent review verifies retained ownership, authorizations, delivery gates,
reviewer independence and recovery obligations. These measurements are words;
they are not a measurement of model tokens or API cost.

## Compatibility and graph parity

The map reading method again states that workers **only** resolve bindings.
The coordinator remains responsible for root migration. Regenerated packages
pass the existing compatibility oracle on all five hosts.

The storage parity reference predates P1/P2's additive `edge_view` metadata and
lexical call provenance. Its expected result now includes every new field and
still compares the entire graph exactly. SQLite's missing engine store and
JSON's unsupported format retain distinct expectations. Ignore-drift and
unresolved-call cases remain protected. Unicode fixtures explicitly use UTF-8
and assert a real parsed, resolved call, avoiding Windows encoding failures that
could otherwise make an empty graph appear equivalent. Production graph code
is unchanged by this repair.

## Verification and limits

- Full isolated candidate: **1511 tests**, exit 0, 786.076 seconds in unittest.
  The default runtime reports 11 skips. Nine Codebase Map MCP tests and one MOE
  SDK test pass separately in the existing SDK runtime; complete source/test
  hashes prove the results apply to the same candidate. The remaining skip is
  the POSIX executable-bit test on Windows.
- Targeted checks: instruction budget **5/5**, host compatibility **7/7**,
  storage queries **14/14**. Independent budget and parity reviews pass.
- All five host packages rebuilt and reproduced by the compiler. Dependency,
  bundled-path, host-vocabulary, registration, fact-anchor, documentation and
  instruction synchronization checks pass. These are compiler and contract
  checks, not installed-host workflow execution.
- The shared checkout's broader diagnostic ran 1664 tests, including concurrent
  unfinished features. Its 13 failure subcases identified the compatibility and
  parity defects above. Affected suites and common/build checks then pass in the
  shared checkout; that diagnostic is not represented as a final full-suite pass.

The isolated candidate contains only owned repairs and generated outputs.
Concurrent source changes are preserved in the shared checkout. Plugin patch
versions and marketplace 38.8.7 accompany the repair. The commit is local; no
remote publication is performed.

Evidence is retained under
`.tritech/daodan/runs/instruction-budget-repair-20261023/` and its separate
`instruction-budget-repair-20261023-record` protocol record. The latter links
the delivery, independent reviews, source fingerprints and final gate results.
The parent `code-context-scope-20261023` record closes P2, P3 and P4 after binding
those checks to the repair commit. P5 through P10 remain open in the
[implementation plan](../plans/2026-10-23-code-context-and-scope.md).
