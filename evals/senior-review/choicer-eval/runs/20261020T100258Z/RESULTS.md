# Choicer offline pilot

The candidate rejected exact critical-role criteria in every observed encoding for senior-review:premise-auditor. This pilot rejects compatibility with this run's catalog; partial answers do not establish full routing quality.

Recorded date: 2026-10-20T10:04:08.661639+00:00. Evidence directory: evals/senior-review/choicer-eval/runs/20261020T100258Z.

## Protocol and scope

The dataset contains 11 cases, 10 with expected reviewer dimensions and 1 without activation labels. The catalog contains 18 reviewer roles; 129 hunks were materialized.

The credential-refill case is unlabeled for reviewer activation. Its must-not-report claim concerns findings and cannot establish that any reviewer should or should not activate. It contributes only to measured agreement and latency when predictions exist.

Expected dimensions are known positive review lenses, not an exhaustive annotation of every legitimate trigger. Consequently, 'false activations' below mean benchmark-excess selections only. They do not establish wasted reviewer tokens or irrelevant reviews. ECE likewise uses proxy negatives and is descriptive, not validated calibration of reviewer relevance.

0.5 fixed a priori; the full empirical curve is descriptive and must not select the reported threshold.
The scoring JSON retains every achievable selection set on the empirical threshold curve, including the inclusive >= boundary, plus a fixed display grid. No best threshold is selected.

Incomplete, failed, duplicate, or blocked cases never become negative predictions.
Comparative metrics use the same complete cases on both sides. Model-level summaries also state their own coverage, which can differ.
Neither partial-capability answers nor raw-declared LLM selections enter any paired comparison or replace a primary prediction.

LLM baseline validation: Accepted under limited citation checks: registered role, hunk ID, exact supplied path and line, snippet occurrence, tier/effort and reason constraints. Frozen hunk inputs omit base/candidate bindings, so side claims are unverified. This is not full schema/evidence conformance or proof of semantic reviewer relevance.
For A, 'complete' means accepted under those limited checks. The original request inputs remain frozen; side warnings are retained with each response.

### Materialization and leakage boundary

| Recorded rule | Exact dataset protocol |
| --- | --- |
| version | choicer-pilot-source-v1 |
| case_order | Lexicographic case-directory order, opaque IDs C01..C11. |
| history_rule | For fix-history cases, git diff --no-ext-diff --no-textconv --no-renames --unified=3 REVIEW FIX, restricted to the case's explicit paths. Each unified block becomes one hunk containing only the OLD side (unchanged context and removed lines). No fixed lines, commit messages or labels enter model state. Added-only blocks retain their old context. Empty old-side blocks are omitted and recorded. Later fixes localize these retrospective inputs; this is not a prospective routing sample. |
| updater_rule | The case explicitly permits 936ba644~1..936ba644. Use the full diff alternative, including its docs, tests and configuration. Each unified block contains only the NEW side, which is the buggy reviewed revision. |
| synthetic_rule | Each verbatim fenced buggy source file is one contiguous introduced block, including its source-path comment. Do not invent companion files or missing model/schema declarations. |
| credential_rule | No diff is supplied. Read complete alive_agent.py and middleware/heartbeat_monitor.py at a0bb4f10. Split all top-level declarations and class members by Python AST source ranges. Attach intervening lines, imports, class headers and comments to the following declaration; append trailing source to the final declaration. Functions remain complete and decorators remain attached. No method is selected using the precision oracle or case narrative. This case is unlabeled. |
| line_coordinates | start_line and end_line are 1-based in the reviewed source blob. Hunk text has no diff prefix; no cross-hunk source rewriting occurs. |
| symbol_cards | No case supplies a symbol card. All symbol_cards are empty; no inferred cards or undocumented one-hop context are synthesized. |
| labels | Union roles from Expected dimension cells, dropping parenthetical qualifiers and deduplicating roles. No Expected dimension table means unlabeled, not a negative example. Labels are case-level only. |
| threshold | noul P(true) >= 0.5 fixed a priori; full curve is descriptive. |
| leakage_boundary | Only hunk id, path, source line coordinates, source text and supplied symbol_cards are model-state fields. source_case, labels, revisions, case Markdown, provenance and anomalies are scorer-side metadata. |

Reviewer-catalog selection: {"dimension_source": {"path": "plugins/senior-review/skills/review-method/references/team-review.md", "sha256": "89383467d1ad7a34beb2021b97869407e49b75ea6322aa3b43932f1c8516bde1"}, "excluded_producers": ["codebase-map:map-analyst", "codebase-map:semantic-interconnect-mapper"], "rule": "review-branch dispatch roles, excluding its two codebase-map evidence producers", "source": {"path": "plugins/daodan/workflows/review-branch.toml", "sha256": "e0102e86e471e027b1c16de6fad60f9c2a9f190af33063c999708827a6070b72"}, "why_not_all_roles": "Writers, maintainers, map producers and protocol workers are not reviewer lenses."}

