# Choicer adapted-catalog exploration

This adapted-catalog experiment has no matched LLM baseline. Local results are exploratory and cannot establish replacement quality or critical-role non-inferiority.

Recorded date: 2026-10-20T10:28:49.347393+00:00. Evidence directory: evals/senior-review/choicer-eval/runs/20261020T100258Z-adapted.

## Protocol and scope

The dataset contains 9 cases, 9 with expected reviewer dimensions and 0 without activation labels. The catalog contains 18 reviewer roles; 41 hunks were materialized.

This run uses separately authored criteria and a tokenizer-selected subset. It is not equivalent to the original exact-catalog experiment. Original A outputs are reference material only unless a new baseline was measured on these same adapted criteria.

Expected dimensions are known positive review lenses, not an exhaustive annotation of every legitimate trigger. Consequently, 'false activations' below mean benchmark-excess selections only. They do not establish wasted reviewer tokens or irrelevant reviews. ECE likewise uses proxy negatives and is descriptive, not validated calibration of reviewer relevance.

0.5 fixed a priori; the full empirical curve is descriptive and must not select the reported threshold.
The scoring JSON retains every achievable selection set on the empirical threshold curve, including the inclusive >= boundary, plus a fixed display grid. No best threshold is selected.

Incomplete, failed, duplicate, or blocked cases never become negative predictions.
Comparative metrics use the same complete cases on both sides. Model-level summaries also state their own coverage, which can differ.
Neither partial-capability answers nor raw-declared LLM selections enter any paired comparison or replace a primary prediction.

LLM baseline validation: Accepted under limited citation checks: registered role, hunk ID, exact supplied path and line, snippet occurrence, tier/effort and reason constraints. Frozen hunk inputs omit base/candidate bindings, so side claims are unverified. This is not full schema/evidence conformance or proof of semantic reviewer relevance.
For A, 'complete' means accepted under those limited checks. The original request inputs remain frozen; side warnings are retained with each response.

### Materialization and leakage boundary

Catalog adaptation: {"equivalent_to_original_catalog": false, "kind": "Separately authored criteria and compact choice descriptions", "original_extraction_provenance_retained": true, "source": "adapted_reviewers.json"}

Recorded subset rule and exclusions: {"excluded_case_ids": ["C02", "C07"], "full_question_encoding_still_required": true, "original_case_count": 11, "overflow_evidence": [{"case_id": "C02", "hunk_id": "H32", "sequence_limit": 8192, "state_alone_exceeds_sequence_limit": true, "state_tokens": 21251}, {"case_id": "C02", "hunk_id": "H33", "sequence_limit": 8192, "state_alone_exceeds_sequence_limit": true, "state_tokens": 41219}, {"case_id": "C07", "hunk_id": "H22", "sequence_limit": 8192, "state_alone_exceeds_sequence_limit": true, "state_tokens": 22647}, {"case_id": "C07", "hunk_id": "H28", "sequence_limit": 8192, "state_alone_exceeds_sequence_limit": true, "state_tokens": 10309}], "remaining_hunks_rewritten": false, "rule": "Exclude an entire case if any original state alone exceeds Julia's sequence limit.", "selection_uses_labels_or_predictions": false}

The following source-materialization rules describe the original corpus; the recorded subset above determines which cases remain here.

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

