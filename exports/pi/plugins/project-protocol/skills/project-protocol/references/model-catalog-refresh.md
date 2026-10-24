> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
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

# Model catalog refresh

How to refresh the model knowledge this skill ships: what each file is, where each fact
comes from, the steps and the checks. The router reads the catalog
([task routing](task-routing.md)); the usage ledger of ADR-0003 reads the prices and the
rules through `scripts/usage_pricing.py`.

## What a refresh produces

| File | Made by | Edited by hand |
|---|---|---|
| `references/model-catalog.json` | `scripts/build_model_catalog.py` | never |
| `references/model-prices.json` | `scripts/build_model_prices.py` | never |
| `references/price-rules.json` | a person, from official pricing pages | yes, every rule with `source`, `verified` and `quote` |
| Arena snapshot, `arena-<date>.json` | `scripts/benchmark_snapshot.py` | never; stays in ignored local storage |

The downloaded inputs stay in `.tritech/local/model-catalog/<date>/`, which Git ignores:
they are large, and the Arena ELO data carries no redistribution term.

## Where each fact comes from

| Dimension | Source | Role |
|---|---|---|
| Identity, creator, family, version, release date, status | models.dev | primary |
| Context and output limits | models.dev | primary |
| Capabilities: modalities, tool call, reasoning and effort options, structured output, open weights, knowledge cutoff | models.dev | primary; declared by providers, measured by nobody |
| Endpoint prices, with context tiers, reasoning and audio rates | models.dev | primary |
| What a pricing page states and models.dev lacks: 1-hour cache write, region or speed multipliers, time windows, per-request tool fees | official pricing pages, into `price-rules.json` | settles every disagreement |
| Second and third reading of prices | LiteLLM, OpenRouter | cross-check only, never a price source |
| Aptitude per work type, tier evidence | Arena leaderboards | evidence for a declared tier; never the maximum across boards |
| Tier | declared in `build_model_catalog.py` (`FAMILY_TIER`) | no source carries one |
| Cost and outcome on this harness's own work | the usage ledger joined to verified gate outcomes (ADR-0003) | the only source that measures our workload |

Status of each external source, read on 2026-10-24:

| Source | Access | Licence | Last update seen |
|---|---|---|---|
| [models.dev](https://models.dev/api.json) | public JSON, `--fetch` | MIT, `github.com/anomalyco/models.dev` | 2026-10-24, synced several times a day |
| [LiteLLM](https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json) | raw file in the repository | MIT outside `enterprise/` | 2026-10-24 |
| [OpenRouter](https://openrouter.ai/api/v1/models) | public API, no key | terms not verified | live |
| Arena, mirror `oolong-tea-2026/arena-ai-leaderboards` | `benchmark_snapshot.py` | MIT on the mirror's files; ELO data belongs to arena.ai | last data 2026-10-07; 14 of 15 runs failed since 2026-10-08 (its issue #2) |

Capability sources read on 2026-10-24 that the builder does not ingest yet, in order of
fit for `agent_tool_use` and `coding`:

| Source | Access | Licence | Last update | Coverage |
|---|---|---|---|---|
| [Arena official dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset), boards `agent` and `webdev` | JSON rows through `datasets-server.huggingface.co/rows`, no key; raw files are parquet | CC-BY-4.0 | 2026-10-23 | agent 50 models, webdev 150; effort inside the model name |
| [Epoch AI Benchmarking Hub](https://epoch.ai/benchmarks/use-this-data) | one ZIP of CSV files, no key | CC-BY-4.0 for Epoch's own runs; copied rows keep their licence | 2026-10-24 | SWE-bench Verified and agentic sets; ids carry effort; `model_metadata.csv` covers 1176 models |
| [tau2-bench](https://github.com/sierra-research/tau2-bench) | one JSON per submission in the repository | MIT | 2026-10-22 | conversational tool use; few economical models |
| [Terminal-Bench](https://www.tbench.ai/leaderboard) | embedded page data only | not stated | 2026-09-29 | 35 rows, mostly vendors' own agents |
| [SWE-bench Pro, Scale](https://labs.scale.com/leaderboard/swe_bench_pro_public_v2) | embedded page data only | terms not read | 2026-10-14 | 16 rows |

Rejected on the same day: the SWE-bench site data (newest row 2026-02-26), BFCL
(2026-04-12), Aider polyglot (2025-10-04), LiveBench (2026-06-25, custom licence),
Artificial Analysis (API key, terms forbid republishing; OpenRouter's copy of its
indices carries the same terms), OpenCompass (no export).

## When to refresh

- Monthly.
- At once when the router reports a harness model it cannot match, or a provider
  announces a price change.
- Re-read a rule's official page when its `verified` date is older than 90 days.

## Steps

Run from this skill's directory: `<plugin-root>/skills/project-protocol` when
installed, the kernel's skill directory in a checkout of the marketplace. `N` is the
current `revision` of the catalog; the generated files take `N+1` together. `DIR` is
ignored local storage of the project you run in.

1. Download the inputs once, so both builders read the same models.dev response:

   ```bash
   DIR=<project>/.tritech/local/model-catalog/$(date +%F)
   mkdir -p "$DIR"
   curl -sSL https://models.dev/api.json -o "$DIR/models-dev.json"
   curl -sSL https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json -o "$DIR/litellm.json"
   curl -sSL https://openrouter.ai/api/v1/models -o "$DIR/openrouter.json"
   ```

2. Pin the Arena snapshot. It refuses an empty snapshot and walks back to the newest one
   with data; if that is older than `--max-staleness-days`, keep the previous snapshot and
   say so in the commit message:

   ```bash
   python -B scripts/benchmark_snapshot.py --fetch --out-dir "$DIR"
   ```

3. Build the catalog with the OpenCode config of the reference deployment, so harness
   models come first and gateway-only models get rows:

   ```bash
   python -B scripts/build_model_catalog.py --from-response "$DIR/models-dev.json" \
     --benchmark "$DIR/arena-<date>.json" --harness-config <opencode.json> \
     --revision N+1 --out references/model-catalog.json
   ```

4. Build the prices from the same response:

   ```bash
   python -B scripts/build_model_prices.py --catalog references/model-catalog.json \
     --from-response "$DIR/models-dev.json" --revision N+1 --out references/model-prices.json
   ```

5. Cross-check the prices and read every finding:

   ```bash
   python -B scripts/price_crosscheck.py --prices references/model-prices.json \
     --litellm "$DIR/litellm.json" --openrouter "$DIR/openrouter.json" --out "$DIR/crosscheck.json"
   ```

   - A numeric disagreement: read the official page. When models.dev is wrong, open an
     issue upstream and add a `rate` rule with the official figure until it is fixed.
     When the aggregator is wrong, note nothing.
   - `dimensions-only-there`: read the official page. Add a rule with its quote, or an
     entry under `not_modelled` saying why no log can carry it (a batch discount, for
     instance).

6. Re-verify every rule older than 90 days, update its `verified` date and raise the
   `revision` of `price-rules.json` when a rule changes.

7. Check. In a checkout of the marketplace, run the suites from its root:

   ```bash
   python -B -m unittest discover -s tests -p "test_build_model_catalog.py"
   python -B -m unittest discover -s tests -p "test_usage_pricing.py"
   python -B -m unittest discover -s tests -p "test_task_router*.py"
   ```

   Everywhere, price a real log of a host that records its own cost:

   ```bash
   python -B scripts/usage_pricing.py summary --host opencode --source <opencode.db>
   ```

   On a host that logs its own cost (OpenCode, Pi), every priced group of the last step
   matches the host's figure when both use the same prices; a difference is explained
   before publishing (a changed harness price, a gateway's own rate), never averaged away.

8. In the marketplace, publish through its update workflow: bump `project-protocol`, bump the
   marketplace version, rebuild, `--check`, one commit with the regenerated files. Name
   the models.dev digest, the Arena snapshot date and the harness config in the message.

## Rules that bind

- A generated file is never edited by hand; a wrong value is fixed at its source or by a
  sourced rule.
- An aggregator is never a price source. An official page settles; models.dev supplies.
- An unknown stays unknown: an unmatched model or an unpriced row is reported, never zero.
- The tier is declared and benchmark rows are evidence for it. Boards are different
  populations, so no score is ever taken as the maximum across them.

## Known gaps

- The `agent_tool_use` aptitude is empty, and the cause is ours: the mirror's `agent`
  rows keep six metrics in a `scores` list and no single `score`, which is the field the
  snapshot reads. Moving the benchmark input to the Arena official dataset, with board
  names pinned so an unknown or renamed board fails, fixes both this and the dead mirror.
- Claude Code's log names no endpoint: pass `--endpoint` for Bedrock, Vertex or a gateway.
- Codex `cache_write_input_tokens` was 0 in every local rollout, so whether it sits inside
  `input_tokens` is unverified.
- Pi and OpenCode log their cost with the prices configured at that moment; a harness
  config passed later prices old rows at today's rates.
- Copilot: no local usage source verified.