Role criteria are parsed from source frontmatter. Missing trigger fields remain missing and are reported as anomalies; this report does not synthesize replacement criteria.

## Dimension mapping

| Expected dimension | Role ID |
| --- | --- |
| architecture | `senior-review:code-auditor` |
| data-integrity | `senior-review:data-integrity-auditor` |
| distributed-flow | `senior-review:distributed-flow-auditor` |
| documentation | `senior-review:cleanup-auditor` |
| hygiene | `senior-review:cleanup-auditor` |
| logic-integrity | `senior-review:logic-integrity-auditor` |
| premise | `senior-review:premise-auditor` |
| resource | `senior-review:resource-lifecycle-auditor` |
| resource-lifecycle | `senior-review:resource-lifecycle-auditor` |
| security | `senior-review:security-auditor` |
| temporal | `senior-review:temporal-resilience-auditor` |
| temporal-resilience | `senior-review:temporal-resilience-auditor` |
| ui | `senior-review:ui-race-auditor` |

Mapping provenance: {"documentation_and_hygiene": {"path": "plugins/senior-review/roles/cleanup-auditor.md", "sha256": "3f46c57b34faf982d4734b9de132ff4eb3d4e8e351730da7031828db1905cc97"}, "rule": "Architecture follows the method's code-auditor row; UI follows UI race conditions; documentation/hygiene use the codebase-hygiene owner, whose remit explicitly includes stale docs.", "source": {"path": "plugins/senior-review/skills/review-method/references/team-review.md", "sha256": "89383467d1ad7a34beb2021b97869407e49b75ea6322aa3b43932f1c8516bde1"}}

## Model identity and environment

| Implementation / variant | Recorded identity and runtime |
| --- | --- |
| julia/choice | {"batch_size": 1, "checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 31.796875, "load_sessions": [{"batch_size": 1, "checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 31.796875, "load_started_at": "2026-10-20T10:45:02.149229+00:00", "load_wall_seconds": 32.42097879998619, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "require_complete_catalog": true, "revision": "a85b127321d580d65176c89ced8273f305745d85", "session_id": "choice-2026-10-20T10:45:02.149229+00:00", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"}], "load_started_at": "2026-10-20T10:45:02.149229+00:00", "load_wall_seconds": 32.42097879998619, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "require_complete_catalog": true, "revision": "a85b127321d580d65176c89ced8273f305745d85", "session_id": "choice-2026-10-20T10:45:02.149229+00:00", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"} |
| julia/noul | {"checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 36.0625, "load_sessions": [{"batch_size": 16, "batch_size_provenance": "Original fixed runner configuration", "checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 36.0625, "load_wall_seconds": 50.45853459998034, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "revision": "a85b127321d580d65176c89ced8273f305745d85", "session_id": "noul-initial", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"}, {"batch_size": 1, "checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 40.90625, "load_started_at": "2026-10-20T10:37:57.517305+00:00", "load_wall_seconds": 42.23155660001794, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "revision": "a85b127321d580d65176c89ced8273f305745d85", "session_id": "noul-2026-10-20T10:37:57.517305+00:00", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"}, {"batch_size": 1, "checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 30.0, "load_started_at": "2026-10-20T10:44:27.809611+00:00", "load_wall_seconds": 30.491656200028956, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "require_complete_catalog": true, "revision": "a85b127321d580d65176c89ced8273f305745d85", "session_id": "noul-2026-10-20T10:44:27.809611+00:00", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"}], "load_wall_seconds": 50.45853459998034, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "revision": "a85b127321d580d65176c89ced8273f305745d85", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"} |
| llm/noul | {"actual_model_used": null, "cheapest_price_verified": false, "host_accepted_model_override": "gpt-6-luna", "identity_source": "Local Codex config model plus available host model catalog", "native_case_tasks": 11, "provider": "OpenAI through Codex native subagents", "provider_api_call_count": null, "provider_reported_model": null, "requested_model": "gpt-6-luna", "status": "11 native case responses captured; 7 pass limited citation/format checks, 4 rejected. Provider telemetry unavailable.", "transport_evidence": "captures/C01-batch.json through captures/C11-batch.json", "usage": null} |

Hardware: {"cpu_model": "Intel(R) Core(TM) Ultra 7 155H", "gpu": "unused; CPU protocol", "logical_cpus": 22, "machine": "", "platform": "Windows-11-10.0.26200-SP0", "python": "3.13.14", "ram_bytes": 33775378432, "ram_measurement_evidence": "execution/hardware-memory.json"}

