# Analysis Templates and Verification Model

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
procedure in `codebase-xray:xray-method`. Structure already recorded comes from
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

## The Semantic Analysis Mandate

```
Scripts extract STRUCTURE:  "class Foo with method bar()"
Claude extracts MEANING:    "Foo implements Repository pattern for
                             caching user sessions with TTL expiration"

NEVER stop at structure. ALWAYS pursue understanding.
```

## Semantic Analysis Template

Use `templates/semantic_analysis.md` for comprehensive per-file analysis that includes:

- Executive summary (purpose, responsibility, patterns)
- Behavioral analysis (triggers, processing, side effects)
- Dependency analysis (why each dependency exists)
- Quality assessment (strengths, concerns, red flags)
- Contract documentation (full interface semantics)
- Flow tracing (primary and error paths)
- Testing implications (what must be tested)

## JSON Output Structure

```json
{
  "file": "src/utils/circuit_breaker.py",
  "classification": "critical",
  "metrics": {
    "lines_of_code": 245,
    "num_classes": 2,
    "num_functions": 8,
    "num_dependencies": 12
  },
  "structure": {
    "classes": [],
    "functions": [],
    "constants": []
  },
  "dependencies": {
    "internal": [],
    "external": [],
    "external_calls": []
  },
  "usages": [],
  "verification_required": true
}
```

## Markdown Output Format

The markdown output follows the template in `templates/analysis_report.md` and produces sections suitable for inclusion in phase deliverable documents.

## Comment Type Classification

| Type | Category | Description | Action |
|------|----------|-------------|--------|
| **function** | GOOD | API docs at function/class top | Keep/Enhance |
| **design** | GOOD | File-level algorithm explanations | Keep |
| **why** | GOOD | Explains reasoning behind code | Keep |
| **teacher** | GOOD | Educates about domain concepts | Keep |
| **checklist** | GOOD | Reminds of coordinated changes | Keep |
| **guide** | GOOD | Section dividers, structure | Keep sparingly |
| **trivial** | BAD | Restates what code says | Delete |
| **debt** | BAD | TODO/FIXME without plan | Rewrite/Resolve |
| **backup** | BAD | Commented-out code | Delete |

## Comment quality analysis

1. Scan and analyze comment issues; write a report inside the run.
2. Verify the finding in source, distinguish useful context from repetition.
3. Propose a change with the affected path and reason. Do not apply it in X-ray.
4. A separate authorized readability/development task performs and verifies edits.

## Documentation diagnosis

1. Scan health and validate links without fix flags.
2. Compare claims with current source and the declared requirement.
3. Report obsolete candidates, broken links and stale navigation with evidence.
4. Write results inside the run. Knowledge maintenance owns application and review.
