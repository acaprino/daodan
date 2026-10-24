# React Performance Audit

Audit React effects, dataflow, rendering and bundle behavior. The coordinator prepares evidence, dispatches the declared reviewer and writes the native final report below. Canonical member roles own detection; do not copy their checklists into a second worker prompt.

Caller: `/daodan:check-health`. Senior-review supplies its own prepared scope and native format when it dispatches `react-development:react-performance-optimizer`; do not also run this method for that assignment.

## Inputs and scope

Use the caller's target, candidate/snapshot, requirements, run directory and permissions. A project uses full scope; a path uses that directory/file scope; a caller-resolved diff uses changeset scope with both sides, staged/unstaged work, untracked paths, removals and renames. Follow implicated callers, configuration and unchanged counterparts within admitted read scope. Do not infer that a preexisting content defect was introduced by the change.

Include components, stores, server/client entrypoints, relevant stylesheets, assets, bundler configuration and dependencies needed to trace the React mechanism. Visual design remains outside this method; a stylesheet affecting React-owned rendering work is evidence, not an automatic exclusion.

Keep a complete scoped inventory and the paths read in depth separately. Prioritize entrypoints and consequential paths, then finish the assigned checks or report the unexamined scope. Sampling or a read limit never proves full coverage. If no applicable source exists, record the inspected inventory and reason.

## Prepare evidence

Inspect relevant source and project configuration before dispatch. Collect project-configured React/JavaScript linting when available and authorized. Use existing local tooling, preserve the actual command, exit status, candidate and output, and report unavailable tooling rather than hiding errors or treating it as a clean run. Do not install tools implicitly.

Bind supplied performance profiles, budgets, compiler/linter output and product requirements to their source and conditions. Source reasoning is not a measured runtime result. Resolve the installed provider root and assigned knowledge once; an unknown target, missing mandatory input or stale binding remains a gap.

## Step 3: Run Review Agent

Dispatch `react-development:react-performance-optimizer` in its required isolated context through the host harness. Supply the full prepared scope, source/evidence paths, provider root, snapshot, requirements, working discipline, permissions and intermediate report path `<run>/react-review/worker-findings.md`. Use the actual rendered role, including each canonical member; loading a role as a skill is not dispatch.

The reviewer returns its findings and a delivered or failed outcome; it does not write the final report. Record that outcome before the report phase. A failed or missing delivery leaves the review incomplete and must be reported.

Supply the native report fields below as the assignment's common review conventions, once. Findings carry severity, current file:line evidence, the required behavior or budget, causal impact, counterevidence, numeric confidence and a concrete correction. Preserve rejected candidates, coverage/gaps, assigned knowledge usage and any required member_results in the one intermediate report. No automatic violation follows merely from an absent optimization, new API, compiler flag or preferred technique.

The coordinator verifies delivery and every assigned member before consolidation. Deduplicate the same cause without hiding independent failure modes. Keep all mandatory gaps open. Scores use evidenced category judgments and explicitly mark unassessed categories; do not derive a score from file counts or API adoption alone.

## Step 4: Generate Markdown Report

After the agent completes, create the `<run>/react-review/` directory and write `report.md`.

Order findings by severity, then file name.

**Output file:** `<run>/react-review/report.md`

```markdown
# React Performance Review: [date]

[Mode, scoped inventory, paths read in depth, runtime paths exercised and remaining gaps]

## Product Brief Context

[If a product brief was found, summarize performance budget and stack info. If not, note "No product brief found: reviewed against general best practices."]

## Scores

| Category | Score |
|----------|-------|
| Re-render Control | X/10 |
| State Management | X/10 |
| Bundle Optimization | X/10 |
| React 19 Adoption | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Files Audited

- `Component.tsx`, `Store.ts`, ...

---

## Critical & High Issues

### Re-render Control

#### `Store.ts`: [issue title]
- **Severity**: Critical
- **Issue**: [description]
- **Fix**: [fix instruction with code]
- [ ] Fixed

### State Management

#### `Context.tsx`: [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

### Bundle Optimization

#### `index.ts`: [issue title]
- **Severity**: High
- **Issue**: [description]
- **Fix**: [fix instruction]
- [ ] Fixed

---

## Medium & Low Issues

[Same format as above]

---

## What's Working Well

- [positive observation]
- [another positive]

---

## Action Plan

1. [ ] [top priority fix, from critical findings]
2. [ ] [second priority]
3. [ ] [third priority]
4. [ ] [fourth priority]
5. [ ] [fifth priority]
```

**Print a short summary** in the conversation:

```
React performance review complete.

Report: <run>/react-review/report.md

Overall Score: X/10
Re-renders: X/10 | State: X/10 | Bundle: X/10 | React 19: X/10

Critical: X | High: X | Medium: X | Low: X

Top 3 issues:
1. [critical issue summary]
2. [high issue summary]
3. [high issue summary]
```

When Critical findings exist, end the summary with the strict line:
```
STRICT MODE: X critical React performance issues found. Recommend addressing before shipping.
```
