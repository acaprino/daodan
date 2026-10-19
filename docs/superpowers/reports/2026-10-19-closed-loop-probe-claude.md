# Closed-loop cycle probe on Claude Code, 2026-10-19

First live run of the task cycle shipped in marketplace 37.0.0, on an installed
host. It is workflow evidence, kept separate from the compiler tests: those prove
what the packages say, this records what one host did with them.

## Setup

| Item | Value |
|---|---|
| Host | Claude Code 2.1.303, headless (`claude -p`), `bypassPermissions`, model `claude-fable-5-1` |
| Profile | The user's production profile, updated to Daodan 37.0.0 at the user's request (project-lifecycle 1.5.0, senior-review 15.3.0, project-protocol 1.2.0) |
| Fixture | `D:\Projects\humanize-probe`, python-humanize at `785e5dc`, branch `probe/base`, push URL disabled |
| Baseline | 744 passed, 112 skipped, in the project's own `.venv` |
| Request | Upstream issue #379: `precisedelta()` drops the sign of negative timedeltas |
| Entry | `/project-lifecycle:change <request>`, no flags, project not initialized with `assess --init` |

The simulated user's answers (workspace, examples, zero rule, scope, rejected
alternatives, authorization) were written before the run. None was asked for.

## Outcome

| Measure | Value |
|---|---|
| Wall time | 40 min 14 s (07:44:43 to 08:24:57 UTC) |
| Cost reported by the host | 30.90 USD |
| Turns, tool calls | 81 turns, 221 tool calls (75 in the coordinator, 146 in workers) |
| Workers dispatched | 11: two test-writer, two fix workers, seven reviewers |
| Change | 72 insertions, 3 deletions in `src/humanize/time.py` and `tests/test_time.py`, uncommitted |
| Suite after | 760 passed, 112 skipped; doctests, ruff, black and mypy clean |

The behaviour is correct. An independent oracle compared base and candidate over
287 cases (seven option sets, fifteen magnitudes, timedelta and integer input):
every positive rendering is byte-identical to the base commit, every negative one
is `-` followed by the positive rendering, and a magnitude that renders as zero
stays unsigned.

## What worked

- The coordinator loaded the method and its per-phase units from the installed
  package and routed the bugfix through the repair unit.
- Workers were dispatched by qualified identity in isolated contexts, and the
  reproduction tests were red on the base before the fix was written.
- The run record was initialized, updated by revision and validated by the
  protocol helper; deliveries and gates were recorded.
- The review earned its place once. The premise auditor found that the first fix
  dropped the sign at `minimum_unit="years"` for integral values; a bounded second
  wave fixed it by deriving the sign from what the loop renders, which also removed
  a duplicated boundary rule three reviewers had flagged independently.
- A required provider that was disabled in the profile (`python-development`) was
  reported as a failed delivery and the result was marked not complete, instead of
  silently reducing coverage. It was noticed late, which is defect 6.

## Defects

1. **No question channel, no questions.** A headless session has no
   `AskUserQuestion` tool. The cycle neither chose nor asked the workspace mode,
   ran no interview and worked in place on `probe/base`. When the host offers no
   way to ask, the cycle must end the turn with its pending questions recorded in
   the run and resume them by `--run-id`, never pick a default.
2. **No proportionality.** Seven reviewers, among them security, Git history and
   abstraction, for a string-formatting fix inside one function; 40 minutes and
   30.90 USD. The October pilot showed the same shape (49 minutes, 28.53 USD,
   37 agents, about 40 lines). The method states proportionality in prose and the
   model, reading it, does everything. The tier has to be computed by a helper
   from measured signals before dispatch and enforced by the protocol.
3. **Global environment written.** The coordinator ran `pip install -e` and
   installed mypy, black and two stub packages into the global Python although the
   project had a `.venv`: eighteen distributions appeared in the global
   site-packages during the run. The preflight must find the project's
   interpreter, record it in the run and bind every command to it; installing
   outside the project needs an explicit grant.
4. **Scratch outside the run root.** Payloads and the plan were written to
   `.daodan-scratch/` at the project root, outside `.daodan/runs/<id>/`.
5. **Uninitialized project accepted silently.** With no Codebase Map and no
   decision index, the run proceeded and declared in its limits that the blind
   derivation did not run. `change` on a project that has never been initialized
   should run the missing parts of `assess --init` or stop and say so.
6. **A disabled provider found late.** `python-development` and `dependency-audit`
   were installed but disabled in the profile, so their roles were absent from the
   session. The run noticed only at review time and closed incomplete after 40
   minutes. The preflight must check that every required provider of the cycle
   exposes its roles and skills in the active session, and stop before any work
   with the exact enable or install command. Both were enabled after the probe.
7. **Shell quoting.** Seven of the twelve tool errors were heredocs the
   coordinator wrote with unbalanced quotes, and one more was `tar` given a
   Windows drive path. Helpers that take a JSON file argument, which the protocol
   already offers, avoid the first class.

## Cleanup after the probe

The eighteen distributions the run installed into the global Python were removed
on the user's decision; none had a dependent outside that set, and `pip check`
reports no broken requirement.

## Not a Daodan defect

The `codebase-map` MCP server reported `failed` at session start. Its cached `uv`
environment, created at 07:41 UTC, held 244 of the 611 files `pywin32` records:
`win32/lib`, `pywintypes.py` and the bootstrap module were missing, so the MCP SDK's
Windows import of `pywintypes` failed. Reinstalling that package
(`uv run --no-config --no-project --reinstall-package pywin32 --script ...`) repaired
it, and an `initialize` and `tools/list` handshake then listed 16 tools. The cause of
the partial install was not established.

## Next

Fix defects 1 to 6 as redesigns of their units, then rerun the same fixture from
`assess --init` in an interactive session so that the workspace question, the
interview and the integration phase are exercised too.
