> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

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

## Script Commands

All scripts live in `${PLUGIN_ROOT}/skills/map-method/scripts/`.

Use the current owned manifest for inventory, graph discovery and source reading.
Standalone commands supplement classification, usage search or parser diagnosis;
they do not create another authoritative index.

### Static Graph Discovery

Before mapping structure, calls or flows, run:

```bash
python "${PLUGIN_ROOT}/skills/map-method/scripts/source_reader.py" graph \
  "<source_manifest>" --path src/service.py --hops 3 --limit 100
```

Repeat `--path` for exact repository-relative files, never directories; omit it
for the whole inventoried scope. Hops range from 1 to 3. The read-only query uses
the supplied manifest's semantic/import graphs, checks source identity and parser
fingerprint, and neither reparses nor writes a snapshot.

Select question-relevant candidate `requests`; read them with `source_reader.py read`
before claims.
Retain JSON only at an explicitly brief-owned run-artifact path; a saved graph
object is directly accepted by `read --requests`. Otherwise read selected
requests without saving. Never write into a parent or another worker's run.

The `xray/source-graph/v1` packet binds its manifest/query, declarations,
callsite spans, target identities, resolution/reasons, imports, coverage and
diagnostics. Record seeds/hops, manifest binding, unavailable AST coverage,
parser fallback, section totals and `truncated`. Narrow or split clipped queries before raising
their limit; retain gaps. AST metadata is not deep reading, and static
resolution does not cover dynamic dispatch or arbitrary receiver types. Cycles,
transitive importers and PageRank guide reading, not criticality or incremental
invalidation. Usage search/Grep supplements dynamic, uncovered or ambiguous
cases; it never replaces a successful graph query.

### 1. Analyze Single File

```bash
# Python
python "${PLUGIN_ROOT}/skills/map-method/scripts/analyze_file.py" \
  --snapshot "$source_manifest" --project-root "<bound-project-root>" \
  --file src/utils/circuit_breaker.py \
  --output-format markdown

```

**Parameters:**
- `--file` / `-f`: Relative or absolute path to file - **REQUIRED**. Any supported extension (see the Language Support table in `SKILL.md`).
- `--output-format` / `-o`: Output format (json, markdown, summary) - default: summary
- `--snapshot`: exact current run snapshot; workflow analysis reuses extraction and semantic bindings. Missing/stale evidence needs the owner's refresh.
- `--find-usages` / `-u`: Find all usages of exported symbols - default: false

### 2. Find Usages of One Symbol

```bash
python "${PLUGIN_ROOT}/skills/map-method/scripts/analyze_file.py" \
  --snapshot "$source_manifest" --project-root "<bound-project-root>" \
  --file src/utils/circuit_breaker.py --find-usages --symbol CircuitBreaker
```

`--symbol` restricts the usage search to a single exported symbol; the script errors cleanly if the symbol is not exported by the file.

### 3. Structural Parse Only

```bash
python "${PLUGIN_ROOT}/skills/map-method/scripts/ast_parser.py" src/services/auth.ts
```

Emits the raw structural extraction (classes, functions, imports, exports) as JSON. Reports the active parser in `notes`.

## Tool Integration

Scripts support the languages in `SKILL.md`. Throughout Phases 1-6, recorded
structure comes from the current manifest; source evidence uses `source_reader.py`.

- **Phase 1-2 (Structure):** Query `source_reader.py graph` first; use manifest metadata/outline for exact definitions and `read` for public contracts. `ast_parser.py` supplies only required missing details, such as signatures/export annotations, or single-file diagnosis. Use `classifier.py` for additional triage metrics; never reparse recorded structure
- **Phase 5 (Risks):** Use the bound graph and `analyze_file.py --snapshot "$source_manifest" --find-usages --symbol <name>` for requested symbol usages without a new project extraction. Multi-language: matches Python `from/import`, Java `import`, JS/TS `import`/`require`, Rust `use`, etc.
- **Phase 6 (Docs):** Use `doc_review.py` for link validation and marker checks, and `rewrite_comments.py` for multi-language comment quality analysis (Python `#`/docstrings, Java/JS/TS `//` / `/* */` / Javadoc / JSDoc, SQL/PL-SQL `--` / `/* */`, Rust `//` / rustdoc).

Inventoried file-level formats use whole-file fallback; uninventoried extensions
remain outside coverage. Tree-sitter is optional (Prerequisites in
`references/snapshot.md`): Java/JS/TS/Rust fall back to regex. Python uses stdlib
`ast`, SQL/PL-SQL regex DDL and CSS/SCSS/LESS a stdlib tokenizer.

Do NOT use raw bash commands (cat, grep, find) to extract structure when a dedicated script exists. The scripts use real parsers, which are faster, more accurate, and consume fewer tokens than reading files line by line.