Provenance: {"entry_sha256": "994fcece16289e350dd62b23b57a37569c432e9dd0be4d9fe9b4249e0b28d807", "final_evaluator_sources": {"adapt_reviewers_blind.py": "58e3f9bf7241ef06b9b33cccc38a925507d258903f5ff6e9b6cea8961277afbd", "dataset.py": "d6fbd713ac791b52e0fa29f879ad0709c15bc94f6945534dd67ca2af0de06725", "metrics.py": "c5cafd06db1960d11536d155ba7074ad9e996f97cbdd507412f89f778b7bd1f5", "prepare_adapted.py": "0d423825b306a69b420d6ea617c20abd41fd858dfec6ed1a7fb9100c55f4d9ce", "run_eval.py": "d8b18e7e7d7b68cb6cc39b33c7359661e962c61d3502fee5094a3be033b87573", "summarize_runs.py": "cb408a3932b810c5990f90cbd172f8cde63ec6897e439ca58a84d1da3ab396b9", "test_adaptation.py": "a5ee610bdfcba535dbef1e90e93e1ee3582d7ca7e294b3d44bec7ff9b5485dec", "test_inputs.py": "d6cc1aa32dbbd636ad49986df7f5ed2d998b16d546cddecb961bbf6343f689cc", "test_llm_validation.py": "c696f8d26df9cc73a36723a582b08eacb21f7bd47fff8c11a7e94f73e0bd2e72", "test_metrics.py": "813a51540fcc8173fb120f199387056135e63b674847882ecb2fa4d9172cc07a", "test_runtime.py": "fd44ccf80dd3dc1591e79a4c122c5f3c57ed9959a83a72311c8cd25a54aa21e7"}, "original_request_count_reverified": 269, "source_files": {"dataset.py": "d6fbd713ac791b52e0fa29f879ad0709c15bc94f6945534dd67ca2af0de06725", "metrics.py": "a202ff20695f3177b448700e7e47567d7988e8a487fce2686f0c4faf6c6e585b", "run_eval.py": "994fcece16289e350dd62b23b57a37569c432e9dd0be4d9fe9b4249e0b28d807", "test_inputs.py": "d6cc1aa32dbbd636ad49986df7f5ed2d998b16d546cddecb961bbf6343f689cc", "test_metrics.py": "65cb50e3da9e9193d56fe6e8d7e410e00e78f856b307bca24b0762bb15b4dea0", "test_runtime.py": "fa2dcd83596f4d43bcae975fb7aea3624611ba11d1e4a09001f985e87071cfc5"}, "upstream_manifest_sha256": "fd52ce9c858bb8d8c0df54889c59b64b3d5a9f24630777aaf39a517d5d606c38"}

Model-card accuracy, context size, format and speed claims are not measurements of this pilot. Unknown identity, revision, weight hash, precision and runtime fields remain unknown until recorded by execution.

## Reviewer activation metrics

| Implementation | Complete cases | Labeled cases scored | Expected-role recall | Critical recall | Benchmark excess / labeled case | Descriptive ECE |
| --- | --- | --- | --- | --- | --- | --- |
| julia/choice | 0/11 | 0 | unknown | undefined (no labeled support) | unknown | unknown |
| julia/noul | 0/11 | 0 | unknown | undefined (no labeled support) | unknown | unknown |
| llm/noul (limited citation checks) | 7/11 | 7 | 0.250 | 1/3 (0.333) | 0.857 | unknown |

| Implementation | Critical role | Recall | False negatives |
| --- | --- | --- | --- |
| julia/choice | senior-review:security-auditor | undefined (no labeled support) | undefined |
| julia/choice | senior-review:premise-auditor | undefined (no labeled support) | undefined |
| julia/choice | senior-review:data-integrity-auditor | undefined (no labeled support) | undefined |
| julia/noul | senior-review:security-auditor | undefined (no labeled support) | undefined |
| julia/noul | senior-review:premise-auditor | undefined (no labeled support) | undefined |
| julia/noul | senior-review:data-integrity-auditor | undefined (no labeled support) | undefined |
| llm/noul (limited citation checks) | senior-review:security-auditor | 0/1 (0.000) | 1 |
| llm/noul (limited citation checks) | senior-review:premise-auditor | undefined (no labeled support) | undefined |
| llm/noul (limited citation checks) | senior-review:data-integrity-auditor | 1/2 (0.500) | 1 |

## Unvalidated LLM declared-role diagnostic

Unvalidated raw-declared LLM role sets, including responses rejected for citations or other output metadata. Reveals selection/validation attrition only; never substitutes for the validated baseline.
Excluded from primary metrics, paired comparisons and the verdict. Do not compare as a controlled baseline to a differently adapted catalog.

11 raw role sets are readable; 4 of those failed primary validation. A known role ID with a bad citation remains unvalidated even when the role happens to be expected.

| Case | Primary limited checks | Raw declared roles | Validation error |
| --- | --- | --- | --- |
| C01 | complete | `senior-review:distributed-flow-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:premise-auditor` | (none) |
| C02 | unavailable | `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:distributed-flow-auditor`, `senior-review:premise-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor` | Citation is outside the supplied hunk |
| C03 | unavailable | `senior-review:data-integrity-auditor`, `senior-review:premise-auditor`, `senior-review:security-auditor` | Citation snippet is absent at the cited line |
| C04 | complete | `senior-review:premise-auditor` | (none) |
| C05 | complete | (none) | (none) |
| C06 | complete | (none) | (none) |
| C07 | unavailable | `senior-review:code-auditor`, `senior-review:premise-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor` | Citation is outside the supplied hunk |
| C08 | unavailable | `senior-review:distributed-flow-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor` | Missing reason or reason exceeds 15 words |
| C09 | complete | `senior-review:resource-lifecycle-auditor`, `senior-review:temporal-resilience-auditor` | (none) |
| C10 | complete | `senior-review:data-integrity-auditor`, `senior-review:premise-auditor`, `senior-review:security-auditor` | (none) |
| C11 | complete | `senior-review:temporal-resilience-auditor` | (none) |

