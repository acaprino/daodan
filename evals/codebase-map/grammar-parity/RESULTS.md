# grammar-parity results

Run date: **2026-10-22**. Single run, one machine, Windows. These are
observations, not a statistical measurement.

## Version under test

The eval protocol requires naming what was exercised. Everything below is from
these exact builds.

| Component | Identity | Notes |
|---|---|---|
| `tree_sitter_plsql` | 0.1.0, built from `njank/tree-sitter-plsql` @ `07c7acc` (2026-10-18) | built from source, MSVC `cl` 14.44.35207, VS 2022 Build Tools |
| — generated parser | ABI `LANGUAGE_VERSION 15` | `STATE_COUNT 45888`, `SYMBOL_COUNT 948`, `TOKEN_COUNT 473`, `EXTERNAL_TOKEN_COUNT 57`, `FIELD_COUNT 29` |
| `tree_sitter_sql` | 0.3.11 from PyPI (`derekstride/tree-sitter-sql`) | released 2025-09-30; upstream `main` was at 2026-10-17 **carrying the same version string**, so this wheel lags `main` by about twelve months of commits |
| `tree_sitter` | 0.26.0 | Python bindings |
| CPython | 3.12.10 | abi3 cross-check ran under 3.11.15 |
| `andreasmaierde/tree-sitter-plsql` | @ `28aebef` (2023-02-18), inspected only | ABI 14, `STATE_COUNT 10236`, `SYMBOL_COUNT 839`, `EXTERNAL_TOKEN_COUNT 0` |
| plugin adapters | working tree at the run date | `languages/plsql.py`, `languages/sql.py`, `notes[0] == "parser=regex (plsql)"` |

Reproduce with `python eval_grammars.py` and `python isolate_constructs.py`
after installing the prerequisites in `README.md`.

## Gate outcome

| Configuration | pass | fail | skip | exit |
|---|---:|---:|---:|---:|
| both grammars installed | **13** | 0 | 0 | 0 |
| Oracle grammar absent, `tree-sitter-sql` present | 6 | 0 | **7** | 0 |

The second row is the realistic CI condition and is the reason the skip policy
exists: the seven Oracle cases report `SKIP` with `ModuleNotFoundError` and the
install command, and never masquerade as passes.

Two of these cases failed on their first run, and in both the case was wrong
rather than the code. They are recorded because both mistakes are easy to repeat:

- `G8` originally included a trivial PL/pgSQL body, which the generic SQL grammar
  does parse clean. That contradicted `G9`, which pins exactly that fact. The
  trivial body is now `PLPGSQL_CONTROL` and belongs to `G9` alone.
- `G11` originally asserted that `ParseResult.external_calls` was empty. It is
  not: the adapter populates it with seven `call_type='database',
  pattern='sql-dml'` entries. `external_calls` is an **effects** taxonomy
  (database / network / filesystem / messaging / ipc) feeding the effect digest,
  not a call graph. The case now asserts the real distinction: effects are
  recorded, caller to callee pairs are not.

## Evidence base, and what it bounds

**There is no real Oracle or PostgreSQL corpus behind any of this.** Neither of
the two projects the resolver measurements ran against contains SQL or PL/SQL
code at all, and this repository holds only fixtures. Every file in `corpus.py`
is hand-written by the same person who wrote the assertions.

That bounds the conclusions hard. What is established is which constructs each
engine handles and which it does not, and that the Oracle engine emits structured
call nodes where the existing adapter emits none. What is **not** established is
any recall or precision figure on real code, any performance figure, or any
estimate of how often the pinned gaps occur in production PL/SQL. A gap that
never appears in a real codebase costs nothing; a gap that appears in half of one
is disqualifying. Neither can be known from ten hand-written files.

## Oracle construct matrix

23 constructs, both engines, one construct per parse (`isolate_constructs.py
--section C`).

| | clean | ERROR |
|---|---:|---:|
| `njank-plsql` | **16** | 7 |
| `derekstride-sql` | **1** | 22 |

