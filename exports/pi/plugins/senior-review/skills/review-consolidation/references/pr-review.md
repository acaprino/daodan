<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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

## Phase 3: Generate PR Description

Using the analysis from Phase 1 and all accounted reviewer findings from Phase 2,
including selected stack specialists, generate a complete PR description after
the canonical evidence/provenance verification. Include selected dimensions,
code-based skips and missing evidence so the description states its coverage.

### PR Description Template

```markdown
## Summary

[2-3 sentence executive summary of what this PR does and why]

**Risk Level**: [Low/Medium/High/Critical] | **Review Time**: ~[estimate] min | **Lines**: +[X] / -[Y]

## What Changed

### [Category Icon] [Category] Changes
- [status]: `filename` -- [brief description of change]

[Repeat for each category with changes]

## Why These Changes

[Extract motivation from commit messages and code context -- the business reason]

## Type of Change

- [ ] New feature
- [ ] Bug fix
- [ ] Refactoring
- [ ] Dependency update
- [ ] Configuration change
- [ ] Documentation

## How to Test

1. [Step-by-step testing instructions]
2. [Include specific commands to run]
3. [Expected outcomes]

## Risk Assessment

| Factor | Level | Details |
|--------|-------|---------|
| Size | [Low/Med/High] | [X files, Y lines] |
| Complexity | [Low/Med/High] | [description] |
| Test Coverage | [Low/Med/High] | [description] |
| Dependencies | [Low/Med/High] | [description] |
| Security | [Low/Med/High] | [description] |

[Include verified security findings from the selected reviewer, if any; an
unselected or failed security dimension is not a clean security result.]

[Include verified stack-specialist findings and their relevant risk factors]

## Review Coverage

[Selected dimensions, code-based skips, failed deliveries and unavailable evidence]

## Hygiene

[Include verified hygiene findings from the selected canonical owner. One row
per finding with its path and owning cleanup phase. Omit an empty section and
record unselected, failed or incomplete hygiene coverage under Review Coverage.]

## Breaking Changes

[List any breaking changes, or "None"]

## Review Checklist

### General
- [ ] Self-review completed
- [ ] No debugging code left
- [ ] No sensitive data exposed

### Code Quality
[Context-aware items based on file types changed]

### Testing
[Items based on whether tests were added/modified]

### Security
[Items based on security agent findings]
```

### PR Split Suggestions (if applicable)

If `--split-check` flag is set or PR exceeds 500 lines, include:

```markdown
## PR Split Suggestion

This PR is [X] lines across [Y] files. Consider splitting into:

1. **[logical unit 1]**: [files], [purpose]
2. **[logical unit 2]**: [files], [purpose]

This improves review quality and reduces merge conflict risk.
```

---

## Phase 4: Present & Optionally Create PR

### Always: Present the description

Save the complete native description to the caller's declared report path, or
`pr-description.md` in the prepared owned output root. Use this same Markdown for
presentation and any authorized PR creation. Keep risk, coverage, evidence, native
checklists and unknown states intact. Any required approval still receives the
complete native description.

Show the complete PR description in the conversation and ask:

```
PR description generated.

Risk Level: [level]
Files: [count] | Lines: +[X]/-[Y]

1. Create PR now (pushes branch and creates PR via gh)
2. Copy description only (I'll create the PR manually)
3. Revise -- adjust the description first
```

### If `--create` flag or user chooses option 1:

First check if branch is pushed:
```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null
```

If not pushed, ask:
```
Branch [name] hasn't been pushed to remote. Push and create PR?
```

Then create the PR:
```bash
git push -u origin [branch-name]
gh pr create --base [base-branch] --title "[title]" --body "[description]"
```

Present the PR URL when done.

### CLAUDE.md Alignment Check

After generating the PR description, check if changes suggest the project's `CLAUDE.md` needs updating:

1. Read `CLAUDE.md` (if it exists)
2. Cross-reference changed files with documented conventions, structure, and workflows
3. If `CLAUDE.md` references outdated information, add a note in the PR description under a `## CLAUDE.md Updates Needed` section

Save final native updates to the same description path, then apply this skill's
`Optional human view` contract. The final writer loads
`report-rendering:report-renderer` when warranted and renders its same-stem HTML
with `--profile review` in the prepared owned output root. The derived view grants
no publication authorization; an explicitly requested HTML deliverable remains
open if rendering fails.

---

### If `--strict-mode` and Critical risk:

```
STRICT MODE: Critical risk factors detected. Recommend splitting or addressing security findings before creating PR.
```
