# Evidence

## CRITICAL PRINCIPLE: EVIDENCE-ANCHORED OUTPUT

Each output claim cites its code and status. Independent review re-derives
premises and refutes claims contradicted by source.

### Mandatory Rules (VIOLATION = FAILURE)

1. **NEVER** document anything without reading the actual source code first
2. **NEVER** assume any existing documentation, comment, or docstring is accurate
3. **NEVER** write documentation based on memory, inference, or "what should be"
4. **ALWAYS** derive technical facts EXCLUSIVELY from reading and tracing actual code
5. **ALWAYS** cite `file:line` for every technical claim in a phase file, and add the qualified symbol (`file.py::Class.method`) where one exists. A stylesheet symbol is the rule's flattened selector, which carries spaces and punctuation, so it is cited inside single backticks exactly as the manifest names it, for example `theme.css::.dark #root > div:first-child`; the incremental gate matches that quoted form whole. The line locates the evidence for this run; the symbol survives the next edit. Downstream consumers (`premise-auditor`, the interconnect mapper, the review dimensions) read `file:line`
6. **ALWAYS** verify state machines, enums, constants against actual definitions
7. **TREAT** all pre-existing docs as unverified claims requiring validation
8. **MARK** every claim with the status the interconnect mapper uses: `verified` (enforced in code, cite where), `documented` (a document declares it, cite where), `unverified` (relied on, nothing enforces or documents it), `disputed` (two derivations disagree, cite both). `[UNVERIFIED - REQUIRES CODE CHECK]` stays the inline form for prose
9. **USE** qualified symbol names, never line numbers, in the verification markers of maintained documentation (`[VERIFIED: file.py::Class.method]`, see Maintained documentation below). Those markers persist across edits, where a phase file is regenerated every run

### Documents play two roles, and only one of them is constrained above

As **evidence**, a document is an unverified claim requiring validation. Rules 2 and 7 govern that role and are not negotiable: a document never establishes a technical fact.

As a **discovery lead**, a document must be collected early: concept names,
module pointers and intent guide source discovery without proving behavior.

Phase 0 collects leads. Phase 6 audits documents as evidence. Never let the second role suppress the first.

## Forbidden Files

NEVER read or include contents from:
- `.env`, `.env.*` - environment variables with secrets
- `credentials.*`, `secrets.*`, `*secret*`, `*credential*`
- `*.pem`, `*.key`, `*.p12`, `*.pfx` - certificates and private keys
- `id_rsa*`, `id_ed25519*` - SSH keys
- `.npmrc`, `.pypirc`, `.netrc` - auth tokens
- `*service-account*.json`, `*kubeconfig*`, `*.tfstate`, `*.tfstate.*`, `*.keystore`, `*.jks` - cloud credentials, infrastructure state, keystores
- Any file that appears to contain API keys, passwords, or tokens

If encountered: note file existence only ("`.env` present - contains environment config"). NEVER quote contents.

## Source reading

The one procedure for every claim about source, in every phase and for every
consumer. Scripts live in `${CLAUDE_PLUGIN_ROOT}/skills/map/scripts/`.
The current owned manifest is the only index: inventory, graph discovery and
source reading all come from it, and no standalone command creates another.

### Binding

Resolve `source_manifest` with `snapshot.py resolve $RUN_DIR` (or take the
exact current path a caller supplies). Never infer its extension, load the
database as text or dump the manifest into model context; binary bytes never
reach the model. SQLite is the default; explicit JSON parents keep
their actual path. A latest mirror identifies no snapshot. After a verified
diff the owner obtains a current manifest with `snapshot.py write --reuse`
before any read, whatever the recommendation (`references/snapshot.md`, Diff
and carry). A missing, stale or mismatched manifest (changed or deleted source,
parser mismatch) is refreshed by its owner, never by altering a parent run or
creating an unowned index; a worker reports the gap to its coordinator.

### Procedure

