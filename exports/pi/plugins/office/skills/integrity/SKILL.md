---
name: integrity
description: >
  Verify the integrity of a Word, PowerPoint or Excel file with static rules, then
  repair what can be repaired on a separate candidate. TRIGGER WHEN: checking a
  DOCX, PPTX or XLSX for broken links, formula errors, missing alternative text,
  inconsistent formulas, empty placeholders or other defects, or fixing them.
  DO NOT TRIGGER WHEN: creating a new document, deck or workbook (use the office
  document, presentation or workbook workflows).
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.
> This package retains its lifecycle callback scripts, but this host has no declared native hook registration. Use the method's explicit workflow checkpoints; automatic interception outside those workflows is unavailable.

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

# Office file integrity

Read `references/rules.md` for the rules, severities and fix classes.

## Verify

Run the read-only checker on the exact file and keep its JSON report:

```text
python "<plugin-root>/skills/integrity/scripts/office_verify.py" INPUT
```

Exit code 0 means no error finding, 1 an error finding or an unreadable package,
2 an unsupported or missing file. The report records the file's SHA-256, verdict
(`pass`, `warnings` or `fail`), counts per severity, findings per rule and the
checks it did not perform. Findings beyond `--max-per-rule` are counted, not listed.

When OfficeCLI is installed the checker also runs its schema validation and
issue scan and says so in `checkers`; otherwise schema validity stays in
`not_checked`. Static rules do not see layout or calculation. Cover the
`not_checked` items with the format's engine when it is available: render pages or slides and inspect them
for overflow and overlap, and run `office:gridcraft`'s `check` for recalculation.
Report any uncovered item as unverified. A `pass` is never a visual or calculation verdict.

Present findings grouped by severity, most severe first, each with its location
and fix class. Keep the source untouched.

## Fix

Repair only on a new candidate path; never overwrite the source. Load the format's
engine skill (`office:wordcraft`, `office:deckcraft` or `office:gridcraft`) and
follow its preservation steps before the first change.

- `safe`: apply.
- `content`: write content that only describes what is already present, such as
  alternative text read from the actual image or a title taken from the slide's
  own text. Never invent facts.
- `review`: apply only when the user's request names that change; otherwise list
  it with the proposed edit.
- `none`: report.

After the changes, run the checker on the candidate and compare the two reports.
Every fixed finding must be gone and no new finding may appear; otherwise discard
the candidate or the failing change. Run the format's inspector `compare` (or
`coverage` after structural edits) between source and candidate and account for
every delta. Deliver the candidate with both reports, the applied changes, the
findings left open with their reasons, and the checks that remained unverified.
