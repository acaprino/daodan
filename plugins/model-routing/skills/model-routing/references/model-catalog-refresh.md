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

Run from this skill's directory: `${CLAUDE_PLUGIN_ROOT}/skills/model-routing` when
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

8. In the marketplace, publish through its update workflow: bump `model-routing`, bump the
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
