> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

Every file this skill produces is a set of claims about the code, each anchored to the code and each carrying a status. None of it is unquestionable. `/senior-review:team-review` re-derives its premises without reading the Codebase Map and refutes a Codebase Map claim whenever the code disagrees; that is the design working, not failing. What makes the output worth consuming is that every claim says where it came from and how sure it is.

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

As a **discovery lead**, a document is a first-class input that must be collected early. A project's own index telling you that a concept named X exists and lives in module Y is not a claim about behaviour; it is a pointer telling you where to look and what to look for. Refusing to read it does not make the analysis more rigorous, it makes it blind to intent and to code paths the structure alone does not reveal.

Phase 0 collects leads. Phase 6 audits documents as evidence. Never let the second role suppress the first.

## Forbidden Files

NEVER read or include contents from:
- `.env`, `.env.*` - environment variables with secrets
- `credentials.*`, `secrets.*`, `*secret*`, `*credential*`
- `*.pem`, `*.key`, `*.p12`, `*.pfx` - certificates and private keys
- `id_rsa*`, `id_ed25519*` - SSH keys
- `.npmrc`, `.pypirc`, `.netrc` - auth tokens
- Any file that appears to contain API keys, passwords, or tokens

If encountered: note file existence only ("`.env` present - contains environment config"). NEVER quote contents.

## Script Commands

All scripts live in `<plugin-root>/skills/map-method/scripts/`.

For an identified run, use its bound manifest for inventory and symbol structure
and `source_reader.py` for source reading. The standalone commands below serve
classification, usage search or parser diagnosis when the question needs them;
they do not create a second authoritative index.

### 1. Analyze Single File

```bash
# Python
python "<plugin-root>/skills/map-method/scripts/analyze_file.py" \
  --file src/utils/circuit_breaker.py \
  --output-format markdown

# Java
python "<plugin-root>/skills/map-method/scripts/analyze_file.py" \
  --file src/main/java/com/example/UserService.java

# TypeScript
python "<plugin-root>/skills/map-method/scripts/analyze_file.py" \
  --file src/services/auth.ts

# Rust
python "<plugin-root>/skills/map-method/scripts/analyze_file.py" \
  --file src/lib.rs

# SQL / PL-SQL
python "<plugin-root>/skills/map-method/scripts/analyze_file.py" \
  --file migrations/0042_users.sql
```

**Parameters:**
- `--file` / `-f`: Relative or absolute path to file - **REQUIRED**. Any supported extension (see the Language Support table in `SKILL.md`).
- `--output-format` / `-o`: Output format (json, markdown, summary) - default: summary
- `--find-usages` / `-u`: Find all usages of exported symbols - default: false

### 2. Find Usages of One Symbol

```bash
python "<plugin-root>/skills/map-method/scripts/analyze_file.py" \
  --file src/utils/circuit_breaker.py --find-usages --symbol CircuitBreaker
```

`--symbol` restricts the usage search to a single exported symbol; the script errors cleanly if the symbol is not exported by the file.

### 3. Structural Parse Only

```bash
python "<plugin-root>/skills/map-method/scripts/ast_parser.py" src/services/auth.ts
```

Emits the raw structural extraction (classes, functions, imports, exports) as JSON. Reports the active parser in `notes`.

## Tool Integration

The scripts in `<plugin-root>/skills/map-method/scripts/` support
**Python, Java, JavaScript, TypeScript (incl. TSX/JSX), SQL, PL/SQL, Rust,
CSS (incl. SCSS and LESS)**. Use the current run's manifest for recorded
structure and `source_reader.py` for source evidence throughout Phases 1-6.

- **Phase 1-2 (Structure):** Use manifest file/import metadata and `source_reader.py outline` for existing structure. Read selected public definitions with `source_reader.py read`. Use `ast_parser.py` only for required extra details absent from the manifest, such as signatures/export annotations, or single-file parser diagnosis; use `classifier.py` when additional triage metrics are needed. Do not reparse the target for recorded structure
- **Phase 5 (Risks):** Use `usage_finder.py` to trace symbol usages across the codebase. Multi-language: matches Python `from/import`, Java `import`, JS/TS `import`/`require`, Rust `use`, etc.
- **Phase 6 (Docs):** Use `doc_review.py` for link validation and marker checks, and `rewrite_comments.py` for multi-language comment quality analysis (Python `#`/docstrings, Java/JS/TS `//` / `/* */` / Javadoc / JSDoc, SQL/PL-SQL `--` / `/* */`, Rust `//` / rustdoc).

Inventoried file-level formats, including configuration and markup, use the
reader's whole-file fallback; extensions absent from the manifest remain absent
from inventory coverage. Tree-sitter is optional (see Prerequisites in `references/snapshot.md`): Java/JS/TS/Rust use it when their grammar
loads, otherwise a regex fallback. Python uses stdlib `ast`, SQL/PL-SQL a regex
DDL extractor, and CSS/SCSS/LESS a stdlib tokenizer.