## Source Reading from the Bound Snapshot

Other plugins load `codebase-map:map-method` by name; helpers belong to its installed
package. Preserve the identified analysis run's evidence lineage and the exact
current owned snapshot path downstream, resolved with `snapshot.py resolve`.
SQLite is the default; explicit JSON and legacy parents retain their actual path. A latest mirror identifies
no snapshot. After every verified diff, obtain the current source manifest with
`snapshot.py write --reuse` before graph queries or block reads, including `none`
and LF/CRLF-only differences. Normalized parent claims do not establish current
source-byte identity. Missing/stale manifests require a caller-owned refresh;
never alter the parent or create an unowned index. Context-brief callers supply
this same current `source_manifest` prerequisite.

1. State the source question. For structural/call/flow mapping, query the graph
   first as above. Use question-relevant requests and outline names/paths to select
   source, relative to the manifest's repository root. Outline metadata neither
   validates current source bytes nor counts as deep reading.
2. Read the selected definitions or inclusive line ranges. The reader checks
   current content identity and parser identity before emitting numbered source.
   Changed or deleted files and parser mismatches require a refreshed manifest.
3. Follow callers, callees, validation gates, constants, types, configuration and
   implicit references. Include applicable stylesheets/markup for screens.
   Graph/import neighbours cannot establish completeness. Expand requests or
   use `--full` until each claim is supported.
4. Record the files and ranges actually examined, parser diagnostics and any
   remaining gaps. Keep inventory, source read in depth and runtime evidence as
   separate coverage facts. Codebase Map remains static.

```bash
python "${PLUGIN_ROOT}/skills/map-method/scripts/source_reader.py" outline \
  "$source_manifest" --path src/service.py --pattern 'Service|validate' --limit 40

python "${PLUGIN_ROOT}/skills/map-method/scripts/source_reader.py" read \
  "$source_manifest" --path src/service.py \
  --symbol Service.validate --symbol load_config --lines 1:20

python "${PLUGIN_ROOT}/skills/map-method/scripts/source_reader.py" read \
  "$source_manifest" --path src/service.py --full

python "${PLUGIN_ROOT}/skills/map-method/scripts/source_reader.py" read \
  "$source_manifest" --requests <run-dir>/source-requests.json
```

`--symbol` and `--lines` are repeatable. Use qualified names exactly as returned
by the outline, including `Class.method`. A requests file is a JSON list, or an
object with `requests`, containing `path`, `symbols`, `ranges` (`start`/`end`)
and optional `full_file` and `context` entries.

Selections retain shared file/class text outside complete function/method
intervals and Java/JavaScript/TypeScript/Rust callable boundary lines, preserving
imports, types, constants, static fields, decorators and shared-line declarations.
`context: false` on every request for a file emits only the selection (reason
`selection`), for context-packet leads, never mandatory evidence. A selected
nested callable is emitted with its enclosing callables.
The reader reports whole-file fallback for legacy/unreliable spans: inferred,
merged, parser-error, single-line, partially overlapping, class-boundary,
long-line, minified or shared-line definitions, even with exact end lines;
strict nesting is not an overlap. Retained context
proves neither omitted bodies irrelevant nor semantic dependencies complete.
Block selection limits model input; every requested file is still read and
hash-checked in full. It promises no measured model-time saving.

### Source reading in every code phase

Resolve `source_manifest` with `snapshot.py resolve $RUN_DIR` from the declared
binding. Never infer an extension, load the database as text or dump the manifest
into model context. Graph discovery precedes mapping; bounded
exact-path/pattern outlines locate definitions. Keep `totals`, `truncated`, coverage and identity. Narrow or split truncated
requests before raising the limit. Binary bytes/base64 never go to the model;
targeted textual packets reduce context, while SQLite reduces local materialization. Read
selected symbols/ranges and expand the evidence as above. Preserve whole-target
cascade scans and mandatory entry-gating paths.

Changed/deleted source or parser mismatch requires a current owned refresh before
continuing. Whole-manifest discovery requires neither blanket reading nor expanded
source/partition boundaries.
Each phase report's `## Source reading` records exact manifest, graph query/gaps,
actual files/ranges, diagnostics and fallback. Deduplicate actual reads for final
deep-read coverage, separately from inventory and user-supplied runtime evidence.
Graph/outline metadata is not deep reading. On updates, preserve carried parent
reading provenance separately; copied ledgers never count as current reads. Add
current re-derivation reads to the relevant phase ledger.

## File Classification Criteria

| Classification | Criteria | Verification |
|---------------|----------|--------------|
| **Critical** | Handles authentication, security, encryption, sensitive data | Mandatory |
| **High-Complexity** | >300 LOC, >12 dependencies, state machines, async patterns | Mandatory |
| **Standard** | Normal business logic, data models, utilities | Recommended |
| **Utility** | Pure functions, helpers, constants | Optional |