The single construct the generic SQL grammar handles and the Oracle grammar does
not is `@dblink` in a `FROM` clause. It fails on packages, package bodies, object
types and type bodies, triggers, PL/SQL procedures, `%NOTFOUND`, `GOTO`,
`PRAGMA`, `RESULT_CACHE`, `PIPELINED`, `WITH FUNCTION`, `LISTAGG` in both forms,
`KEEP`, `MERGE ... DELETE WHERE`, `(+)` outer joins, `q'[...]'` quoting,
`CONNECT BY` / `START WITH` / `ORDER SIBLINGS BY` / `SEARCH ... CYCLE`,
`JSON_TABLE` `COLUMNS ... PATH`, and escaped quotes inside quoted identifiers.

**The generic SQL grammar is not a candidate for Oracle.** It is a
PostgreSQL/MySQL/T-SQL-flavoured grammar, and the dialect mismatch is total
rather than partial.

## Negative controls

`isolate_constructs.py --section N`. Invalid Oracle must be rejected; a grammar
that accepts everything is worthless as evidence.

| Input | `njank-plsql` | correct? |
|---|---|---|
| `PROCEDURE q(x IN DATE) DETERMINISTIC;` (invalid: DETERMINISTIC applies to functions) | ERROR at `'DETERMINISTIC'` | yes |
| `FUNCTION q(x IN DATE) RETURN NUMBER DETERMINISTIC;` (valid) | **clean** | yes |
| `FUNCTION f(x NUMBER) IS ...` with no `RETURN` clause (invalid) | ERROR | yes |
| unbalanced `BEGIN` with no `END` (invalid) | ERROR | yes |

The first row is a recorded mistake. An earlier version of the corpus carried the
invalid form and its rejection was reported as a grammar gap. It was the test
that was wrong. `N1` and `N1b` exist so the same misattribution cannot happen
quietly again.

## Call recall and precision inside a package body

`02_pkg_body.pkb`, 66 lines, `isolate_constructs.py --section A`.

Ground truth hand-counted in `corpus.EXPECTED_CALLS_IN_PACKAGE_BODY`: **8**
cross-unit calls. Recovered as dotted `ref_call` nodes: **8 of 8**, including a
call inside an `EXCEPTION` handler, one in a declaration default expression, one
in the package initialization section, and one intra-package sibling call.

Node shape:

```
(ref_call
  (referenced_element (identifier) (identifier))
  (parameter (parameter_element (parameter_value (literal_string)))))
```

which for `logging_pkg.init('order_mgmt')` gives the dotted callee as separate
`identifier` children plus typed parameters. That is directly consumable as a
graph edge.

Total `ref_call` nodes: 11. Breakdown:

| | count | verdict |
|---|---:|---|
| cross-unit or sibling routine calls | 8 | true positive |
| `NVL(SUM(total), 0)` | 1 | true positive, builtin wrapping an aggregate |
| `l_ids(i)` collection subscript | **2** | **false positive** |

Raw precision **9/11 = 82%** on this file. The false positive is mechanically
filterable: it has no dotted receiver and its referent is a local collection
declared in the same scope. `G7` pins it so that obligation stays visible.

Also emitted, as distinct node types rather than `ref_call`:
`aggregate_function_call` for `SUM(total)`, a dedicated
`raise_application_error_statement`, and `execute_immediate`.

Two recall limits measured:

- `l_ids.COUNT`, a collection method, is **not** a `ref_call`.
- The call inside `EXECUTE IMMEDIATE 'BEGIN stats_pkg.refresh(:1); END;'` is
  reachable only by re-parsing the string literal. The `execute_immediate` node
  exists and keeps the literal intact; nothing extracts the target.

## Gap register for the Oracle grammar

Three tiers, because they carry different weight.

**Declared by the grammar's own README, confirmed:**

| Gap | Case |
|---|---|
| `LISTAGG(DISTINCT ...)` | `G5`, `C10` |
| `@dblink` references, in `FROM` and in a call | `G5`, `C11`, `C12` |
| Oracle-wrapped (obfuscated) bodies | `G5`, `C07` |

**Found by measurement, not declared:**