Current trigger criteria, missing negatives and compact choice descriptions were authored for this separate adaptation. Original extracted text, field status and rationale remain in the catalog as provenance; they do not make the adapted wording verbatim or equivalent.

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
| julia/choice | {"batch_size": 1, "checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 32.703125, "load_sessions": [{"batch_size": 1, "checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 32.703125, "load_started_at": "2026-10-20T10:56:02.371998+00:00", "load_wall_seconds": 33.375859300023876, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "require_complete_catalog": true, "revision": "a85b127321d580d65176c89ced8273f305745d85", "session_id": "choice-2026-10-20T10:56:02.371998+00:00", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"}], "load_started_at": "2026-10-20T10:56:02.371998+00:00", "load_wall_seconds": 33.375859300023876, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "require_complete_catalog": true, "revision": "a85b127321d580d65176c89ced8273f305745d85", "session_id": "choice-2026-10-20T10:56:02.371998+00:00", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"} |
| julia/noul | {"batch_size": 1, "checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 33.203125, "load_sessions": [{"batch_size": 1, "checkpoint_files": {"config.json": "da8dc5e01fa7c23035ac5b9f02979ba114aac6fc039d7635f56e8043ef8f9672", "encoder/config.json": "c79cda42d42ddf777218254845ce92fb25a10dc35874be40d06abd707894523d", "inference-policy.json": "415468ae1c229186e63a277b2fd2e5ee3bbf4c00655125c0e43e01d5a8406e8a", "julia/__init__.py": "02485eb4dd7dadd13907380d1a9c3398709bd8af54b3e0e12b3061a3ebb5c1da", "julia/cuda.py": "138ab63182f25473ce3886296c47ac44e94fc50ae5270927ae4c373f7bb49137", "julia/data.py": "e3510fa4152ec11fa193046715991f44d7c2f85fd2488a98ef11c9d3db23da4e", "julia/inference.py": "79b4e716365a6e07da4580ead725d5b76d06ef3a824a3ec23738feba64704b36", "julia/model.py": "ef2ba82fe20cdf0db7bb887e9ef075476ed08b985ce9a95be0de3e26246ecc81", "julia/probabilities.py": "2a0197d2e0fa5a3c4b06b93599a85706724df7b0d2cc821a13ed293aef59f206", "julia/router/__init__.py": "832cf0a44569941efba66dfa7099b645fdb1084082e40c6115bb0ac5edd78a96", "julia/router/build.py": "ea059c3a97425cadb1068fe41626b6d3bcd77e1efccfc154dbde29352c432ed9", "julia/router/encoder.py": "df25efee2ed916d52af9c4e9c0d98e80854ca70bbfc8140f1de871f290fd3238", "julia/router/engine.py": "91bb30987ff8626ed1610955c6fd796939a5d271e2405b73f8674ccb947eb931", "julia/router/native.py": "42bdba5ea7d874e1f53b2f17e99e731789611b5bd6734f687eaa2b0262c5d7ae", "julia/router/router.py": "624b0b82fd34e4c6874a37595fa91a1d79553d0ca9d8111ef8330ed805f6be7c", "julia/router/specialize.py": "4ba766a45785da0f48898143eb04e13bdf736019a8ba76b71ad84a4bfec8b2d9", "julia/router/tests/synthetic.py": "f2b37bd6ceaf184449f1037b6aa8fda3bcb6263c76b3d11453c11c18d23d0196", "julia/router/tests/test_engine.py": "eb91ee1963400cb732350dadb7f5e39cb68917c6314ca8039e24974310364d52", "julia/router/tests/test_router.py": "e4df6d1f7d0962d0b5b119572d2d3897f1f4cadaa72600f26f3e72090a49172b", "julia/router/transformer.py": "0ce04fab361ca4e8bed636c615e5a6e178fa1a52332db34457e5235c667e1786", "julia/typed.py": "ed89e66a70fcedac1339347bd8fcca69fd2cd1a31535ad0148dae42c610b544d", "julia_config.json": "b9b881646beeac5414eaa78b39d3fe89ff8a2c062731ad718432620f9aee6bf7", "metrics/accuracy-20260924.json": "7d3613bca83a255b9d6da313cc7f849c9c559a0485c55bf37565fd14673c544b", "metrics/context-8k-smoke.json": "1c5aa2aee7946ec0070a735953ef13f31a4c1b6a03543e37df4d48c256c06eec", "metrics/typed-cpu-20260926.json": "5d51e84097d629cfb0f5c14d90bcbbfd467d2d25252adfb4e86ae16db083746c", "metrics/validation.json": "c1dd9a94af32066a38db43410323ec23c1db73af5966109c9a9a25e102f8fa9e", "model.safetensors": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72", "provenance.json": "d3322e07820ad33b38e4bf5b4c4833c6b7e858ca553754fb8cac682ee802fd25", "tokenizer/tokenizer.json": "609d8f4c067cd3950f88594c5a802616cea245823836ef5848ee4fc40aab5b6f", "tokenizer/tokenizer_config.json": "6b069e57db0ce0794c22547725275f22618809c4ef4249307337e651a0dfef8c"}, "device": "cpu", "load_cpu_seconds": 33.203125, "load_started_at": "2026-10-20T10:45:37.597971+00:00", "load_wall_seconds": 34.124335400003474, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "require_complete_catalog": true, "revision": "a85b127321d580d65176c89ced8273f305745d85", "session_id": "noul-2026-10-20T10:45:37.597971+00:00", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"}], "load_started_at": "2026-10-20T10:45:37.597971+00:00", "load_wall_seconds": 34.124335400003474, "marker_only_head": false, "max_length": 8192, "precision": "FP32", "repo": "SupersonicLabs/Julia-1", "require_complete_catalog": true, "revision": "a85b127321d580d65176c89ced8273f305745d85", "session_id": "noul-2026-10-20T10:45:37.597971+00:00", "strict_encoding": true, "threads": 4, "versions": {"huggingface-hub": "1.33.0", "numpy": "2.5.4", "safetensors": "0.8.0", "torch": "2.14.0", "transformers": "5.0.0"}, "weight_bytes": 577189056, "weight_sha256": "df853bf7fe424420011f3d0c47a05d7341aa9eefa7fb9f203ea4aada4ad95b72"} |
| llm/noul | unknown |

