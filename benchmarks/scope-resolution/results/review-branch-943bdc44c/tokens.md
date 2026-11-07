# Token count: reviews of commit 943bdc44c

Source: the Claude Code session transcripts, summed by `tokens.py` in this folder. A request occupies several transcript lines that repeat its usage: count one per request. An earlier version of this file summed every line and overstated output and new tokens; the numbers below replace it.

- **Coordinator context**: input + cache read + cache write of its last request, plus that request's output.
- **Output**: output tokens of all agents, thinking included.
- **New**: sum per request of input + cache write + output, for all agents. It counts cache rewrites, so it grows with waiting time.

| Review | Blind | Reviewers | Agents | Coordinator context | Output | New | Minutes | Defect |
|---|---|---|---|---|---|---|---|---|
| `light` (`../review-light-943bdc44c/`) | yes | composition of 26 members | 4 | 216,901 | 62,238 | 637,173 | 14 | found, reproduced |
| `branch`, Phase 1 with questions (this folder) | no | composition of 26 members | 10 | 366,414 | 190,890 | 1,579,281 | 36 | found, reproduced |
| `branch`, simplified Phase 1 (`../review-branch-943bdc44c-simplified/`) | no | 3 chosen roles | 6 | 328,842 | 175,680 | 1,170,141 | 30 | found, reproduced |
| `branch`, simplified Phase 1 (`../review-branch-943bdc44c-blind-stopped/`) | yes | 2 chosen roles | 4 so far | 292,043 | 89,013 | 769,896 | 14, then stopped | found by both reviewers; not reproduced |

**Not blind.** Two runs were executed as sub-agents of a session whose cached memory index said a seeded defect existed in this commit, and all their agents received that line. `leak_check.py` shows it in their `attachment` records. Rewriting the index on disk did not help, because a session caches it at start. Their costs stand; "found" does not count as a blind result. The `light` ran before that line existed.

**Blind run.** A fresh Claude Code process, with the index rewritten and the two `review-light-*` folders hidden from `git status` for the run. The seed words are absent from every agent's context records, and `01-context.md` does not name the defect. The system stopped the run for low memory during Lens 0: no Lens 1, no final report. The process was the coordinator, not a sub-agent as in the other runs.

**Where the cost is.** A `general-purpose` agent starts near 155K of context in this environment (skill list, tool schemas): Lens 3 ended at 160K after 3 requests. A role agent with a short tool list starts near 40K. So `light`, with its coordinator and its reviewer on `general-purpose`, carries that base twice; the chosen roles do not. The coordinator is the largest share in every `branch` run: it reads about 43K of method text and writes the phase files.

Limits: the fixture and the seed come from the same model family; the map run is older than the candidate; `search` through the MCP server reports a stale index (`binding differs: sqlite_version`); the commit subjects in `git status` mention this measurement.