1. **State the source question, then query the graph first** for every
   structure, call or flow claim:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/map/scripts/source_reader.py" graph \
     "<source_manifest>" --path src/service.py --hops 3 --limit 100
   ```

   Repeat `--path` for exact repository-relative files, never directories; omit
   it for the whole inventoried scope. Hops range from 1 to 3. The query is
   read-only, checks source identity and parser fingerprint, and neither
   reparses nor writes. Its `xray/source-graph/v1` packet binds manifest and
   query, declarations, callsite spans, target identities, resolution and
   reasons, imports, coverage and diagnostics. Report call coverage as
   `edge_view.coverage.resolution`: resolved over resolvable, never resolved over
   all calls, per language from `by_language`, and name the engine state of a
   language whose stage is still running or unavailable. Narrow or split a `truncated`
   query before raising its limit; retain gaps. Static resolution does not cover
   dynamic dispatch or arbitrary receiver types, and a resolved edge verifies no
   contract. Cycles, transitive importers and PageRank guide reading, never
   criticality or invalidation. Usage search or Grep supplements dynamic,
   uncovered or ambiguous cases; it never replaces a successful query. Whole
   scope discovery needs neither blanket reading nor wider boundaries. Keep
   graph JSON only at a brief-owned run-artifact path (a saved packet feeds
   `read --requests`); never write into a parent or another worker's run.
2. **Select and read.** Outline names locate definitions; read the selected
   definitions or inclusive ranges, with qualified names exactly as the outline
   returns them (`Class.method`):

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/skills/map/scripts/source_reader.py" outline \
     "$source_manifest" --path src/service.py --pattern 'Service|validate' --limit 40

   python "${CLAUDE_PLUGIN_ROOT}/skills/map/scripts/source_reader.py" read \
     "$source_manifest" --path src/service.py \
     --symbol Service.validate --symbol load_config --lines 1:20

   python "${CLAUDE_PLUGIN_ROOT}/skills/map/scripts/source_reader.py" read \
     "$source_manifest" --path src/service.py --full

   python "${CLAUDE_PLUGIN_ROOT}/skills/map/scripts/source_reader.py" read \
     "$source_manifest" --requests <run-dir>/source-requests.json
   ```

   `--symbol` and `--lines` are repeatable. A requests file is a JSON list, or
   an object with `requests`, of `path`, `symbols`, `ranges` (`start`/`end`),
   optional `full_file` and `context`. The reader checks content and parser
   identity before emitting numbered source; every requested file is read and
   hash-checked in full, whatever the selection. Selections keep the shared
   file and class text outside complete callable intervals and the
   Java/JavaScript/TypeScript/Rust boundary lines (imports, types, constants,
   static fields, decorators, shared-line declarations); a nested callable is
   emitted with its enclosing ones; `context: false` on every request for a
   file emits only the selection (reason `selection`), for context-packet
   leads, never for mandatory evidence. Whole-file fallback applies to
   inferred, merged, parser-error, single-line, partially overlapping,
   class-boundary, long-line, minified or shared-line definitions, even with
   exact end lines; strict nesting is not an overlap. Retained context proves
   neither omitted bodies irrelevant nor dependencies complete, and no
   model-time saving is promised.
3. **Expand until each claim is supported:** callers, callees, validation
   gates, constants, types, configuration and implicit references, plus the
   stylesheets and markup of a screen. Graph and import neighbours never
   establish completeness; expand the requests or use `--full`. Keep the
   whole-target cascade scan and the mandatory entry-gating paths of Phases 3
   and 5.
4. **Record `## Source reading` in every phase file:** the exact manifest,
   graph seeds, hops, coverage and truncation, the files and ranges actually
   read, parser diagnostics and fallback, and the remaining gaps. Inventory,
   source read in depth and runtime evidence are three separate coverage facts:
   outline, graph and inventory metadata are not deep reading, runtime is none
   unless the user supplied it, and Codebase Map stays static. On an update,
   carried parent reading provenance stays separate and copied ledgers never
   count as current reads; add this run's re-derivation reads to the phase
   ledger. Final deep-read coverage deduplicates the ledgers by path.

## Other scripts

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map/scripts/analyze_file.py" \
  --snapshot "$source_manifest" --project-root "<bound-project-root>" \
  --file src/utils/circuit_breaker.py --output-format markdown

python "${CLAUDE_PLUGIN_ROOT}/skills/map/scripts/analyze_file.py" \
  --snapshot "$source_manifest" --project-root "<bound-project-root>" \
  --file src/utils/circuit_breaker.py --find-usages --symbol CircuitBreaker

