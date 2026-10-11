<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
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

# Code-review output templates (Steps 5, 5b, 6)

Full output structure for `/senior-review:code-review`: the final review template,
the CLAUDE.md alignment check, and the PR auto-comment flow. Loaded on demand by
the command when it reaches Step 5.

## Step 5: Final Review Output

After validation completes, synthesize everything into the final structured review:

```
## Code Review -- [PR title or branch name]

### Review Scope
- **Scope:** [diff source -- e.g., origin/main..HEAD, uncommitted changes, PR #42]
- **Intent:** [2-3 line intent summary from Step 1b]
- **Reviewers:** code-auditor, security-auditor, dead-code, [+ conditional agents with justification]
- Files reviewed: [N]
- Lines changed: +X / -Y
- CLAUDE.md compliance: [checked / not found]
- Verification: X of Y findings verified (4-lens panel), Z false positives, W contested, V premise-refuted, U premise-contested{cost_guard_note}

### Overall Score: X/10 (confidence: X%)

### Critical & High Findings
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|
| 1 | Critical | ...       | ...     | 95%        | ... |

### Medium & Low Findings
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### Dead Code & Unused Parameters
| # | Source | Severity | File:Line | Finding | Confidence | Action |
|---|--------|----------|-----------|---------|------------|--------|

### Failure Flow & Resilience
| # | Severity | File:Line | Scenario | Confidence | Fix |
|---|----------|-----------|----------|------------|-----|

### UI Race Conditions (if applicable)
| # | Severity | File:Line | Timeline | Confidence | Fix |
|---|----------|-----------|----------|------------|-----|

### Platform Engineering (if applicable)
| # | Severity | File:Line | Rule | Confidence | Fix |
|---|----------|-----------|------|------------|-----|

### Git History & Churn (if applicable)
| # | Severity | File:Line | Pattern | Commits Referenced | Confidence |
|---|----------|-----------|---------|-------------------|------------|

### Testing Issues (if applicable)
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### API Contract Issues (if applicable)
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### Data Migration Issues (if applicable)
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### React Performance (if applicable)
| # | Severity | File:Line | Finding | Confidence | Fix |
|---|----------|-----------|---------|------------|-----|

### Abstraction & Reuse (if applicable)
| # | Class | Severity | New Code | Prior Art | Difference | Direction |
|---|-------|----------|----------|-----------|------------|-----------|

Second occurrences (R4), listed without flagging: [one line each, or "none"]

### Coverage
- Suppressed: [N] findings below 0.50 confidence
- Deduplicated: [N] cross-agent duplicates merged
- Residual risks: [risks noticed but not confirmed as findings]
- Testing gaps: [missing test coverage identified]

### Coverage Gaps
[paste the ## Coverage Gaps list from the completeness critic, or "None identified"]

### Pattern Consistency
- [pattern deviations found, or "Changes follow established patterns"]

### CLAUDE.md Compliance
- [list any violations, or "All changes comply with project conventions"]

### Pre-existing Issues (does not count toward verdict)
| # | File:Line | Issue | Reviewer |
|---|-----------|-------|----------|
[issues in unchanged code unrelated to the diff, or "None"]

---

> **Verdict:** [Ready to merge / Ready with fixes / Not ready]
>
> **Reasoning:** [1-2 sentences explaining why]
>
> **Fix order:** [severity-ordered list of what to fix first, if applicable]
```

Where `{cost_guard_note}` is `, narrowed to stakes+band (N unverified)` when the cost guard fired, else empty.

If `--strict` and there are Critical findings:

```
STRICT MODE: Critical issues found. Not ready to merge.
```

## Step 5b: CLAUDE.md Alignment Check

After producing the review output, check if findings suggest the project's `CLAUDE.md` is stale:

1. Read `CLAUDE.md` (if it exists -- it was already read in Step 2)
2. Cross-reference review findings with documented conventions, structure, and workflows
3. If any documented information is outdated or missing, add a `### CLAUDE.md Staleness` section to the review output noting what needs updating

---

## Step 6: Auto-Comment on PR (if --auto-comment)

If `--auto-comment` flag is set and reviewing a PR:

Post only **CRITICAL and HIGH severity** findings as inline PR comments. Do NOT auto-comment MEDIUM or LOW findings -- include those only in the summary report. This prevents comment spam and focuses reviewer attention on what matters.

Write each comment body to a temp file first, then use `-F` to avoid shell injection from LLM-generated content.

### Committable Suggestions

For each inline comment, decide whether to include a committable suggestion:

- **Include suggestion** when the fix is small and self-contained (< 6 lines changed, single location, committing the suggestion fully resolves the issue)
- **No suggestion** when the fix is large (6+ lines), structural, spans multiple locations, or committing the suggestion alone would not fully fix the problem
- **Never** post a committable suggestion unless committing it fixes the issue entirely -- partial suggestions that require follow-up steps are worse than no suggestion

### Inline comment format

```bash
mkdir -p .code-review-tmp

# Without committable suggestion (large or multi-location fix)
cat > .code-review-tmp/temp_inline_comment.md << 'COMMENT_EOF'
**[Severity]** -- [finding summary]

[concrete fix recommendation describing what to change]
COMMENT_EOF

# With committable suggestion (small, self-contained fix)
cat > .code-review-tmp/temp_inline_comment.md << 'COMMENT_EOF'
**[Severity]** -- [finding summary]

```suggestion
[corrected code that fully fixes the issue when committed]
```
COMMENT_EOF

# Post as inline PR comment using -F (file input)
gh api repos/{owner}/{repo}/pulls/{number}/comments \
  -F body=@.code-review-tmp/temp_inline_comment.md \
  -f path="[file]" \
  -f line=[line] \
  -f commit_id="$(gh pr view {number} --json headRefOid --jq '.headRefOid')"
```

Post the overall summary as a regular PR comment (also via temp file):

```bash
mkdir -p .code-review-tmp

cat > .code-review-tmp/temp_summary_comment.md << 'SUMMARY_EOF'
## Automated Code Review

**Overall Score: X/10**

[summary of critical/high findings]

[top 3 recommended actions]

---
*Reviewed by: code-auditor, security-auditor, dead-code-and-lint-detector, ui-race-auditor, git-history-analyzer | Findings verified by 4-lens panel*
SUMMARY_EOF

gh pr comment {number} -F .code-review-tmp/temp_summary_comment.md
```

---