Hardware: {"cpu_model": "Intel(R) Core(TM) Ultra 7 155H", "gpu": "unused; CPU protocol", "logical_cpus": 22, "machine": "", "platform": "Windows-11-10.0.26200-SP0", "python": "3.13.14", "ram_bytes": 33775378432, "ram_measurement_evidence": "../20261020T100258Z/execution/hardware-memory.json"}

Provenance: {"entry_sha256": "9f50b0c20a314af3ab8357f30e3256dda6860d6132367c8deca9fe83d8496c45", "final_evaluator_sources": {"adapt_reviewers_blind.py": "58e3f9bf7241ef06b9b33cccc38a925507d258903f5ff6e9b6cea8961277afbd", "dataset.py": "d6fbd713ac791b52e0fa29f879ad0709c15bc94f6945534dd67ca2af0de06725", "metrics.py": "c5cafd06db1960d11536d155ba7074ad9e996f97cbdd507412f89f778b7bd1f5", "prepare_adapted.py": "0d423825b306a69b420d6ea617c20abd41fd858dfec6ed1a7fb9100c55f4d9ce", "run_eval.py": "d8b18e7e7d7b68cb6cc39b33c7359661e962c61d3502fee5094a3be033b87573", "summarize_runs.py": "cb408a3932b810c5990f90cbd172f8cde63ec6897e439ca58a84d1da3ab396b9", "test_adaptation.py": "a5ee610bdfcba535dbef1e90e93e1ee3582d7ca7e294b3d44bec7ff9b5485dec", "test_inputs.py": "d6cc1aa32dbbd636ad49986df7f5ed2d998b16d546cddecb961bbf6343f689cc", "test_llm_validation.py": "c696f8d26df9cc73a36723a582b08eacb21f7bd47fff8c11a7e94f73e0bd2e72", "test_metrics.py": "813a51540fcc8173fb120f199387056135e63b674847882ecb2fa4d9172cc07a", "test_runtime.py": "fd44ccf80dd3dc1591e79a4c122c5f3c57ed9959a83a72311c8cd25a54aa21e7"}}

Model-card accuracy, context size, format and speed claims are not measurements of this pilot. Unknown identity, revision, weight hash, precision and runtime fields remain unknown until recorded by execution.

## Reviewer activation metrics

| Implementation | Complete cases | Labeled cases scored | Expected-role recall | Critical recall | Benchmark excess / labeled case | Descriptive ECE |
| --- | --- | --- | --- | --- | --- | --- |
| julia/choice | 9/9 | 9 | 0.000 | 0/5 (0.000) | 1.556 | unknown |
| julia/noul | 9/9 | 9 | 0.778 | 5/5 (1.000) | 12.444 | 0.689 |
| llm/noul (limited citation checks) | 0/9 | 0 | unknown | undefined (no labeled support) | unknown | unknown |