| Diagnostic only | Labeled cases | Expected-role recall | Benchmark excess / case |
| --- | --- | --- | --- |
| Raw declared known-role sets | 10 | 0.304 | 1.400 |

| Critical role | Unvalidated declared-role recall |
| --- | --- |
| senior-review:security-auditor | 0/1 (0.000) |
| senior-review:premise-auditor | undefined (no labeled support) |
| senior-review:data-integrity-auditor | 2/4 (0.500) |

## Partial-capability diagnostic

This separate view inspects successful questions retained inside failed full-catalog calls. It never fills missing primary predictions, changes the primary recall denominator, or supplies a B set for agreement. A role/case is usable here only when every one of its hunks has an explicitly accepted, untruncated encoding and a finite normalized binary answer. Probabilities are aggregated by maximum at the fixed threshold. Recall is conditional on this stated role-specific coverage.

### julia/noul

| Role | Complete cases for role | Scored / expected positive cases | Scored positive case IDs | Positive hits | Conditional recall | Accepted encodings | Rejected encodings |
| --- | --- | --- | --- | --- | --- | --- | --- |
| abstraction-architect:abstraction-architect-agent | 0 | 0/0 | (none) | undefined | unknown | 0 | 129 |
| platform-engineering:platform-reviewer | 0 | 0/0 | (none) | undefined | unknown | 0 | 129 |
| react-development:react-performance-optimizer | 0 | 0/0 | (none) | undefined | unknown | 0 | 129 |
| repo-hygiene:workspace-auditor | 0 | 0/0 | (none) | undefined | unknown | 0 | 129 |
| senior-review:api-contract-auditor | 1 | 0/0 | (none) | undefined | unknown | 125 | 4 |
| senior-review:chicken-egg-detector | 1 | 0/0 | (none) | undefined | unknown | 125 | 4 |
| senior-review:cleanup-auditor | 0 | 0/1 | (none) | undefined | unknown | 0 | 129 |
| senior-review:code-auditor | 1 | 0/3 | (none) | undefined | unknown | 125 | 4 |
| senior-review:data-integrity-auditor | 1 | 1/4 | C01 | 1 | 1.000 | 125 | 4 |
| senior-review:distributed-flow-auditor | 0 | 0/1 | (none) | undefined | unknown | 0 | 129 |
| senior-review:logic-integrity-auditor | 1 | 0/4 | (none) | undefined | unknown | 125 | 4 |
| senior-review:premise-auditor | 0 | 0/0 | (none) | undefined | unknown | 0 | 129 |
| senior-review:resource-lifecycle-auditor | 1 | 0/1 | (none) | undefined | unknown | 125 | 4 |
| senior-review:security-auditor | 1 | 0/1 | (none) | undefined | unknown | 125 | 4 |
| senior-review:temporal-resilience-auditor | 1 | 1/6 | C01 | 1 | 1.000 | 125 | 4 |
| senior-review:ui-race-auditor | 0 | 0/2 | (none) | undefined | unknown | 0 | 129 |
| testing:test-suite-auditor | 1 | 0/0 | (none) | undefined | unknown | 125 | 4 |
| typescript-development:type-safety-auditor | 0 | 0/0 | (none) | undefined | unknown | 0 | 129 |

| Role with encoding failure | Recorded errors and counts |
| --- | --- |
| abstraction-architect:abstraction-architect-agent | {"ValueError: Option exceeds 48-token model contract": 129} |
| platform-engineering:platform-reviewer | {"ValueError: JSONL line 1: options must contain 2–20 nonempty rendered descriptions": 129} |
| react-development:react-performance-optimizer | {"ValueError: Option exceeds 48-token model contract": 129} |
| repo-hygiene:workspace-auditor | {"ValueError: Option exceeds 48-token model contract": 129} |
| senior-review:api-contract-auditor | {"ValueError: Game state exceeds lossless context budget": 4} |
| senior-review:chicken-egg-detector | {"ValueError: Game state exceeds lossless context budget": 4} |
| senior-review:cleanup-auditor | {"ValueError: Option exceeds 48-token model contract": 129} |
| senior-review:code-auditor | {"ValueError: Game state exceeds lossless context budget": 4} |
| senior-review:data-integrity-auditor | {"ValueError: Game state exceeds lossless context budget": 4} |
| senior-review:distributed-flow-auditor | {"ValueError: JSONL line 1: options must contain 2–20 nonempty rendered descriptions": 129} |
| senior-review:logic-integrity-auditor | {"ValueError: Game state exceeds lossless context budget": 4} |
| senior-review:premise-auditor | {"ValueError: Option exceeds 48-token model contract": 129} |
| senior-review:resource-lifecycle-auditor | {"ValueError: Game state exceeds lossless context budget": 4} |
| senior-review:security-auditor | {"ValueError: Game state exceeds lossless context budget": 4} |
| senior-review:temporal-resilience-auditor | {"ValueError: Game state exceeds lossless context budget": 4} |
| senior-review:ui-race-auditor | {"ValueError: JSONL line 1: options must contain 2–20 nonempty rendered descriptions": 129} |
| testing:test-suite-auditor | {"ValueError: Game state exceeds lossless context budget": 4} |
| typescript-development:type-safety-auditor | {"ValueError: Option exceeds 48-token model contract": 129} |

