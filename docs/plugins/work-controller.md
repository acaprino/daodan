# Work controller

A dependency-free leaf owns the work contract (`contracts/work.toml`, which also
holds the project-result envelope), run identities, exact file snapshots, state
transitions, delivery accounting, candidate gates, questions to the user and
recovery obligations. It does not define domain findings or run Git rollback.
Its isolated-worker role is the neutral task, owned-scope and report contract
for explicitly declared generic workers; the coordinator's brief carries the
working discipline.

Consumers declare `work-controller/contracts/work.toml` in `shared_schemas`
rather than copying its fields. The senior-review schemas remain review-domain
payloads.

Load `work-controller:work-record`. Its stdlib `run_state.py` keeps every record
and the agenda in `.daodan/` of the main checkout, behind one write lock and
atomic replacement. Writes name the session, and a task is written only by the
session holding it. `update` needs the expected revision and refuses a stale
one; a refused write changes nothing, so a draft plan is checked by writing it.
`snapshot` prints the current candidate digest and head for a gate;
`validate --current` rejects changed inputs, and `--result` checks the result
envelope against the exact revision and candidate.

Declare expected deliveries and required gates. Gates, grants, rulings and
reviews are append-only. A delivered worker identifies an existing run-owned
report. Completion requires every delivery, current candidate-bound successful
gates, closed phases, no interruption and no open question. Result validation
correlates the envelope with the record; it does not prove the payload's
semantic truth.

Baseline, pre-phase snapshot/SHA and exclusive workspace ownership precede
mutation. Recovery preserves prior successful phases and foreign files. Remote
checks name the exact candidate revision and job attempt and require the inputs
to match that commit. Published changes need an authorized revert.

Questions change only through `ask` and `answer`. `ask` records a question before
it is asked and returns the open question of the same phase that already asks it;
whether an earlier answer still applies is the coordinator's judgment. `answer`
records the user's own words and their source and never changes an answer,
because a changed answer is a new question. Both print only the question they
touched. A wave task that needs an answer lists `question:<id>` in its `consumes`
and waits; `answer` names the tasks it unblocks and `resume` the tasks still
waiting. A withdrawn question closes without unblocking anyone. The shape of a
question, in `references/questions.md`, is shared by every method that asks.
Decision maps and tickets belong to the process runtime below. They do not
replace the work record's human answers or completion gates. Selective revision
of work after a changed decision remains a separate capability contract.

## Process runtime

The complete existing process engine has one source owner in this plugin:
`skills/work-record/scripts/work_controller/`, including its console assets.
`skills/work-record/scripts/controller.py` launches the CLI and read-only MCP
interface. There is no separate engine repository or package installation.
The isolated launcher supplies Python 3.11 or newer and the restricted PyYAML
runtime dependency; the marketplace compiler remains standard-library only.

The runtime admits immutable YAML graphs, orders their dependencies through
`graphlib`, records attempts and events in SQLite, stores immutable artifacts by
content digest, and supplies sequential command execution and agent handoff
packets. Decision maps have acyclic blockers and run-bound execution tickets.
The authenticated loopback console and stdio MCP share bounded read-only views.
Commands use argv without a shell; a declared write set is not operating-system
confinement.

The default process store is `.daodan/processes` of the main checkout. Existing
`daodan/work/v1` records, their agenda and evidence remain in place. An explicit
record/process binding joins graph progress to the existing grants, deliveries,
questions and candidate-bound gates; terminal graph success alone cannot close
a delivery task. Legacy state requires an explicit home rather than a silent
choice between competing roots. New definitions use
`work-controller/process/v1`; the `process-controller/process/v1` and
`deadly-brain/process/v1` inputs retain their original identities and digests.

Source transfer does not prove installed-host dispatch, observed model selection,
parallel or distributed execution, bounded loops, selective replan or semantic
memory. Model selection and pricing remain with `model-routing@daodan`.
Preserve the engine's license and provenance when renaming public identifiers.

Version 2.0.0 removed `plan-check` (write the draft; a refused write changes
nothing) and the custom `--out` root. A run that 1.x recorded under a custom root
stays on disk as plain files and is finished with work-controller 1.x.

Helpers mechanically confine their own writes. Other agent tools remain subject
to prompt obligations until an installed runtime enforcement mechanism is proved.

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `1.0.0`. **Source:** [plugin.toml](<../../plugins/work-controller/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [work-controller](<work-controller.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `repository.write`, `shell.execute`, `mcp.servers`.
**Optional capabilities:** `network.fetch`.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `work-controller:work-record` | Shared working discipline, run identity, snapshots, delivery/verification accounting, authorization continuity, user questions and phase recovery. Load before authoring components/tools, briefing workers, asking users, recording, resuming or closing project interventions. | [work-record](<../../plugins/work-controller/skills/work-record/SKILL.md>) |
| Role | `work-controller:isolated-worker` | Isolated task worker for a coordinator-owned method. Executes the supplied concrete task within its owned scope and returns an actual evidence report. | [isolated-worker](<../../plugins/work-controller/roles/isolated-worker.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/work-controller](<../../exports/claude/plugins/work-controller>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/work-controller](<../../exports/copilot/plugins/work-controller>) | `adapted` | No workflow entry points |
| codex | [exports/codex/plugins/work-controller](<../../exports/codex/plugins/work-controller>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/work-controller](<../../exports/pi/plugins/work-controller>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/work-controller](<../../exports/opencode/plugins/work-controller>) | `adapted` | No workflow entry points |

### Additional shipped contracts and mechanisms

- Exported shared contract: [contracts/work.toml](<../../plugins/work-controller/contracts/work.toml>).
- MCP server `work-controller`: `uv`, `run`, `--no-config`, `--no-project`, `--script`, `${CLAUDE_PLUGIN_ROOT}/skills/work-record/scripts/controller.py`, `mcp`. Host registration differs; see the host reference.

<!-- daodan:reference:end -->