| Gap | Case | Note |
|---|---|---|
| `KEEP (DENSE_RANK ...) OVER (...)` | `G6`, `C13` | `KEEP` **without** `OVER` is clean (`C14`), so it is the combination |
| `PIPELINED` in a function signature | `G6`, `C15` | `PIPE ROW` inside a normal function body is clean (`C16`) |
| `WITH FUNCTION` (12c inline function) | `G6`, `C17` | |

**Contradicting the grammar's own README:**

| Claim | Measured | Cases |
|---|---|---|
| "`$IF`/`$END` as named trivia, `$$inquiry` directives" | `$IF TRUE $THEN` is clean; `$IF $$DBG $THEN` is **ERROR**, in a spec, in a body, with `$ELSE`, and with `$ERROR` | `D1`–`D5` |

Conditional compilation with a literal condition works. With an inquiry directive
it does not. The README claims both.

**Verified working, beyond the README's list:** `%TYPE` / `%ROWTYPE`,
`PRAGMA AUTONOMOUS_TRANSACTION`, `PRAGMA EXCEPTION_INIT`,
`PRAGMA RESTRICT_REFERENCES`, `BULK COLLECT` / `FORALL` / `LIMIT`,
`RESULT_CACHE RELIES_ON`, `CASE`, `GOTO` with `<<label>>`, `SYS_REFCURSOR`,
`%NOTFOUND`, `MERGE` with `DELETE WHERE`, multi-predicate `(+)` outer joins,
`q'[...]'` alternative quoting, `SELF.g()` member dispatch, escaped quotes in
quoted identifiers, and every non-reserved-keyword identifier tried.

## PostgreSQL

**Procedural: no engine.** `G8` pins it. Eight realistic PL/pgSQL bodies, every
available grammar, all ERROR. The published field is `chrde/tree-sitter-plpgsql`
(4 stars, last pushed 2021-09-02, **no licence**, therefore unusable) and
`latchbio/tree-sitter-plpgsql` (0 stars, 2023-10-28, Unlicense). Neither was
built or evaluated: one has no licence and neither has any signal of use.

**`G9` is the finding that corrects an earlier claim.** The generic SQL grammar
parses `AS $$ BEGIN RETURN 1; END; $$ LANGUAGE plpgsql` **clean**, in either
clause order. Adding any one real statement flips it to ERROR, and the error
lands **inside** the quoted body:

| Body | `derekstride-sql` |
|---|---|
| `BEGIN RETURN 1; END;` | clean |
| + `DECLARE` | ERROR at `'x := 1;'` |
| + `%ROWTYPE` | ERROR at `'%ROWTYPE'` |
| + `IF/THEN` | ERROR at `'IF 1 = 1 THEN'` |
| + `EXCEPTION WHEN` | ERROR at `'EXCEPTION WHEN no_data_found THEN'` |
| + `RAISE EXCEPTION ... USING ERRCODE` | ERROR at the `RAISE` line |
| + `PERFORM audit_write(...)` | ERROR at the `PERFORM` line |
| `DO $$ BEGIN PERFORM 1; END $$;` | ERROR |
| `CREATE PROCEDURE ... LANGUAGE plpgsql AS $$` | ERROR |

A clean result on a toy body is therefore **not** evidence of dollar-quote
support. An earlier measurement in this investigation reported that it was, on
exactly such a toy body, and that report was wrong.

**SQL:** `G10` pins that PostgreSQL-legal nested block comments
(`/* a /* b */ c */`) are unhandled by both grammars. On `09_pg_sql.sql` the
generic grammar additionally fails on `ARRAY[]::TEXT[]`; the Oracle grammar fails
on `IF NOT EXISTS`, `::jsonb` casts and `::TEXT[]`, as expected of an
Oracle-only grammar. The Oracle grammar also rejects plain PostgreSQL dollar
quotes in a `SELECT` list (`B9`, `B10`), correctly.

## The repository's own adapters, measured

`G11`, `G12`, `G14`, on the same corpus.

- **Declarations work.** `02_pkg_body.pkb` yields `classes=['order_mgmt']` and
  `functions=['close_order', 'purge_old_orders', 'get_order_total']`, labelled
  `parser=regex (plsql)`.
