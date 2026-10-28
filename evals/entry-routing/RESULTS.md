# Chat entry routing: measured results

Date: 2026-10-28. Run against commit `b529e1e47` (before the G-1 rebuild; the
rebuild and the kernel declarations it packages are the code under test, not
anything in the eval harness itself).

## Method

All 65 cases of `cases.json` run twice through `claude -p --restricted` (which
ignores the real user/project settings, so the real installation is never
touched), isolated per case in a throwaway working directory, with
`--disallowedTools Bash,PowerShell,Edit,Write,NotebookEdit,WebFetch,WebSearch`
so an accidentally-invoked workflow cannot act on anything real. The 30
routing-capable plugin packages were loaded via repeated `--plugin-dir`:

- **with-hooks**: `exports/claude/plugins/<name>` as committed at `b529e1e47`
  (after T1-T11 of this run).
- **without-hooks**: the same 30 packages extracted from `git archive
  a1951b694` (the commit immediately before any routing code existed).

Detection: the first `Skill` tool call in the session's `stream-json`
transcript. A case counts as a hit when its name matches `expected_entry`
(leading `/` ignored). This is a real tool invocation, not a self-report.

## Result

| Condition | task+vertical (of 50) | non-task false positives (of 15) | cost |
|---|---|---|---|
| with hooks | 38 (76%) | 0 | $15.57 |
| without hooks | 37 (74%) | 0 | $15.19 |

**7 of 65 cases flip direction between the two runs** (4 favour with-hooks, 3
favour without-hooks). With one trial per condition per case, this is noise,
not a measured effect: **the S-6 target (≥85%, and better than without) is not
met, and no reliable improvement from the hook is demonstrated at this plugin
count.** Non-task precision is excellent in both conditions: zero false
triggers across 15 cases, twice.

4 of the 11 raw misses are defects in `cases.json` itself, not routing
failures: `vert-003`/`vert-004` expect the bare skill name (`ibkr`, `mt5`)
where the model correctly invoked the real workflow (`ibkr-audit`,
`mt5-audit`); `vert-009` expects the specialist (`project-delivery:adr-method`)
where the model correctly used the project's own front door
(`daodan:record-decision`), per CLAUDE.md's rule that specialists have no
command of their own. The genuine misses (`task-015`, `task-025`, `task-027`,
`task-031`, `task-033`, `task-039`, `task-040`, `vert-002`, `vert-006`) are on
clear, unambiguous prompts; the model answered in free text instead of
invoking the skill.

## Why the target was not reached here

This is not evidence the hook is useless. The mechanism it targets is
budget-based description dropping under real crowding (official Claude Code
docs: the listing always keeps every name, but drops descriptions once the
listing exceeds roughly 1% of the context window). 30 plugins' worth of
descriptions do not reach that budget, so the native listing alone was
already sufficient in both conditions here — the originating anecdote (6 of
31 `daodan` commands visible) came from a ~250-skill real installation, which
this harness deliberately does not load, because doing so would mean reading
most of the user's real plugin cache into the "disposable" probe. **A
measurement that would actually settle this needs the real, crowded
installation**, which means it is a live post-install check, not something a
disposable probe can certify in advance.

## Host delivery checks (P-1 to P-5)

- **P-1/P-2 (Claude)**: not run as a separate check; superseded by the full
  run above, which demonstrates both that `/daodan:` commands are invocable
  and that the hook's `additionalContext` reaches the model (every hit in the
  with-hooks condition is evidence of this).
- **P-3 (Codex)**: attempted. `CODEX_HOME` isolates Codex's config directory
  cleanly (confirmed: `codex doctor` reports a fresh, credential-less home);
  copying only `auth.json` into that isolated home and running `codex plugin
  marketplace add`/`codex plugin add` installed the plugin into the isolated
  cache without touching the real `~/.codex`. `codex exec` then failed with
  `workspace routing discovery failed` after 5 reconnect attempts and a
  WebSocket-to-HTTPS fallback, before producing any assistant output. This is
  a backend/workspace-registration error, not a hook-rendering error; it did
  not get far enough to test hook delivery. **Codex stays "generated, not
  probed."**
- **P-4 (OpenCode)**: attempted. OpenCode's `plugin add` installs only to the
  *global* configuration (its own `--help` says so), which this run will not
  touch. A project-local `opencode.json` with `"plugin": ["file:<path>"]` in a
  throwaway directory was tried instead, so no global state would be touched
  either way. `opencode run --standalone --format json` then hung for the
  full 90-second timeout with zero output, not even a startup log line. Not
  investigated further within this run's budget. **OpenCode stays "generated,
  not probed" for both the general hook mechanism check this spec's P-4 names
  and the routing-specific slot docs/hosts.md already flagged.**
- **P-5 (Copilot)**: not attempted. The GitHub Copilot CLI is installed but
  broken on this machine (`no platform package found`), unrelated to this
  work. **Copilot stays unprobed**, as it already was.

## What this changes

- The Claude layout decision (T12, "render workflows as skills instead of
  commands") stays skipped: this run never reproduced the original 6-of-31
  absence (every `/daodan:` command was invocable throughout, in both
  conditions), so there is no evidence calling for that change.
- `docs/hosts.md` is updated to cite this file instead of asserting an
  unmeasured target.