The classifier matches patterns against raw file content (including comments and string literals), so treat its verdict as a triage signal to be confirmed by reading the file, not as ground truth.

## Best Practices

### Source Code Analysis (Phases 1-5)
1. Start with Phase 1 - foundation modules inform everything else
2. Never skip code-path verification for critical/high-complexity files. This is static analysis: runtime evidence is welcome when supplied, never required, never fabricated
3. Keep all writes inside the active run directory until the publish step

## Maintained documentation

Read this section when verifying maintained documentation, not for phase-file claims.

## Verification Trust Model

```
Layer 1: TOOL-VALIDATED
  - Automated checks: file exists, AST symbol exists, signature matches
  - Marker: [VALIDATED: file.py::ClassName.method_name @ 2025-12-20]

Layer 2: HUMAN-VERIFIED
  - Manual review: semantic correctness, behavior match
  - Marker: [VERIFIED: file.py::ClassName.method_name by @reviewer @ 2025-12-20]

Layer 3: RUNTIME-CONFIRMED (only when the user supplies logs or traces)
  - Log/trace evidence of actual behavior, handed over by the user
  - Marker: [CONFIRMED: trace_id=abc123 @ 2025-12-20]

Tool validation catches STRUCTURAL issues (file moved, symbol renamed, signature changed).
Human verification ensures SEMANTIC correctness (code does what doc says).
Runtime confirmation proves BEHAVIORAL truth (system actually works this way).

Layers 1 and 2 are required for critical documentation. Layer 3 is added when runtime
evidence exists: the analysis is static, it cannot produce a trace, and a trace_id it
did not receive is a fabrication.

NOTE: Markers use qualified symbol names (Module::Class.method, file::function)
instead of line numbers. Line numbers shift on any edit; symbol names are stable
and survive refactoring as long as the symbol itself is not renamed.
```

## The Iron Law of Documentation

```
DOCUMENTATION = f(SOURCE_CODE) + VERIFICATION

If NOT verified_against_code(statement) -> statement is FALSE
If NOT exists_in_codebase(reference)    -> reference is FABRICATED
If NOT traceable_to_source(claim)       -> claim is SPECULATION
```

## The Temporal Purity Principle

```
Documentation = PRESENT_TENSE(current_implementation)

FORBIDDEN:
- "was/were/previously/formerly/used to"
- "deprecated since version X" -> just REMOVE it
- "changed from X to Y" -> only describe Y
- "in the old system..." -> irrelevant, delete
- inline changelogs -> use CHANGELOG.md or git

REQUIRED:
- Present tense: "The system uses..." not "The system used..."
- Current state only: Document what IS, not what WAS
- Git for archaeology: History lives in version control, not docs
```

**The Rule:**
> When you find documentation containing historical language, **DELETE IT**.
> Git blame exists for archaeology. Documentation exists for the present.

## Verification Requirements

Use the current run's resolved `source_manifest` and the source-reading
procedure in the Source Reading from the Bound Snapshot section above. Structure already recorded comes from
manifest metadata/outline; semantic verification comes from validated source
blocks expanded to the definitions and implicit context required by the claim.
After a verified diff, always obtain the current owned manifest with
`snapshot.py write --reuse` before block reading, even when normalized claims
are unchanged or only LF/CRLF bytes differ. Keep supported parent evidence and
its lineage separate from the current source-byte identity required by the reader.
Record actual files/ranges read. Neither outline metadata nor the presence of a
file in the inventory establishes semantic verification or runtime coverage.

| Documentation Type | Required Evidence |
|-------------------|-------------------|
| **Enum/State values** | Exact match with source code enum definition |
| **Function behavior** | Code path tracing, actual implementation reading |
| **Constants/Timeouts** | Variable definition in source with file:line |
| **Message formats** | Message class definition, field validation |
| **Architecture claims** | Import graph analysis, actual class relationships |
| **Flow diagrams** | Verified against runtime logs OR code path analysis |

## Documentation Verification Status

Every section of documentation MUST have one of these status markers:

- `[VERIFIED: file.py::ClassName.method_name]` - Confirmed against source code symbol
- `[VERIFIED: trace_id=xyz]` - Confirmed against runtime logs the user supplied
- `[UNVERIFIED]` - Requires verification before trusting
- `[DEPRECATED]` - Code has changed, documentation outdated

Symbol reference format: `file.py::symbol` for top-level, `file.py::Class.method` for members. A stylesheet symbol is the rule's flattened selector, `modal.css::.modal` or `modal.css::@media (max-width: 600px) { .modal }`, and a marker for one takes no `@ date` suffix, because the `@` of an at-rule would be read as one.
Never use line numbers in markers -- they break on any file edit.

**UNVERIFIED documentation is UNTRUSTED documentation.**