python "${CLAUDE_PLUGIN_ROOT}/skills/map/scripts/ast_parser.py" src/services/auth.ts
```

`analyze_file.py` takes `--file` (required, any supported extension),
`--output-format json|markdown|summary` (default summary), `--snapshot` (the
exact current run snapshot, reusing its extraction and semantic bindings) and
`--find-usages`, restricted to one exported symbol by `--symbol`; it errors
cleanly when the file does not export that symbol. `ast_parser.py` emits the
raw structural extraction as JSON and names the active parser in `notes`.

- **Phases 1 and 2:** graph first; manifest metadata and outline for exact
  definitions; `read` for public contracts. `ast_parser.py` supplies only
  missing details (signatures, export annotations) or single-file diagnosis;
  `classifier.py` adds triage metrics. Never reparse recorded structure.
- **Phase 5:** the bound graph and `analyze_file.py --find-usages --symbol`
  for requested usages, without a new project extraction; usages match Python
  `from/import`, Java `import`, JS/TS `import`/`require`, Rust `use` and so on.
- **Phase 6:** `doc_review.py` for link validation and marker checks,
  `rewrite_comments.py` for comment quality (Python `#` and docstrings,
  Java/JS/TS `//`, `/* */`, Javadoc, JSDoc, SQL and PL/SQL `--`, `/* */`,
  Rust `//` and rustdoc).

Inventoried file-level formats use whole-file fallback; uninventoried
extensions stay outside coverage. Tree-sitter is optional (Prerequisites in
`references/snapshot.md`): Java/JS/TS/Rust fall back to regex, Python uses
stdlib `ast`, SQL/PL-SQL regex DDL, CSS/SCSS/LESS a stdlib tokenizer. Do not
use raw `cat`, `grep` or `find` to extract structure when a script exists: the
scripts use real parsers and cost fewer tokens than reading line by line.

## File Classification Criteria

| Classification | Criteria | Verification |
|---------------|----------|--------------|
| **Critical** | Handles authentication, security, encryption, sensitive data | Mandatory |
| **High-Complexity** | >300 LOC, >12 dependencies, state machines, async patterns | Mandatory |
| **Standard** | Normal business logic, data models, utilities | Recommended |
| **Utility** | Pure functions, helpers, constants | Optional |

The classifier matches patterns against raw file content, comments and string
literals included: its verdict is a triage signal to confirm by reading the
file. Mandatory verification traces every code path the claim depends on;
runtime evidence counts only when the user supplies it, and is never invented.

## Maintained documentation

Read this section when verifying maintained documentation, not for phase-file
claims. A statement not verified against code is false; a reference that does
not exist in the codebase is fabricated; a claim not traceable to source is
speculation. Documentation describes the present, in the present tense: delete
"was", "previously", "deprecated since", "changed from X to Y" and inline
changelogs, because Git holds the history.

### Markers

| Layer | Proves | Marker |
|---|---|---|
| Tool-validated | structure: file exists, symbol exists, signature matches | `[VALIDATED: file.py::Class.method @ 2025-12-20]` |
| Human-verified | semantics: the code does what the document says | `[VERIFIED: file.py::Class.method by @reviewer @ 2025-12-20]` |
| Runtime-confirmed | behavior, only from logs or traces the user handed over | `[CONFIRMED: trace_id=abc123 @ 2025-12-20]` |

Critical documentation requires the first two layers; the third is added only
when the user supplied the evidence, since the analysis is static and a
`trace_id` it did not receive is a fabrication. Every section carries one
status: `[VERIFIED: file.py::Class.method]`, `[VERIFIED: trace_id=xyz]`,
`[UNVERIFIED]` (untrusted until verified) or `[DEPRECATED]` (the code changed).
Markers name qualified symbols (`file.py::symbol`, `file.py::Class.method`),
never line numbers, which break on any edit. A stylesheet symbol is the rule's
flattened selector, `modal.css::.modal` or
`modal.css::@media (max-width: 600px) { .modal }`, and its marker takes no
`@ date` suffix, because the `@` of an at-rule would be read as one.

### Verification

Read source as `## Source reading` directs, from the run's resolved
`source_manifest`: structure already recorded comes from outline metadata,
semantic verification from validated source blocks expanded to the definitions
and implicit context the claim needs. Record the files and ranges read. Neither
outline metadata nor a file's presence in the inventory establishes semantic
verification or runtime coverage.

| Documentation Type | Required Evidence |
|-------------------|-------------------|
| **Enum/State values** | Exact match with source code enum definition |
| **Function behavior** | Code path tracing, actual implementation reading |
| **Constants/Timeouts** | Variable definition in source with file:line |
| **Message formats** | Message class definition, field validation |
| **Architecture claims** | Import graph analysis, actual class relationships |
| **Flow diagrams** | Verified against runtime logs OR code path analysis |
