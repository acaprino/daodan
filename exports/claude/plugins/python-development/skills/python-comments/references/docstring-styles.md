<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
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

# Python Docstring Styles

Three major styles: Google, NumPy, Sphinx/reST. Pick one per project, use it consistently. With type hints, docstrings document **semantics** -- not types.

## When to use

Choosing a docstring convention for a new project, or auditing an existing one for consistency. For comment patterns inside function bodies (the antirez 9-type taxonomy), see `taxonomy.md`.

## Decision table (memorize this)

| Project type | Recommended | Rationale |
|--------------|-------------|-----------|
| Web app / API | **Google** | Clean, readable, widely understood |
| Data science / ML | **NumPy** | Matches pandas / numpy / scikit-learn conventions |
| Library with Sphinx docs | **Sphinx/reST** | Native Sphinx rendering, `:param:` directives |
| Open source (general) | **Google** | Lowest barrier for contributors |
| Existing project | **Match existing** | Consistency > preference |

**Rule**: if the project already has docstrings, match their style. If starting fresh, default to Google.

## Gotchas

- **With type hints, document SEMANTICS not types.** `transactions (list[Transaction]): A list of Transaction objects` duplicates the type hint and rots when types change. Write *what they mean*, not *what they are*.
- **One-line docstrings only for trivially-named functions.** `def is_expired(token): """Check if the token has passed its expiry time."""` is fine. Anything more than a single sentence of explanation = use the multi-line format.
- **First line is imperative mood, ends with a period.** "Send a notification..." not "Sends a notification..." or "Sending a notification". `pydocstyle` D401/D400 flag both.
- **Don't start with "This function..."** -- redundant. The first line is implicitly the function description.
- **`Returns:` documents semantics**, not type. The type hint already says `-> NotificationResult`. The docstring says *what the result means* and *what the status values mean*.
- **`Raises:` is for exceptions YOU intentionally raise**, not every possible exception. `KeyError` from a dict access deep in the call chain doesn't go here unless you re-raise it deliberately.
- **`Examples:` (Google) / `Examples` (NumPy) / `.. code-block::` (Sphinx)** -- doctest-runnable examples are gold. They double as living docs and test coverage.

## The three styles, side-by-side

### Google (recommended default)

```python
def send_notification(user, message, channel="email", priority=0):
    """Send a notification to a user through the specified channel.

    Validates the channel, formats the message according to channel
    requirements, and dispatches asynchronously. Falls back to email
    if the preferred channel is unavailable.

    Args:
        user: Target user. Must have a verified contact for the channel.
        message: Notification body. Markdown for email; plain text for SMS/push.
        channel: One of "email", "sms", "push".
        priority: 0=normal (batched), 1=high, 2=urgent (skip batching).

    Returns:
        Result object with delivery status and message ID.
        Status is "queued" for normal priority, "sent" for high/urgent.

    Raises:
        ChannelUnavailableError: If channel is down and no fallback exists.
        InvalidRecipientError: If user has no verified contact for channel.

    Example:
        >>> result = send_notification(user, "Deploy complete", channel="push")
        >>> result.status
        'queued'
    """
```

### NumPy

```python
"""Send a notification to a user through the specified channel.

Parameters
----------
user : User
    Target user. Must have a verified contact for the channel.
message : str
    Notification body. Markdown for email; plain text for SMS/push.
channel : str, default "email"
    One of "email", "sms", "push".
priority : int, default 0
    0=normal, 1=high, 2=urgent.

Returns
-------
NotificationResult
    Status is "queued" for normal, "sent" for high/urgent.

Raises
------
ChannelUnavailableError
    If channel is down and no fallback exists.

Examples
--------
>>> send_notification(user, "Deploy complete", channel="push").status
'queued'
"""
```

### Sphinx/reST

```python
"""Send a notification to a user through the specified channel.

:param user: Target user.
:param message: Notification body.
:param channel: One of "email", "sms", "push".
:param priority: 0=normal, 1=high, 2=urgent.
:returns: Result object with delivery status.
:rtype: NotificationResult
:raises ChannelUnavailableError: If channel is down.
"""
```

## Tooling

### pydocstyle (legacy, but still common)

```bash
pip install pydocstyle
pydocstyle --convention=google src/      # or numpy
pydocstyle --add-ignore=D100,D104 src/   # ignore module/__init__ docstring rules
```

Common codes: `D100` (missing module docstring), `D101` (missing class), `D102` (missing method), `D103` (missing function), `D104` (missing `__init__.py`), `D400` (first line should end with period), `D401` (first line should be imperative).

### interrogate (coverage as a percentage)

```bash
pip install interrogate
interrogate -v src/
interrogate --fail-under=80 src/         # CI gate
interrogate --generate-badge docs/
```

`pyproject.toml`:
```toml
[tool.interrogate]
ignore-init-method = true
ignore-init-module = true
ignore-magic = true
fail-under = 80
verbose = 1
```

### ruff (the modern one-stop)

```toml
[tool.ruff.lint]
select = ["D"]                           # pydocstyle rules

[tool.ruff.lint.pydocstyle]
convention = "google"                    # or "numpy"
```

ruff's `D` rule set replaces pydocstyle entirely and is much faster.

## Official docs

- PEP 257 (Docstring Conventions): https://peps.python.org/pep-0257/
- Google Python Style Guide -- docstrings: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings
- NumPy Style: https://numpydoc.readthedocs.io/en/latest/format.html
- Sphinx (reST in docstrings): https://www.sphinx-doc.org/en/master/usage/domains/python.html
- pydocstyle: https://www.pydocstyle.org/
- interrogate: https://interrogate.readthedocs.io/
- ruff `D` rules: https://docs.astral.sh/ruff/rules/#pydocstyle-d

## Related

- `taxonomy.md` -- the antirez 9-type comment classification (LOCAL IP, do not slim)
- `examples/write-mode-examples.md` -- worked examples per type
- `examples/audit-mode-examples.md` -- pedagogical examples for the audit mode