Critical roles rejected in every observed encoding: `senior-review:premise-auditor`. This is a compatibility failure for this run's supplied criteria, not a measured false negative.

## Per-case agreement

A is the verbatim LLM full-mode reviewer selection. B is Julia noul at the fixed threshold. C is Julia categorical choice, whose per-hunk argmax selections are unioned. Agreement is exact set equality followed by Jaccard overlap; two measured empty sets have Jaccard 1.

The same A baseline is compared with both B and C. A separate LLM single-choice control would change the verbatim full-mode prompt and is therefore not claimed by this benchmark.

| Case | Expected | A selected (limited checks) | B selected | C selected | A/B agreement |
| --- | --- | --- | --- | --- | --- |
| C01 (jupiter-cache-convergence) | `senior-review:data-integrity-auditor`, `senior-review:temporal-resilience-auditor` | `senior-review:distributed-flow-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:premise-auditor` | unavailable | unavailable | unavailable |
| C02 (jupiter-credential-refill) | unlabeled | unavailable | unavailable | unavailable | unavailable |
| C03 (jupiter-economic-events-upsert) | `senior-review:data-integrity-auditor` | unavailable | unavailable | unavailable | unavailable |
| C04 (jupiter-market-state-tristate) | `senior-review:logic-integrity-auditor`, `senior-review:temporal-resilience-auditor` | `senior-review:premise-auditor` | unavailable | unavailable | unavailable |
| C05 (jupiter-position-notice-owner) | `senior-review:logic-integrity-auditor`, `senior-review:security-auditor` | (none) | unavailable | unavailable | unavailable |
| C06 (jupiter-trade-failure-drop) | `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor` | (none) | unavailable | unavailable | unavailable |
| C07 (jupiter-updater) | `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor` | unavailable | unavailable | unavailable | unavailable |
| C08 (synthetic-cache-stale-read) | `senior-review:data-integrity-auditor` | unavailable | unavailable | unavailable | unavailable |
| C09 (synthetic-connection-pool-leak) | `senior-review:code-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:temporal-resilience-auditor` | `senior-review:resource-lifecycle-auditor`, `senior-review:temporal-resilience-auditor` | unavailable | unavailable | unavailable |
| C10 (synthetic-payment-double-insert) | `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:logic-integrity-auditor` | `senior-review:data-integrity-auditor`, `senior-review:premise-auditor`, `senior-review:security-auditor` | unavailable | unavailable | unavailable |
| C11 (synthetic-retry-storm) | `senior-review:code-auditor`, `senior-review:temporal-resilience-auditor` | `senior-review:temporal-resilience-auditor` | unavailable | unavailable | unavailable |

| Pair | Paired cases | Paired labeled cases | Exact agreement | Mean Jaccard | Left recall | Right recall | Left excess / case | Right excess / case |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| julia/choice vs julia/noul | 0 | 0 | unknown | unknown | unknown | unknown | unknown | unknown |
| julia/choice vs llm/noul | 0 | 0 | unknown | unknown | unknown | unknown | unknown | unknown |
| julia/noul vs llm/noul | 0 | 0 | unknown | unknown | unknown | unknown | unknown | unknown |

## Calibration

### julia/choice

Categorical choice probabilities are not independent binary P(true) values.

### julia/noul

No complete labeled case probabilities.

### llm/noul

The verbatim REVIEWER_CHOICER emits selections, not P(true); no synthetic confidence.

## Latency and provider tokens

All values are seconds. Full-case totals require one uniquely identified attempt for every expected hunk or case batch, whether that attempt succeeded or failed. They are unknown if a required attempt or component timing is absent. Prediction validity is independent of timing coverage. Known recorded-attempt sums are shown separately for partial cases and never imply a measured full-case duration. Recorded call duration includes question-encoding preflight. Cold/warm rows describe the recorded call phases, not invented repeated trials. CPU is the runner's recorded process CPU time; remote service CPU is unknown. Failed attempted calls remain in operational call and token totals. Model provisioning and load costs are reported separately when supplied in run metadata. Cold means the first inference in a fresh process; the operating-system page cache is not flushed. Repeated warm timing samples, when recorded, do not add prediction votes or calibration observations.

