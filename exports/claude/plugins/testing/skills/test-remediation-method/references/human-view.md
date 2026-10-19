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

# Optional human view

Only the coordinator loads this reference when the user requests HTML, or the
completed audit/consolidation report substantially benefits from navigation,
comparison or table filtering. Workers deliver native findings, not presentation.

Load the `report-rendering:report-renderer` skill and resolve its shipped helper through
that registered skill. Render the final native Markdown once with `--profile review`.
Audit uses the task-selected `TEST_AUDIT.md` after any accepted fix and
its final refresh; consolidation uses Step 8's existing coordinator report or
Step 2's final dry-run inventory report, preserving its unexecuted work and status.
Never render `work.json` or `result.json` as Markdown or create another state ledger.

Bind `--input` to that exact final Markdown path. Bind `--output` to
`<output-root>/<report-stem>.html` and `--root` to the same dedicated, exact
task-owned `<output-root>` inside the project. Verify that root's ownership through
the prepared protocol run. A shared target directory containing `TEST_AUDIT.md`
does not become owned by the audit: choose the run's dedicated output directory
instead. Keep the canonical audit and owned `findings.md` at their native paths;
the helper rebases relative evidence links when rendering in a different directory.

Set `$REPORT_MD` to the exact native source, `$OUTPUT_ROOT` to the verified
dedicated output directory and `$REPORT_HTML` to its same-stem HTML path inside
that directory. Run:

```bash
python "<resolved-report-renderer-helper>" --input "$REPORT_MD" --output "$REPORT_HTML" --profile review --root "$OUTPUT_ROOT"
```

Preserve classifications, inventory acceptance, protected behaviors and failure
modes, oracle/bugfix provenance, quarantine ledger references, evidence, coverage
and gates. Retain `--no-run`, stale, unavailable and unknown measurements without
turning them into zero or a pass. Filters and checkboxes affect only the view;
they never accept categories, retire tests, change dispositions or satisfy gates.

Verify helper success and the complete embedded source/hash, required sections,
evidence and uncertainty through the renderer's structural checks. A browser is
optional; state when interactions were not exercised. Link HTML beside native
Markdown through the existing delivery envelope. Rendering adds no authority,
mutation, behavioral verification or measured token saving.

Diagnose and recover render failures while preserving native output. If requested
HTML is failed or missing, leave that deliverable open and do not close the run.
An unrequested optional view failure is reported without changing the native
audit/consolidation result. Apply normal completion only after required gates and
every requested deliverable are verified.