Do NOT use raw bash commands (cat, grep, find) to extract structure when a dedicated script exists. The scripts use real parsers, which are faster, more accurate, and consume fewer tokens than reading files line by line.

## Source Reading from the Bound Snapshot

Load `codebase-map:map-method` by name to use this procedure from another
plugin. The helper paths below belong to this skill's installed package. Use the
identified analysis run for evidence lineage and a current owned
`snapshot/manifest.json` for source reading; keep both exact paths downstream.
A latest mirror does not identify its snapshot. After every verified diff,
write or obtain the current source manifest with `snapshot.py write --reuse`
before block reading, including a `none` result or LF/CRLF-only differences.
Unchanged normalized claims can support parent evidence while the reader needs
new source-byte identity. Use this one current manifest, preserving the parent.

1. State the source question. Use the outline to choose exact symbol names and
   paths from the bound manifest; paths are relative to its recorded repository
   root. Outline output is metadata and does not validate current source bytes
   or count as deep reading.
2. Read the selected definitions or inclusive line ranges. The reader checks
   current content identity and parser identity before emitting numbered source.
   Changed or deleted files and parser mismatches require a refreshed manifest.
3. Follow the question's callers, callees, validation gates, constants, types,
   configuration reads and implicit references. Include applicable stylesheets
   and markup when tracing a screen. Import neighbours alone cannot supply those
   relationships. Expand the request or use `--full` until the claim is supported.
4. Record the files and ranges actually examined, parser diagnostics and any
   remaining gaps. Keep inventory, source read in depth and runtime evidence as
   separate coverage facts. Codebase Map remains static.

```bash
python "<plugin-root>/skills/map-method/scripts/source_reader.py" outline \
  <run-dir>/snapshot/manifest.json --path src/service.py --pattern 'Service|validate' --limit 40

python "<plugin-root>/skills/map-method/scripts/source_reader.py" read \
  <run-dir>/snapshot/manifest.json --path src/service.py \
  --symbol Service.validate --symbol load_config --lines 1:20

python "<plugin-root>/skills/map-method/scripts/source_reader.py" read \
  <run-dir>/snapshot/manifest.json --path src/service.py --full

python "<plugin-root>/skills/map-method/scripts/source_reader.py" read \
  <run-dir>/snapshot/manifest.json --requests <run-dir>/source-requests.json
```

`--symbol` and `--lines` are repeatable. Use qualified names exactly as returned
by the outline, including `Class.method`. A requests file is a JSON list, or an
object with `requests`, containing `path`, `symbols`, `ranges` (`start`/`end`)
and optional `full_file` entries.

Selected definitions retain shared file/class text outside the complete
function/method intervals, plus start/end lines of Java/JavaScript/TypeScript/Rust
callables. Imports, types, constants, static fields and decorators outside those
intervals stay; boundary lines also preserve globals or fields sharing a
callable's opening or closing line. The reader falls back to a whole file for legacy or unreliable
spans, including inferred, merged or parser-error entries, single-line,
overlapping or class-boundary spans, and long lines,
and reports that fallback. Minified or shared-line definitions can also force
whole-file fallback even with exact end lines, preserving class declarations
and static fields on those lines. This retained context does not prove that omitted
function bodies are irrelevant or that semantic dependencies are complete.
Block selection limits the source presented to the model; each requested file
is still read and hash-checked in full. It is not a measured model-time guarantee.

### Source reading in every code phase

Derive `source_manifest = $RUN_DIR/snapshot/manifest.json` from the run directory;
this is a prompt alias, not a new `state.json` field or another index. Use
`source_reader.py outline` with bounded exact-path/pattern queries to locate
definitions. Narrow truncated output. Use `source_reader.py read` with exact
symbols or line ranges to examine source, expanding to callers/callees, gates,
constants, types, invariants, configuration and applicable CSS/markup until each
claim is supported. Keep whole-target cascade scans for entry-gating paths.
Import neighbours and retained file/class context do not establish completeness.

Changed/deleted source or parser mismatches require refreshing the current run's
snapshot before continuing; never substitute a latest mirror or edit the parent.
Use full-file reading where needed, rather than reading every file by default.
Each code phase's owned report includes `## Source reading`: exact manifest,
actual source files/ranges examined, diagnostics and gaps. Derive final deep-read
coverage from that union, separately from inventory and user-supplied runtime
evidence. Outline metadata does not count as deep reading.
On an update, keep carried parent reading provenance separate from source
actually examined in this run; copied `## Source reading` sections do not count
as a current read. Add current re-derivation reads to the relevant phase ledger.

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

Use the current run's bound `snapshot/manifest.json` and the source-reading
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
