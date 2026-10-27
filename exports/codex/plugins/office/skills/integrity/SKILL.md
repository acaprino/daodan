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

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.
> This package registers lifecycle callbacks through `hooks/hooks.json` when the plugin is enabled. Execution requires the host's hook trust approval and Python 3 on PATH as `python`. The compiler does not approve hooks or modify host settings. Generated registration and subprocess checks do not prove installed-host execution.

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

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
