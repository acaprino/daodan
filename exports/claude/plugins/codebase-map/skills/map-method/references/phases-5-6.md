<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# Phases 5 and 6

## Phase 5: Pattern & Risk Detection

Tools for this phase:

- **Phase 5 (Usability-blocking):** Run `cascade_scan.py <client root>` (add `--json` to consume it) before reading any stylesheet by hand. It lists every rule whose selector reaches the document root, every element or the root's untargeted children and sets a positioning, scroll, sizing, display or containing-block property, with the class, id and attribute rules each one can override and what decides it in cascade order (`!important`, cascade layer, specificity, source order), screen-level rules first: a fixed or sticky position, a scroll container, a viewport height. Tailwind `@apply` utilities count as the declarations they inline, and when a stylesheet uses Tailwind, screen-level utilities in string-literal `class` and `className` attributes count as conflicts. Its output is leads, never verdicts.

Scan for anti-patterns, red flags, and technical debt:

- **Anti-patterns**: God objects, spaghetti code, shotgun surgery, feature envy
- **Red flags**: Swallowed exceptions, hardcoded credentials, race conditions, N+1 queries
- **Usability-blocking**: an entry-gating path (from Phase 3 when it ran, otherwise identified here from the Phase 1 entry points) that cannot be completed under a reachable configuration: theme, viewport, font scale, locale. Start from `cascade_scan.py`: each candidate it lists reaches the root or its untargeted children and sets a property that decides layout, and each conflict names a rule the candidate can beat. Confirm every candidate against the component tree: does its selector match the entry screen's element, and is its scope class applied there (`usage_finder.py`). A confirmed override of a fixed or scrollable entry screen is Critical. This is static evidence, ranked by what the cascade proves; nothing here was exercised, and the report says so unless the user supplied runtime evidence
- **Technical debt**: TODO/FIXME comments, deprecated APIs, outdated patterns
- **Failure modes**: What breaks under load, edge cases, missing error handling

**Output file:** `$RUN_DIR/05-risks.md`

```markdown
# Phase 5: Pattern & Risk Detection

## Anti-Patterns Found
[Organized by severity]

## Red Flags
[Security, reliability, performance, and usability-blocking risks. A usability-blocking row names the entry-gating path it blocks and the rule that blocks it]

## Technical Debt Inventory
[TODO/FIXME items, deprecated usage, modernization opportunities]

## Failure Mode Analysis
[What could break and under what conditions]

## Source reading
[Manifest, actual files/ranges, parser diagnostics and unresolved gaps]
```

---

## Phase 6: Documentation Health

Evaluate existing documentation against the code reality:

- **Accuracy**: Do docs match the actual code?
- **Completeness**: What's documented vs what should be?
- **Freshness**: When were docs last updated vs code?
- **Broken links**: References to files/functions that don't exist
- **Comment quality**: Using antirez standards (if `--comments` flag)

If `--comments` flag is set, also analyze comment quality:
- Identify trivial/debt/backup comments
- Score comment usefulness
- Suggest rewrites following antirez standards

Write Comment Quality only when `--comments` is active.

**Output file:** `$RUN_DIR/06-documentation.md`

```markdown
# Phase 6: Documentation Health

## Documentation vs Code Accuracy
[Mismatches between docs and reality]

## Coverage Gaps
[Undocumented public APIs, missing architecture docs]

## Broken References
[Dead links, non-existent file paths in docs]

## Comment Quality
[Comment audit with improvement suggestions]

## Source reading
[Manifest, actual files/ranges, parser diagnostics and unresolved gaps]
```

### Red Flags to Identify

```
ARCHITECTURE:
- GOD CLASS: >10 public methods or >500 LOC
- CIRCULAR DEPENDENCY: A -> B -> C -> A
- LEAKY ABSTRACTION: Implementation details in interface

RELIABILITY:
- SWALLOWED EXCEPTION: Empty catch blocks
- MISSING TIMEOUT: Network calls without timeout
- RACE CONDITION: Shared mutable state without sync

SECURITY:
- HARDCODED SECRET: Passwords, API keys in code
- SQL INJECTION: String concatenation in queries
- MISSING VALIDATION: Unsanitized user input
```

## Documentation Diagnosis Commands (Phase 6)

### 4. Scan Documentation Health

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/doc_review.py" scan \
  --path docs/ --output <run-dir>/doc_health_report.json
```

### 5. Validate Links

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/doc_review.py" validate-links \
  --path docs/
```

### 6. Verify Against Source Code

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/doc_review.py" verify \
  --doc docs/agents/lifecycle.md --source src/agents/lifecycle.py
```

### 7. Documentation changes

Report stale indexes, broken links and obsolete claims with evidence. Do not run
update-indexes or auto-fix maintenance during analysis. Durable document edits
belong to a separately authorized knowledge operation.

---

## Comment Quality Commands (Antirez Standards)

### 9. Analyze Comment Quality

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/rewrite_comments.py" analyze \
  src/main.py --report
```

### 10. Scan Directory for Comment Issues

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/rewrite_comments.py" scan \
  src/ --recursive --issues-only
```

### 11. Generate Comment Health Report

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/rewrite_comments.py" report \
  src/ --output <run-dir>/comment_health.md
```

### 12. Comment remediation boundary

The utility library retains rewriting support for separately scoped callers.
Codebase Map uses only analyze, scan and report; it never applies rewrites, type edits
or source fixes. Record proposals in the run for the development/readability owner.

### 13. View Standards Reference

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/map-method/scripts/rewrite_comments.py" standards
```

### Documentation Maintenance (Phase 6)
1. Run scan first to understand current state
2. Fix links before content - broken links indicate structural issues
3. Verify against code before updating documentation
4. Update indexes last to reflect final state

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
3. Propose a change with the affected path and reason. Do not apply it in Codebase Map.
4. A separate authorized readability/development task performs and verifies edits.

## Documentation diagnosis

1. Scan health and validate links without fix flags.
2. Compare claims with current source and the declared requirement.
3. Report obsolete candidates, broken links and stale navigation with evidence.
4. Write results inside the run. Knowledge maintenance owns application and review.

## Team mode

### Team extensions

| Heading | File | Mode | Writer | After | Aggregation |
|---|---|---|---|---|---|
| Cross-Partition Risk Attribution | 05-risks.md | partition | partition-quality-worker | Failure Mode Analysis | Attribute risks with a side in this partition; use <other-partition>::<symbol>. |
| Cross-Partition Risk Attribution | 05-risks.md | consolidated | partition-synthesizer | Failure Mode Analysis | Collect attributed partition risks and deduplicate. |

### Partition worker

Attribute every cross-partition risk with a side in this partition. Phase 6 and Comment Quality remain conditional on depth and comments; neither authorizes applying changes.

### Consolidation

| File | Common heading | Rule |
|---|---|---|
| 05-risks.md | Anti-Patterns Found | Concatenate and sort globally by severity; rows cite partition, pattern, file:line and rationale. |
| 05-risks.md | Red Flags | Apply the same global severity ordering. |
| 05-risks.md | Technical Debt Inventory | Group by partition; debt is partition-local. |
| 05-risks.md | Failure Mode Analysis | Concatenate triggers and user-visible impacts. |
| 06-documentation.md | Documentation vs Code Accuracy | Concatenate partition discrepancies. |
| 06-documentation.md | Coverage Gaps | Public API gaps first, citing cross-partition exports; internal gaps follow. |
| 06-documentation.md | Broken References | Concatenate partition references. |
| 06-documentation.md | Comment Quality | Concatenate only with the comments flag; otherwise omit. |
