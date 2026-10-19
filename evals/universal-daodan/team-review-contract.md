# Canary eval: the branch review contract on every host

The branch review (`/daodan:review-branch`, variant `team-review`) is the complex canary. It fans out over dimensions chosen at runtime, requires every
reviewer to work in its own context, holds an all-delivered barrier before anything is consolidated,
cross-examines the consolidated set in fresh contexts, and lets exactly one phase write the report.

Each host picks a different topology to do that. The topology may differ; the contract may not.

## What is asserted mechanically

`tests/test_review_pipeline_ports.py` runs in the normal suite. Since marketplace 38.0.0 the entry is
`/daodan:review-branch`, whose sidecar carries no phase graph: the review's roster is computed per
run, and the order, barrier and single writer belong to the three units the variant reads
(`references/team-review.md` of review-preparation, review-method and review-consolidation). It
asserts, for every host:

- review-branch dispatches in isolated contexts with inline workers, and declares every reviewer
  role those units and `stack-dimensions.md` name
- the units' phases run 0, 0b, 0c, 1, 1a, 1c, 1d, 1b, 2, 3, 4, 4b, 4c, 5; reviewers run in parallel,
  each in its own context; consolidation waits for the delivery barrier; verification starts after
  the consolidated findings exist
- only the consolidation unit writes the final report, and reviewers write only their own findings
- all seven record contracts are exported by `senior-review` and listed by review-branch, which also
  keeps the seven outcomes of the former team-review command
- `codebase-map` writes only `.codebase-map` through the neutral write-confinement
  policy; historical `.codebase-xray` report archives use the project-bound migration helper
- `senior-review` declares no external team runtime, and every dimension plugin stays a hard
  dependency of it and of `daodan`

Rebuild and verify with:

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check
python -m unittest discover -s tests -p "test_review_pipeline_ports.py" -v
python adapters/copilot/policies/xray-guard/test_xray_guard.py
```

The guard suite reports `36/36 passed`.

## Selected topology per host

Recorded in each package's `.daodan-provenance.json` under `harnessStrategies`:

| host | strategy | role delivery | isolated | parallel |
|---|---|---|---|---|
| claude | `native-team` (runtime-optional, falls back to `parallel-subagents`) | named agent | yes | yes |
| copilot | `parallel-subagents` | named custom agent, restricted by the coordinator's `agents` allowlist | yes | yes |
| codex | `parallel-subagents` | inline prompt | yes | yes |

**These rows are provisional.** They come from the adapter coordination files, which still carry the
spec's documented assumptions rather than measured evidence: the host protocol probes in
`tests/host-probes/README.md` have not been run. Re-derive this table from that one.

## Contract results

The behavioural half needs one fixture review run per host.

| host | isolated worker contexts | every expected reviewer delivered or failed | cross-examination after the barrier | every retained finding carries evidence | final report artifact written | single writer respected |
|---|---|---|---|---|---|---|
| claude | TODO | TODO | TODO | TODO | TODO | TODO |
| copilot | TODO | TODO | TODO | TODO | TODO | TODO |
| codex | TODO | TODO | TODO | TODO | TODO | TODO |

**Not yet measured.** The eval passes only when every column is `yes` on every host. A `no` anywhere
blocks the complete release, because a review with a hole in it is the exact failure the mandatory
dependency policy exists to prevent.
