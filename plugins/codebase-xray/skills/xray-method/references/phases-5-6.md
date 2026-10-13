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

**Output file:** `$RUN_DIR/06-documentation.md`

```markdown
# Phase 6: Documentation Health

## Documentation vs Code Accuracy
[Mismatches between docs and reality]

## Coverage Gaps
[Undocumented public APIs, missing architecture docs]

## Broken References
[Dead links, non-existent file paths in docs]

## Comment Quality [if --comments]
[Comment audit with improvement suggestions]
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
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/doc_review.py" scan \
  --path docs/ --output <run-dir>/doc_health_report.json
```

### 5. Validate Links

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/doc_review.py" validate-links \
  --path docs/
```

### 6. Verify Against Source Code

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/doc_review.py" verify \
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
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/rewrite_comments.py" analyze \
  src/main.py --report
```

### 10. Scan Directory for Comment Issues

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/rewrite_comments.py" scan \
  src/ --recursive --issues-only
```

### 11. Generate Comment Health Report

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/rewrite_comments.py" report \
  src/ --output <run-dir>/comment_health.md
```

### 12. Comment remediation boundary

The utility library retains rewriting support for separately scoped callers.
X-ray uses only analyze, scan and report; it never applies rewrites, type edits
or source fixes. Record proposals in the run for the development/readability owner.

### 13. View Standards Reference

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/xray-method/scripts/rewrite_comments.py" standards
```

### Documentation Maintenance (Phase 6)
1. Run scan first to understand current state
2. Fix links before content - broken links indicate structural issues
3. Verify against code before updating documentation
4. Update indexes last to reflect final state