| Implementation | Phase | Timed calls / calls | Wall total | Wall mean | CPU total |
| --- | --- | --- | --- | --- | --- |
| julia/choice | cold | 0/0 | unknown | unknown | unknown |
| julia/choice | warm | 0/0 | unknown | unknown | unknown |
| julia/choice | preflight | 129/129 | 0.033 | 0.000 | 0.031 |
| julia/choice | unknown | 0/0 | unknown | unknown | unknown |
| julia/noul | cold | 1/1 | 4.285 | 4.285 | 16.719 |
| julia/noul | warm | 22/22 | 870.373 | 39.562 | 3023.688 |
| julia/noul | preflight | 106/106 | 0.626 | 0.006 | 0.641 |
| julia/noul | unknown | 0/0 | unknown | unknown | unknown |
| llm/noul | cold | 0/0 | unknown | unknown | unknown |
| llm/noul | warm | 0/0 | unknown | unknown | unknown |
| llm/noul | preflight | 0/0 | unknown | unknown | unknown |
| llm/noul | unknown | 0/11 | unknown | unknown | unknown |

| Implementation | Case | Prediction status | Timing coverage | Full wall | Full CPU | Cold wall | Cold CPU | Warm wall | Warm CPU | Known recorded-attempt wall | Known recorded-attempt CPU |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| julia/choice | C01 | unavailable | complete (14/14 records) | 0.009 | 0.016 | unknown | unknown | unknown | unknown | 0.009 | 0.016 |
| julia/choice | C02 | unavailable | complete (49/49 records) | 0.011 | 0.000 | unknown | unknown | unknown | unknown | 0.011 | 0.000 |
| julia/choice | C03 | unavailable | complete (5/5 records) | 0.001 | 0.000 | unknown | unknown | unknown | unknown | 0.001 | 0.000 |
| julia/choice | C04 | unavailable | complete (7/7 records) | 0.001 | 0.000 | unknown | unknown | unknown | unknown | 0.001 | 0.000 |
| julia/choice | C05 | unavailable | complete (2/2 records) | 0.000 | 0.000 | unknown | unknown | unknown | unknown | 0.000 | 0.000 |
| julia/choice | C06 | unavailable | complete (9/9 records) | 0.002 | 0.000 | unknown | unknown | unknown | unknown | 0.002 | 0.000 |
| julia/choice | C07 | unavailable | complete (39/39 records) | 0.008 | 0.016 | unknown | unknown | unknown | unknown | 0.008 | 0.016 |
| julia/choice | C08 | unavailable | complete (1/1 records) | 0.000 | 0.000 | unknown | unknown | unknown | unknown | 0.000 | 0.000 |
| julia/choice | C09 | unavailable | complete (1/1 records) | 0.000 | 0.000 | unknown | unknown | unknown | unknown | 0.000 | 0.000 |
| julia/choice | C10 | unavailable | complete (1/1 records) | 0.000 | 0.000 | unknown | unknown | unknown | unknown | 0.000 | 0.000 |
| julia/choice | C11 | unavailable | complete (1/1 records) | 0.000 | 0.000 | unknown | unknown | unknown | unknown | 0.000 | 0.000 |
| julia/noul | C01 | unavailable | complete (14/14 records) | 84.244 | 327.625 | 4.285 | 16.719 | 79.959 | 310.906 | 84.244 | 327.625 |
| julia/noul | C02 | unavailable | complete (49/49 records) | 790.808 | 2713.219 | unknown | unknown | 790.415 | 2712.781 | 790.808 | 2713.219 |
| julia/noul | C03 | unavailable | complete (5/5 records) | 0.015 | 0.000 | unknown | unknown | unknown | unknown | 0.015 | 0.000 |
| julia/noul | C04 | unavailable | complete (7/7 records) | 0.021 | 0.016 | unknown | unknown | unknown | unknown | 0.021 | 0.016 |
| julia/noul | C05 | unavailable | complete (2/2 records) | 0.005 | 0.000 | unknown | unknown | unknown | unknown | 0.005 | 0.000 |
| julia/noul | C06 | unavailable | complete (9/9 records) | 0.017 | 0.000 | unknown | unknown | unknown | unknown | 0.017 | 0.000 |
| julia/noul | C07 | unavailable | complete (39/39 records) | 0.168 | 0.172 | unknown | unknown | unknown | unknown | 0.168 | 0.172 |
| julia/noul | C08 | unavailable | complete (1/1 records) | 0.002 | 0.016 | unknown | unknown | unknown | unknown | 0.002 | 0.016 |
| julia/noul | C09 | unavailable | complete (1/1 records) | 0.002 | 0.000 | unknown | unknown | unknown | unknown | 0.002 | 0.000 |
| julia/noul | C10 | unavailable | complete (1/1 records) | 0.002 | 0.000 | unknown | unknown | unknown | unknown | 0.002 | 0.000 |
| julia/noul | C11 | unavailable | complete (1/1 records) | 0.002 | 0.000 | unknown | unknown | unknown | unknown | 0.002 | 0.000 |
| llm/noul | C01 | complete | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C02 | unavailable | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C03 | unavailable | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C04 | complete | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C05 | complete | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C06 | complete | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C07 | unavailable | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C08 | unavailable | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C09 | complete | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C10 | complete | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C11 | complete | complete (1/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |

| Implementation | Attempted calls | Provider input tokens | Provider output tokens |
| --- | --- | --- | --- |
| llm/noul | 11 | unknown | unknown |

Provisioning/load evidence: {"complete_environment_download_bytes": null, "complete_installed_bytes": null, "created_environment": true, "direct_wheels_minimum_bytes": 134255956, "downloaded_weights": true, "environment_path": "D:\\Projects\\daodan\\evals\\senior-review\\choicer-eval\\.cache\\uv", "model_cache_path": "D:\\Projects\\daodan\\evals\\senior-review\\choicer-eval\\.cache\\huggingface", "planned_tokenizer_bytes": 34363188, "planned_weights_bytes": 577189056}

## Coverage, anomalies and authorization gates

| Implementation | Unavailable case | Reason |
| --- | --- | --- |
| julia/choice | C01 | Non-success records: error |
| julia/choice | C02 | Non-success records: error |
| julia/choice | C03 | Non-success records: error |
| julia/choice | C04 | Non-success records: error |
| julia/choice | C05 | Non-success records: error |
| julia/choice | C06 | Non-success records: error |
| julia/choice | C07 | Non-success records: error |
| julia/choice | C08 | Non-success records: error |
| julia/choice | C09 | Non-success records: error |
| julia/choice | C10 | Non-success records: error |
| julia/choice | C11 | Non-success records: error |
| julia/noul | C01 | Non-success records: error |
| julia/noul | C02 | Non-success records: error |
| julia/noul | C03 | Non-success records: error |
| julia/noul | C04 | Non-success records: error |
| julia/noul | C05 | Non-success records: error |
| julia/noul | C06 | Non-success records: error |
| julia/noul | C07 | Non-success records: error |
| julia/noul | C08 | Non-success records: error |
| julia/noul | C09 | Non-success records: error |
| julia/noul | C10 | Non-success records: error |
| julia/noul | C11 | Non-success records: error |
| llm/noul | C02 | Non-success records: error |
| llm/noul | C03 | Non-success records: error |
| llm/noul | C07 | Non-success records: error |
| llm/noul | C08 | Non-success records: error |

| Anomaly source | Recorded evidence |
| --- | --- |
| execution | The verbatim REVIEWER_CHOICER returns selections, not probabilities. LLM ECE is unavailable. |
| execution | The full-review LLM baseline cannot become a single-choice control without changing its prompt; it is reused for comparison with both local variants. |
| execution | No case supplies symbol cards. Graph evidence is unavailable, not inferred. |
| execution | tier_router.py named in the design is absent from this checkout; this evaluates the specified prompt, not a proved installed routing implementation. |
| execution | Missing DO NOT TRIGGER WHEN is encoded as an empty false criterion and reported, never paraphrased or invented. |
| execution | Julia advertises a separate 48-token option limit. Exact criteria that exceed it are recorded as failures, not truncated. |
| execution | Three noul false criteria are empty because the real catalog omits them. The pinned Julia validator requires nonempty descriptions; those questions are unsupported before any weights are downloaded. |
| execution | There is no positive premise-auditor label among the ten labeled cases. The full critical-role condition cannot be established by this pilot. |
| execution | Tokenizer validation confirmed that the exact 18-role choice descriptions violate Julia option/head limits. Every original choice request is rejected before inference; execution/julia-option-capacity.json records capacity evidence. |
| execution | Native gpt-6-luna was the authorized available economical A binding. Comparative pricing and live tier1 discovery were not verified; provider-reported model identity is unavailable. |
| execution | No paired per-case cold/warm repeats have been performed. First actual inference cold and subsequent calls warm are recorded separately from load cost. |
| execution | The optional task-tier experiment and secondary laya inference were not performed. |
| execution | The design source changed concurrently after prompt extraction. Frozen prompt and request hashes are preserved; execution/final-verification.json records which prompt bodies are unchanged. No spec edits were made by this benchmark task. |
| execution | The native baseline uses isolated file-loader tasks. Exact loader prompts and responses are saved; the host does not expose provider identity, token counts, API call counts, finish reasons or inference timing. |
| execution | Four native baseline outputs fail the frozen response contract; raw declarations remain evidence and are not silently repaired. |
| execution | The original Julia state-only tokenizer audit finds four oversized hunks across C02 and C07. The adapted experiment excludes both whole cases before inference, without rewriting any remaining hunk. |
| execution | Input-side binding is missing: passing A citation checks verifies hunk/path/line/snippet only, not the base/candidate marker requested by the frozen prompt. |
| execution | Original local execution retained 23 valid-subset classifications, then switched to atomic full-catalog validation after universal criterion incompatibility was established. Remaining 106 binary and 129 categorical attempts did not perform classifier inference. |
| execution | Per-case wall/CPU counts recorded attempts, including validation; mixed batching and interrupted work preclude a controlled model-speed comparison. |
| dataset | {"case_id": "C02", "detail": "Precision-only must_not_report case has no Expected dimension table; exclude from recall, false activations and calibration.", "kind": "missing_reviewer_ground_truth"} |
| dataset | {"case_id": "C10", "detail": "Case requests payments/models.py with no unique constraint but supplies no model source. Only verbatim service code is materialized; no schema is invented.", "kind": "unspecified_companion_model"} |
| dataset | {"detail": "All 11 case inputs omit symbol cards because the source cases supply none.", "kind": "no_supplied_symbol_cards"} |
| dataset | {"detail": "The labeled case tables contain no premise expected role; premise recall is unmeasurable in this pilot.", "kind": "no_positive_premise_label"} |
| dataset | {"detail": "Expected dimension attributes known defects. Treat non-listed roles as negatives only for the requested pilot proxy; a selected role may be relevant without owning a listed defect.", "kind": "case_labels_are_not_exhaustive_trigger_labels"} |
| dataset | {"detail": "The spec prompt is the baseline definition; do not describe it as a verified live implementation.", "kind": "proposed_router_not_in_working_tree", "observed": true} |
| catalog | {"kind": "missing_negative_trigger", "policy": "Preserve null; do not invent a negative criterion.", "roles": ["platform-engineering:platform-reviewer", "senior-review:distributed-flow-auditor", "senior-review:ui-race-auditor"]} |
| catalog | {"kind": "missing_positive_trigger", "policy": "Preserve null; do not invent a positive criterion.", "roles": []} |
| catalog | {"claim": "approximately 20 or 20+", "kind": "spec_role_count", "observed": 18} |
| catalog | {"kind": "current_security_trigger_differs_from_proposed_spec", "policy": "Use actual role frontmatter, never the replacement proposed in spec section 3.1."} |
| llm/noul / C01 | H3: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C01 | H11: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C01 | H5: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C02 | H3: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C02 | H4: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C02 | H3: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C03 | H3: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C04 | H1: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C07 | H38: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C07 | H28: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C07 | H29: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C07 | H27: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C07 | H23: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C08 | H1: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C08 | H1: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C09 | H1: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C09 | H1: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C10 | H1: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C10 | H1: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C10 | H1: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |
| llm/noul / C11 | H1: citation side 'candidate' is not independently verified; the supplied evidence omitted a side binding. |

Authorization gates: [{"evidence": "execution/julia-authorization.json", "gate": "uv environment", "status": "Explicitly authorized by user; created only under benchmark .cache/uv"}, {"evidence": "execution/julia-authorization.json", "gate": "Julia weights", "status": "Explicitly authorized by user; pinned snapshot downloaded under benchmark .cache/huggingface"}, {"actual_provider_tokens": null, "gate": "paid LLM baseline", "status": "Explicitly authorized by user: 11 gpt-6-luna case tasks, 184073 input-token planning estimate (characters/4); 11 completed, no reruns"}, {"gate": "reviewer adaptation", "status": "User authorized reviewer adaptation; kept in a separate experiment, without further paid baseline calls"}]

## Verdict and token economics

The candidate rejected exact critical-role criteria in every observed encoding for senior-review:premise-auditor. This pilot rejects compatibility with this run's catalog; partial answers do not establish full routing quality.

| Critical role | Paired labeled support | A false negatives | B false negatives | B no worse than A |
| --- | --- | --- | --- | --- |
| senior-review:security-auditor | 0 | unknown | unknown | unknown |
| senior-review:premise-auditor | 0 | unknown | unknown | unknown |
| senior-review:data-integrity-auditor | 0 | unknown | unknown | unknown |

Net tokens saved per run = tier1 Choicer tokens avoided + tier2/tier3 tokens avoided by finer routing - routing-error and retry token costs. Net savings: unknown. Downstream tier2/tier3 spend avoided and routing-error/retry token costs are not measured by this pilot.

This small, fixed case set is a pilot. It can inform whether to open shadow observation on the Decision Log. It cannot establish statistical non-inferiority, downstream token savings or promotion to default. The model-card benchmark scores are excluded from that decision.

## Proposed spec update

Revise sections 7.5/8 to distinguish the reviewer-activation pilot's partial positive dimension labels from exhaustive trigger labels: the credential-refill precision case has no activation labels and must be excluded from accuracy and calibration, while excess activations and ECE remain descriptive proxies until all legitimate triggers are adjudicated. Keep the noul threshold fixed before evaluation, aggregate probabilities once per case and role, compare only paired complete cases, and report absent critical-role support explicitly. The verbatim LLM prompt supplies selections rather than probabilities, so its ECE is unavailable; categorical choice scores do not substitute for binary probabilities. Preserve the offline pilot as a gate to considering Decision Log shadow observation only, and require measured downstream review/retry costs, positive net token savings and adequate critical-role coverage before any promotion.