| Implementation | Critical role | Recall | False negatives |
| --- | --- | --- | --- |
| julia/choice | senior-review:security-auditor | 0/1 (0.000) | 1 |
| julia/choice | senior-review:premise-auditor | undefined (no labeled support) | undefined |
| julia/choice | senior-review:data-integrity-auditor | 0/4 (0.000) | 4 |
| julia/noul | senior-review:security-auditor | 1/1 (1.000) | 0 |
| julia/noul | senior-review:premise-auditor | undefined (no labeled support) | undefined |
| julia/noul | senior-review:data-integrity-auditor | 4/4 (1.000) | 0 |
| llm/noul (limited citation checks) | senior-review:security-auditor | undefined (no labeled support) | undefined |
| llm/noul (limited citation checks) | senior-review:premise-auditor | undefined (no labeled support) | undefined |
| llm/noul (limited citation checks) | senior-review:data-integrity-auditor | undefined (no labeled support) | undefined |

## Partial-capability diagnostic

This separate view inspects successful questions retained inside failed full-catalog calls. It never fills missing primary predictions, changes the primary recall denominator, or supplies a B set for agreement. A role/case is usable here only when every one of its hunks has an explicitly accepted, untruncated encoding and a finite normalized binary answer. Probabilities are aggregated by maximum at the fixed threshold. Recall is conditional on this stated role-specific coverage.

### julia/noul

| Role | Complete cases for role | Scored / expected positive cases | Scored positive case IDs | Positive hits | Conditional recall | Accepted encodings | Rejected encodings |
| --- | --- | --- | --- | --- | --- | --- | --- |
| abstraction-architect:abstraction-architect-agent | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |
| platform-engineering:platform-reviewer | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |
| react-development:react-performance-optimizer | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |
| repo-hygiene:workspace-auditor | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |
| senior-review:api-contract-auditor | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |
| senior-review:chicken-egg-detector | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |
| senior-review:cleanup-auditor | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |
| senior-review:code-auditor | 9 | 2/2 | C09, C11 | 2 | 1.000 | 41 | 0 |
| senior-review:data-integrity-auditor | 9 | 4/4 | C01, C03, C08, C10 | 4 | 1.000 | 41 | 0 |
| senior-review:distributed-flow-auditor | 9 | 1/1 | C10 | 1 | 1.000 | 41 | 0 |
| senior-review:logic-integrity-auditor | 9 | 3/3 | C04, C05, C10 | 1 | 0.333 | 41 | 0 |
| senior-review:premise-auditor | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |
| senior-review:resource-lifecycle-auditor | 9 | 1/1 | C09 | 0 | 0.000 | 41 | 0 |
| senior-review:security-auditor | 9 | 1/1 | C05 | 1 | 1.000 | 41 | 0 |
| senior-review:temporal-resilience-auditor | 9 | 5/5 | C01, C04, C06, C09, C11 | 4 | 0.800 | 41 | 0 |
| senior-review:ui-race-auditor | 9 | 1/1 | C06 | 1 | 1.000 | 41 | 0 |
| testing:test-suite-auditor | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |
| typescript-development:type-safety-auditor | 9 | 0/0 | (none) | undefined | unknown | 41 | 0 |

Critical roles rejected in every observed encoding: (none). No such rejection is established by the recorded encodings.

## Per-case agreement

B is Julia noul and C is Julia choice on the adapted catalog. A is available only if measured on this same adapted catalog. Original-catalog A responses are not imported into this comparison. Agreement is exact set equality followed by Jaccard overlap.

The unchanged hunk text is shared across the retained cases. Criteria changed, so any comparison to original A belongs in a separately labeled exploratory reference analysis, never a controlled paired result.

