# grammar-parity

A **mechanical** gate over SQL and PL/SQL parsing. Unlike the agent-scored cases
in `../cases/`, this runs as a script and asserts named invariants, so it can be
re-run on every change and cannot drift silently.

## Why it exists

The resolver layer treats the Oracle PL/SQL grammar as an optional, probed
engine. That grammar is third-party, publishes **no tests of its own**, ships no
wheel, and sits close to a state budget its own README says must not be exceeded
because overflow "generates without errors but misparses at runtime in
layout-dependent ways". Nothing else in the repository would notice a new
version of it starting to parse real code incorrectly. This directory is that
notice.

It also pins what we lose without the engine, so that "the existing regex
adapter already handles this" cannot be assumed again: three cases here assert
the adapter's concrete, measured limits.

## Relationship to the other eval assets

| Asset | Shape | Scored by |
|---|---|---|
| `../cases/` | behavioral invariants over a full `/daodan:map-code` run | a reader holding the assertions and the transcript |
| `../context-scope/` | code context and retrieval measurement | numbers, recorded in its `RESULTS.md` |
| `../resolver-spike/` | call-resolution measurement against real project snapshots | numbers, recorded per run |
| **`grammar-parity/`** | **parser-level invariants, no agent in the loop** | **`eval_grammars.py`, exit code** |
| `../../../tests/test_xray_scripts.py` | the shipped parsers' own unit suite | CI, every push |

`tests/test_xray_scripts.py` is the precedent for the skip policy below: it runs
the tree-sitter path wherever tree-sitter is installed and does not fail when it
is not.

## Prerequisites

`tree-sitter>=0.25` and `tree-sitter-sql==0.3.11` come from PyPI as wheels and
need no compiler. The Oracle grammar does:

```
pip install git+https://github.com/njank/tree-sitter-plsql
```

Windows needs MSVC Build Tools, Debian/Ubuntu needs `build-essential`. See
`abi3-packaging.md` for the measured build recipe and for the patch that makes
the result version-independent.

**Engines are probed, never assumed.** When the Oracle grammar is absent its
cases report `SKIP` with the reason and the install command, and the run still
exits 0 if nothing else failed. A `SKIP` is not a pass; it is counted separately
in the summary so a green run on a machine without the grammar cannot be
mistaken for coverage.

## Running

```
python eval_grammars.py                       # the gate; exit 1 on any MUST failure
python eval_grammars.py --json <scratch>.json # machine-readable, write outside the repo
python isolate_constructs.py                  # the observations behind the invariants
python isolate_constructs.py --section B C    # one construct at a time
```

`isolate_constructs.py` exists because every wrong conclusion reached while
building this gate came from parsing several constructs in one document and
attributing the resulting error to the wrong one. Its section N is a set of
negative controls: invalid Oracle that **must** be rejected, so that a correct
rejection is never again mistaken for a grammar gap. That mistake was made once,
in this directory's own history, and N1 is the case that remembers it.

## Invariants

| Case | Req | Invariant |
|---|---|---|
| `G1` | MUST | A package body yields structured dotted `ref_call` nodes, with full recall against a hand-counted ground truth |
| `G2` | MUST | Non-reserved Oracle keywords inside identifiers (`LoopContacts`, `outer`, `level_id`) are not split |
| `G3` | MUST | Doubled quotes inside a quoted identifier parse clean |
| `G4` | MUST | Each Oracle object kind gets its own named node, not a generic `statement` |
| `G5` | MUST, **inverted pin** | The gaps the grammar's own README declares are still open |
| `G6` | MUST, **inverted pin** | The gaps found by measurement and *not* declared are still open |
| `G7` | MUST, **inverted pin** | A collection subscript still surfaces as `ref_call`, so consumers must filter it |
| `G8` | MUST, **inverted pin** | No available grammar parses a realistic PL/pgSQL body: the PostgreSQL gap is still a gap |
| `G9` | MUST, **pin** | The generic SQL grammar's dollar-quote handling depends on the body: a trivial body is clean, every realistic one errors inside the quotes |
| `G10` | MUST, **pin** | PostgreSQL-legal nested block comments are unhandled by both grammars |
| `G11` | MUST | The repository's PL/SQL adapter yields declarations and effect kinds, never a caller to callee pair |
| `G12` | MUST, **pin** | The regex adapter still returns a mangled name for an escaped quoted identifier |
| `G13` | SHOULD | The abi3 recipe produces a version-independent wheel (compiler-gated, reported as SKIP unless built) |
| `G14` | MUST, **pin** | A dynamic SQL target is unrecoverable from the regex adapter: the literal is blanked out of the effect context |

### Inverted pins

`G5`, `G6`, `G7`, `G8`, `G9`, `G10`, `G12` and `G14` assert that a known defect
or gap **still exists**. They fail loudly the day it is fixed. That is the
intended behaviour: a fix must be re-measured and the claim in `RESULTS.md`
updated, not silently drifted past.

Do not weaken or delete an inverted pin to make a run green. Update the
expectation, record the re-measurement, and keep the case. This mirrors the rule
`../README.md` states for the agent-scored cases: a case that fails once keeps
its case forever.

## Corpus

`corpus.py`, hand-written. Ten files: eight Oracle, two PostgreSQL. Every
cross-unit call in `02_pkg_body.pkb` is enumerated in
`EXPECTED_CALLS_IN_PACKAGE_BODY` so recall is checked against a hand count rather
than against whatever node count the parser happened to emit, and the known false
positive is enumerated in `EXPECTED_FALSE_CALLS_IN_PACKAGE_BODY`.

The corpus is hand-written because no real one exists. See `RESULTS.md`,
"Evidence base", for what that bounds.
