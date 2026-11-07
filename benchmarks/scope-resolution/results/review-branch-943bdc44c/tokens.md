# Token count: review `branch` vs `light` on commit 943bdc44c

Source: the Claude Code session transcripts (`~/.claude/projects/D--Projects-daodan/<session>/subagents/*.jsonl`), summed by `tokens.py` in this folder (`python -I tokens.py SESSION ROOT_AGENT_PREFIX`). Both reviews were run by an Opus coordinator agent that dispatched its workers as sub-agents.

Formulas:

- **final context** of an agent: `input + cache_read + cache_creation` of its last turn, plus that turn's output. The 217K quoted for the `light` is this number for its coordinator.
- **new tokens**: sum over every turn of `input + cache_creation + output` (tokens processed for the first time; cache reads excluded). Cache reads are the bulk of the bill in both runs and are not compared here.

| Review | Agents | Coordinator turns | Coordinator final context | New tokens, all agents | Output tokens, all agents |
|---|---|---|---|---|---|
| `light` (session c0d0b1dd, agent a92b4ccf) | 4: coordinator, job-01, Lens 0, Lens 1 | 94 | 216,901 | 1,199,929 | 116,595 |
| `branch` (session ffc3cc44, agent branch-review-coordinator) | 10: coordinator, job-01, Lens 0-3 for two findings | 181 | 366,414 | 3,239,815 | 400,957 |

Per agent, `branch`:

| Agent | Turns | Output | New tokens | Max context |
|---|---|---|---|---|
| coordinator (Phase 0, 1, 3, 4, 5 in its own context) | 181 | 251,495 | 1,529,727 | 365,070 |
| job-01 code-auditor discovery | 40 | 61,322 | 610,193 | 222,593 |
| Lens 0 J01-F1 / J01-F2 (premise-auditor) | 25 / 14 | 18,052 / 25,480 | 107,784 / 89,322 | 45,934 / 41,919 |
| Lens 1 J01-F1 / J01-F2 | 15 / 12 | 10,161 / 12,657 | 334,151 / 114,357 | 170,469 / 167,629 |
| Lens 2 J01-F1 / J01-F2 | 7 / 7 | 6,246 / 6,836 | 103,707 / 103,713 | 164,601 / 164,414 |
| Lens 3 J01-F1 / J01-F2 | 5 / 7 | 3,646 / 5,062 | 92,698 / 154,163 | 160,293 / 160,322 |

Per agent, `light`:

| Agent | Turns | Output | New tokens | Max context |
|---|---|---|---|---|
| coordinator | 94 | 59,500 | 662,546 | 215,677 |
| job-01 code-auditor | 42 | 41,978 | 180,859 | 175,272 |
| Lens 0 F1 (premise-auditor) | 13 | 8,345 | 78,757 | 35,822 |
| Lens 1 F1 | 10 | 6,772 | 277,767 | 142,057 |

Where the difference comes from: the `branch` coordinator runs Phase 0-1 (scope, evidence pack, context, questions, selection) and the consolidation in its own context (251K output tokens against 60K), and the team-review panel runs four lenses per finding on two findings (eight workers) where the `light` runs two lenses on one finding. The Codebase Map MCP tools were not exposed to the coordinator agent, which called the same backend through `python -B` scripts: same evidence, more tool-call text.