| Case | Expected | A selected (limited checks) | B selected | C selected | A/B agreement |
| --- | --- | --- | --- | --- | --- |
| C01 (jupiter-cache-convergence) | `senior-review:data-integrity-auditor`, `senior-review:temporal-resilience-auditor` | unavailable | `platform-engineering:platform-reviewer`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:premise-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor`, `typescript-development:type-safety-auditor` | `platform-engineering:platform-reviewer`, `senior-review:cleanup-auditor` | unavailable |
| C03 (jupiter-economic-events-upsert) | `senior-review:data-integrity-auditor` | unavailable | `platform-engineering:platform-reviewer`, `react-development:react-performance-optimizer`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:premise-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor` | `platform-engineering:platform-reviewer`, `senior-review:cleanup-auditor` | unavailable |
| C04 (jupiter-market-state-tristate) | `senior-review:logic-integrity-auditor`, `senior-review:temporal-resilience-auditor` | unavailable | `platform-engineering:platform-reviewer`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:premise-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor` | `platform-engineering:platform-reviewer`, `senior-review:cleanup-auditor` | unavailable |
| C05 (jupiter-position-notice-owner) | `senior-review:logic-integrity-auditor`, `senior-review:security-auditor` | unavailable | `platform-engineering:platform-reviewer`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:premise-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor` | `platform-engineering:platform-reviewer`, `senior-review:cleanup-auditor` | unavailable |
| C06 (jupiter-trade-failure-drop) | `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor` | unavailable | `platform-engineering:platform-reviewer`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:logic-integrity-auditor`, `senior-review:premise-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor` | `platform-engineering:platform-reviewer`, `senior-review:cleanup-auditor` | unavailable |
| C08 (synthetic-cache-stale-read) | `senior-review:data-integrity-auditor` | unavailable | `platform-engineering:platform-reviewer`, `react-development:react-performance-optimizer`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:premise-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor` | `senior-review:cleanup-auditor` | unavailable |
| C09 (synthetic-connection-pool-leak) | `senior-review:code-auditor`, `senior-review:resource-lifecycle-auditor`, `senior-review:temporal-resilience-auditor` | unavailable | `platform-engineering:platform-reviewer`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:premise-auditor`, `senior-review:security-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor` | `platform-engineering:platform-reviewer` | unavailable |
| C10 (synthetic-payment-double-insert) | `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:logic-integrity-auditor` | unavailable | `platform-engineering:platform-reviewer`, `react-development:react-performance-optimizer`, `repo-hygiene:workspace-auditor`, `senior-review:api-contract-auditor`, `senior-review:chicken-egg-detector`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:distributed-flow-auditor`, `senior-review:premise-auditor`, `senior-review:temporal-resilience-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor`, `typescript-development:type-safety-auditor` | `senior-review:cleanup-auditor` | unavailable |
| C11 (synthetic-retry-storm) | `senior-review:code-auditor`, `senior-review:temporal-resilience-auditor` | unavailable | `platform-engineering:platform-reviewer`, `react-development:react-performance-optimizer`, `senior-review:api-contract-auditor`, `senior-review:cleanup-auditor`, `senior-review:code-auditor`, `senior-review:data-integrity-auditor`, `senior-review:premise-auditor`, `senior-review:ui-race-auditor`, `testing:test-suite-auditor`, `typescript-development:type-safety-auditor` | `senior-review:cleanup-auditor` | unavailable |

| Pair | Paired cases | Paired labeled cases | Exact agreement | Mean Jaccard | Left recall | Right recall | Left excess / case | Right excess / case |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| julia/choice vs julia/noul | 9 | 9 | 0.000 | 0.101 | 0.000 | 0.778 | 1.556 | 12.444 |
| julia/choice vs llm/noul | 0 | 0 | unknown | unknown | unknown | unknown | unknown | unknown |
| julia/noul vs llm/noul | 0 | 0 | unknown | unknown | unknown | unknown | unknown | unknown |

## Calibration

### julia/choice

Categorical choice probabilities are not independent binary P(true) values.

### julia/noul

Descriptive case-role ECE against partial benchmark labels. An absent expected role is a proxy negative, not proof that its review is irrelevant. P(case, role) is the maximum P(true) across that case's hunks.