- **No call edges.** `external_calls` carries seven entries, all
  `('database', 'sql-dml')`, which is an effects classification. **0 of 6**
  cross-unit callees and **0 of 8** hand-counted calls are recoverable from any
  field of the `ParseResult`.
- **Dynamic SQL target destroyed** (`G14`). Line 62 is reported as
  `'EXECUTE IMMEDIATE                                     USING p_cutoff;'`. The
  string literal holding `stats_pkg.refresh(:1)` has been blanked out, so the
  target is unrecoverable. The Oracle grammar keeps the literal intact.
- **Escaped identifiers mangled** (`G12`). `10_quoted_identifiers.sql` yields
  `classes=['sales data.order"items', 'CREATE VIEW ghost AS SELECT 1']`: the
  doubled quote is broken, and the *content of a quoted identifier* is returned
  as a view name.
- **Ownership is best-effort by its own admission.** `languages/plsql.py` states
  in comments that it does not track package boundaries ("that would require a
  real parser") and attaches cursors and exceptions to "the last package seen".
  `_INNER_FUNCTION_RE` anchors only at line start, so a `FUNCTION ... RETURN`
  line inside a string literal matches; the masking covers comments, not quoted
  strings.

## Packaging

Measured and rejected. Full numbers, the exact patch and the build recipe are in
`abi3-packaging.md`. Summary: an abi3 build is viable and was verified across
two Python minor versions, one binary per platform instead of twenty, 0.79 MB
per wheel. Bundling the compiled extension was costed at 222 MB across the five
host packages against ~30 MB for all of `exports/` today, would introduce the
repository's first tracked binary, and would transfer a permanent
four-platform build obligation to us for an artifact whose upstream publishes no
tests.

## Not measured

- **No real corpus.** See "Evidence base". Every figure above is from ten
  hand-written files.
- **No performance figure.** Parse latency, memory and the effect of the 11.12 MB
  installed extension on snapshot time were not measured.
- **No incremental-parse behaviour.** tree-sitter's edit-and-reparse path was not
  exercised; only whole-file parses.
- **`STATE_COUNT` headroom was not stress-tested.** The grammar reports 45,888
  against a self-declared limit of about 48,000, i.e. 2,112 states, and its
  README warns that overflow misparses silently. No attempt was made to find a
  construct that crosses it.
- **Linux and macOS builds.** Only `win_amd64` was compiled. The abi3 tag
  suggests the other three platforms behave the same; that is an inference, not a
  measurement.
- **The upstream `main` of `derekstride/tree-sitter-sql`.** Only the PyPI 0.3.11
  wheel was tested, which lags `main` by roughly twelve months. At least two
  scanner fixes landed after it, so some findings here may already be fixed
  upstream.
- **Other Oracle dialects and versions.** No 11g, 19c or 23c specific syntax was
  probed separately; `WITH FUNCTION` is the only version-gated construct in the
  matrix.

## Decision this supports

Oracle PL/SQL becomes an **optional, probed** engine: probe for
`tree_sitter_plsql`, use it when present, stamp `resolver` and `confidence` on
every edge it produces, and fall back to the labelled regex adapter when it is
absent, with the report declaring that bodies then yield no call edges. No fork,
no vendoring, no bundled binary. This gate is the compensating control for
depending on an untested third-party grammar.

PostgreSQL procedural stays a **declared gap**. There is no engine to adopt, and
`G8` is the tripwire that says so the day there is.

**Status of the mechanism this decision depends on (2026-10-22).** The stamping
half now exists and is exercised for Python: every reference carries
`payload.resolver` (`builtin-lexical`, or `<engine>@<version>` for an engine edge),
a derived store binds engine edges to one snapshot revision, and
[`resolve_edges.py`](../../../plugins/codebase-map/skills/map-method/scripts/resolve_edges.py)
probes its engine and declares the degradation when it is absent. The PL/SQL engine
itself is **not attached**: no `tree_sitter_plsql` adapter ships, the regex adapter
still yields no call edges from bodies, and this gate still passes 13/13 only where
both grammars are installed. What changed is that attaching it no longer requires
inventing a resolver identity or a confidence vocabulary.