| Probability bin | Case-role observations | Mean P(true) | Expected-role frequency | Absolute gap |
| --- | --- | --- | --- | --- |
| [0.0, 0.1) | 23 | 0.023 | 0.130 | 0.107 |
| [0.1, 0.2) | 5 | 0.162 | 0.000 | 0.162 |
| [0.2, 0.3) | 4 | 0.240 | 0.000 | 0.240 |
| [0.3, 0.4) | 2 | 0.388 | 0.500 | 0.112 |
| [0.4, 0.5) | 2 | 0.444 | 0.000 | 0.444 |
| [0.5, 0.6) | 4 | 0.554 | 0.000 | 0.554 |
| [0.6, 0.7) | 3 | 0.657 | 0.000 | 0.657 |
| [0.7, 0.8) | 5 | 0.744 | 0.000 | 0.744 |
| [0.8, 0.9) | 6 | 0.860 | 0.333 | 0.527 |
| [0.9, 1.0] | 108 | 0.993 | 0.111 | 0.882 |

### llm/noul

The verbatim REVIEWER_CHOICER emits selections, not P(true); no synthetic confidence.

## Latency and provider tokens

All values are seconds. Full-case totals require one uniquely identified attempt for every expected hunk or case batch, whether that attempt succeeded or failed. They are unknown if a required attempt or component timing is absent. Prediction validity is independent of timing coverage. Known recorded-attempt sums are shown separately for partial cases and never imply a measured full-case duration. Recorded call duration includes question-encoding preflight. Cold/warm rows describe the recorded call phases, not invented repeated trials. CPU is the runner's recorded process CPU time; remote service CPU is unknown. Failed attempted calls remain in operational call and token totals. Model provisioning and load costs are reported separately when supplied in run metadata. Cold means the first inference in a fresh process; the operating-system page cache is not flushed. Repeated warm timing samples, when recorded, do not add prediction votes or calibration observations.

| Implementation | Phase | Timed calls / calls | Wall total | Wall mean | CPU total |
| --- | --- | --- | --- | --- | --- |
| julia/choice | cold | 1/1 | 0.708 | 0.708 | 2.703 |
| julia/choice | warm | 40/40 | 53.413 | 1.335 | 210.188 |
| julia/choice | preflight | 0/0 | unknown | unknown | unknown |
| julia/choice | unknown | 0/0 | unknown | unknown | unknown |
| julia/noul | cold | 1/1 | 5.235 | 5.235 | 20.656 |
| julia/noul | warm | 40/40 | 581.917 | 14.548 | 2191.062 |
| julia/noul | preflight | 0/0 | unknown | unknown | unknown |
| julia/noul | unknown | 0/0 | unknown | unknown | unknown |
| llm/noul | cold | 0/0 | unknown | unknown | unknown |
| llm/noul | warm | 0/0 | unknown | unknown | unknown |
| llm/noul | preflight | 0/0 | unknown | unknown | unknown |
| llm/noul | unknown | 0/0 | unknown | unknown | unknown |

| Implementation | Case | Prediction status | Timing coverage | Full wall | Full CPU | Cold wall | Cold CPU | Warm wall | Warm CPU | Known recorded-attempt wall | Known recorded-attempt CPU |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| julia/choice | C01 | complete | complete (14/14 records) | 16.470 | 64.578 | 0.708 | 2.703 | 15.762 | 61.875 | 16.470 | 64.578 |
| julia/choice | C03 | complete | complete (5/5 records) | 10.129 | 40.016 | unknown | unknown | 10.129 | 40.016 | 10.129 | 40.016 |
| julia/choice | C04 | complete | complete (7/7 records) | 11.756 | 46.203 | unknown | unknown | 11.756 | 46.203 | 11.756 | 46.203 |
| julia/choice | C05 | complete | complete (2/2 records) | 2.700 | 10.641 | unknown | unknown | 2.700 | 10.641 | 2.700 | 10.641 |
| julia/choice | C06 | complete | complete (9/9 records) | 9.140 | 36.047 | unknown | unknown | 9.140 | 36.047 | 9.140 | 36.047 |
| julia/choice | C08 | complete | complete (1/1 records) | 1.088 | 4.281 | unknown | unknown | 1.088 | 4.281 | 1.088 | 4.281 |
| julia/choice | C09 | complete | complete (1/1 records) | 0.986 | 3.828 | unknown | unknown | 0.986 | 3.828 | 0.986 | 3.828 |
| julia/choice | C10 | complete | complete (1/1 records) | 0.893 | 3.500 | unknown | unknown | 0.893 | 3.500 | 0.893 | 3.500 |
| julia/choice | C11 | complete | complete (1/1 records) | 0.958 | 3.797 | unknown | unknown | 0.958 | 3.797 | 0.958 | 3.797 |
| julia/noul | C01 | complete | complete (14/14 records) | 159.595 | 598.203 | 5.235 | 20.656 | 154.360 | 577.547 | 159.595 | 598.203 |
| julia/noul | C03 | complete | complete (5/5 records) | 156.039 | 609.969 | unknown | unknown | 156.039 | 609.969 | 156.039 | 609.969 |
| julia/noul | C04 | complete | complete (7/7 records) | 132.174 | 456.359 | unknown | unknown | 132.174 | 456.359 | 132.174 | 456.359 |
| julia/noul | C05 | complete | complete (2/2 records) | 28.804 | 113.281 | unknown | unknown | 28.804 | 113.281 | 28.804 | 113.281 |
| julia/noul | C06 | complete | complete (9/9 records) | 70.444 | 276.828 | unknown | unknown | 70.444 | 276.828 | 70.444 | 276.828 |
| julia/noul | C08 | complete | complete (1/1 records) | 9.878 | 39.000 | unknown | unknown | 9.878 | 39.000 | 9.878 | 39.000 |
| julia/noul | C09 | complete | complete (1/1 records) | 11.858 | 45.406 | unknown | unknown | 11.858 | 45.406 | 11.858 | 45.406 |
| julia/noul | C10 | complete | complete (1/1 records) | 9.590 | 37.969 | unknown | unknown | 9.590 | 37.969 | 9.590 | 37.969 |
| julia/noul | C11 | complete | complete (1/1 records) | 8.770 | 34.703 | unknown | unknown | 8.770 | 34.703 | 8.770 | 34.703 |
| llm/noul | C01 | unavailable | unavailable (0/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C03 | unavailable | unavailable (0/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C04 | unavailable | unavailable (0/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C05 | unavailable | unavailable (0/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C06 | unavailable | unavailable (0/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C08 | unavailable | unavailable (0/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C09 | unavailable | unavailable (0/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C10 | unavailable | unavailable (0/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| llm/noul | C11 | unavailable | unavailable (0/1 records) | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |

| Implementation | Attempted calls | Provider input tokens | Provider output tokens |
| --- | --- | --- | --- |
| llm/noul | 0 | unknown | unknown |

Provisioning/load evidence: unknown

## Coverage, anomalies and authorization gates

| Implementation | Unavailable case | Reason |
| --- | --- | --- |
| llm/noul | C01 | No prediction records. |
| llm/noul | C03 | No prediction records. |
| llm/noul | C04 | No prediction records. |
| llm/noul | C05 | No prediction records. |
| llm/noul | C06 | No prediction records. |
| llm/noul | C08 | No prediction records. |
| llm/noul | C09 | No prediction records. |
| llm/noul | C10 | No prediction records. |
| llm/noul | C11 | No prediction records. |

| Anomaly source | Recorded evidence |
| --- | --- |
| execution | Criteria and compact choices were authored by a separate agent without cases, labels or outputs. |
| execution | This is a changed-catalog experiment, not a drop-in measurement of the exact kernel criteria. |
| execution | Cases with state-only context overflow are excluded as whole cases using pre-inference token counts. |
| execution | No premise-positive label exists; the full critical-role condition remains untested. |
| execution | No additional paid LLM baseline was executed for these adapted criteria. |
| original dataset provenance | {"case_id": "C02", "detail": "Precision-only must_not_report case has no Expected dimension table; exclude from recall, false activations and calibration.", "kind": "missing_reviewer_ground_truth"} |
| original dataset provenance | {"case_id": "C10", "detail": "Case requests payments/models.py with no unique constraint but supplies no model source. Only verbatim service code is materialized; no schema is invented.", "kind": "unspecified_companion_model"} |
| original dataset provenance | {"detail": "All 11 case inputs omit symbol cards because the source cases supply none.", "kind": "no_supplied_symbol_cards"} |
| original dataset provenance | {"detail": "The labeled case tables contain no premise expected role; premise recall is unmeasurable in this pilot.", "kind": "no_positive_premise_label"} |
| original dataset provenance | {"detail": "Expected dimension attributes known defects. Treat non-listed roles as negatives only for the requested pilot proxy; a selected role may be relevant without owning a listed defect.", "kind": "case_labels_are_not_exhaustive_trigger_labels"} |
| original dataset provenance | {"detail": "The spec prompt is the baseline definition; do not describe it as a verified live implementation.", "kind": "proposed_router_not_in_working_tree", "observed": true} |
| original catalog extraction provenance | {"kind": "missing_negative_trigger", "policy": "Preserve null; do not invent a negative criterion.", "roles": ["platform-engineering:platform-reviewer", "senior-review:distributed-flow-auditor", "senior-review:ui-race-auditor"]} |
| original catalog extraction provenance | {"kind": "missing_positive_trigger", "policy": "Preserve null; do not invent a positive criterion.", "roles": []} |
| original catalog extraction provenance | {"claim": "approximately 20 or 20+", "kind": "spec_role_count", "observed": 18} |
| original catalog extraction provenance | {"kind": "current_security_trigger_differs_from_proposed_spec", "policy": "Use actual role frontmatter, never the replacement proposed in spec section 3.1."} |

Authorization gates: [{"gate": "uv environment", "status": "Previously authorized environment reused"}, {"gate": "Julia weights", "status": "Previously authorized pinned weights reused offline"}, {"gate": "reviewer adaptation", "status": "Explicit user instruction; separate benchmark artifact"}, {"gate": "paid adapted LLM baseline", "status": "Not requested or executed; original A is reference only"}]

## Verdict and token economics

This adapted-catalog experiment has no matched LLM baseline. Local results are exploratory and cannot establish replacement quality or critical-role non-inferiority.

| Critical role | Paired labeled support | A false negatives | B false negatives | B no worse than A |
| --- | --- | --- | --- | --- |
| senior-review:security-auditor | 0 | unknown | unknown | unknown |
| senior-review:premise-auditor | 0 | unknown | unknown | unknown |
| senior-review:data-integrity-auditor | 0 | unknown | unknown | unknown |

Net tokens saved per run = tier1 Choicer tokens avoided + tier2/tier3 tokens avoided by finer routing - routing-error and retry token costs. Net savings: unknown. Downstream tier2/tier3 spend avoided and routing-error/retry token costs are not measured by this pilot.

This small, fixed case set is a pilot. It can inform whether to open shadow observation on the Decision Log. It cannot establish statistical non-inferiority, downstream token savings or promotion to default. The model-card benchmark scores are excluded from that decision.

## Proposed spec update

Revise sections 7.5/8 to distinguish the reviewer-activation pilot's partial positive dimension labels from exhaustive trigger labels: the credential-refill precision case has no activation labels and must be excluded from accuracy and calibration, while excess activations and ECE remain descriptive proxies until all legitimate triggers are adjudicated. Keep the noul threshold fixed before evaluation, aggregate probabilities once per case and role, compare only paired complete cases, and report absent critical-role support explicitly. The verbatim LLM prompt supplies selections rather than probabilities, so its ECE is unavailable; categorical choice scores do not substitute for binary probabilities. Preserve the offline pilot as a gate to considering Decision Log shadow observation only, and require measured downstream review/retry costs, positive net token savings and adequate critical-role coverage before any promotion. Keep separately authored criteria and capacity-selected subsets in distinct experiments with preserved originals, and require a matched baseline on the adapted catalog before drawing controlled comparisons.
