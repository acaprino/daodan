"""Independent artifact and source checks for a prepared or finished Gutsy run."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

from gutsy_followup import HERE, build_prompt, runtime_signature, state_prefix, window_hunks


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(root, complete=False):
    plan = read(root / "plan.json")
    for name, expected in plan["hashes"].items():
        assert sha((root / name).read_bytes()) == expected, name
    slot_mode = plan.get("prefix_mode") == "slot-restore"
    paired = slot_mode and "reference_run" in plan
    if paired:
        reference = HERE / plan["reference_run"]
        for name in plan["hashes"]:
            assert (root / name).read_bytes() == (reference / name).read_bytes(), f"{name} differs from the reference"
    cases, jobs = read(root / "cases.json"), read(root / "jobs.json")
    assert len(jobs) == plan["jobs"]
    assert len({j["id"] for j in jobs}) == len(jobs)
    by_case = {case["id"]: case for case in cases}
    assert len(by_case) == len(cases)
    source_cache, source_checks = {}, 0
    for case in cases:
        prov = case["provenance"]
        repo = prov.get("repo", prov.get("source_repo"))
        rev = prov.get("revision", prov.get("review_revision"))
        for hunk in case["hunks"]:
            assert sha(hunk["text"].encode("utf-8")) == hunk["sha256"]
            key = (repo, rev, hunk["path"])
            if key not in source_cache:
                source_cache[key] = subprocess.check_output(["git", "-C", repo, "show", f"{rev}:{hunk['path']}"])
            blob = source_cache[key]
            if case["id"].startswith("E"):
                assert sha(blob) == prov["blob_sha256"]
            lines = blob.decode("utf-8").splitlines(keepends=True)
            actual = "".join(lines[hunk["start_line"] - 1:hunk["end_line"]])
            assert actual == hunk["text"], (case["id"], hunk["id"])
            source_checks += 1
        recovered = defaultdict(str)
        windows = window_hunks(case["hunks"])
        for w in windows:
            for p in w["pieces"]:
                assert p["offset"] == len(recovered[p["hunk_id"]])
                recovered[p["hunk_id"]] += p["text"]
        assert dict(recovered) == {h["id"]: h["text"] for h in case["hunks"]}
    development = {h["path"] for c in cases if c.get("split") == "development" for h in c["hunks"]}
    verification = {h["path"] for c in cases if c.get("split") == "verification" for h in c["hunks"]}
    assert not development & verification
    groups = defaultdict(list)
    for job in jobs:
        assert set(job) == {"id", "case_id", "mode", "window", "variant", "role", "state", "question", "options"}
        case = by_case[job["case_id"]]
        assert case.get("source_case", "_NO_TITLE_") not in job["state"]
        assert "expected_roles" not in job["state"]
        groups[(job["case_id"], job["mode"], job["window"]["id"], job["role"])].append(job)
    for key, pair in groups.items():
        if key[0].startswith("E"):
            assert len(pair) == 2
            assert {j["variant"] for j in pair} == {"v2", "candidate"}
            assert pair[0]["state"] == pair[1]["state"]
    result = {"status": "passed", "phase": "complete" if complete else "preflight",
              "cases": len(cases), "jobs": len(jobs), "source_hunks_verified": source_checks,
              "source_files_verified": len(source_cache), "split_path_overlap": 0,
              "source_coverage": "all supplied hunk text reconstructs exactly",
              "not_verified": ["semantic citation relevance", "independent applicability labels", "production routing", "full reviewer catalog"]}
    if complete:
        execution = read(root / "execution.json")
        assert execution["status"] == "complete"
        assert execution["completed_calls"] == len(jobs)
        raw = {p.stem: read(p) for p in (root / "wire").glob("Q*.json")}
        assert set(raw) == {j["id"] for j in jobs}
        assert all(r["status"] == "ok" for r in raw.values())
        token_ids = execution["option_token_ids"]
        for j in jobs:
            r = raw[j["id"]]
            prompt = build_prompt(j)
            assert r["prompt_sha256"] == sha(prompt.encode())
            assert r["request"]["prompt"] == prompt
            assert r["response"]["truncated"] is False
            assert r["letter"] in ("A", "B", "Z")
            assert r["response"]["completion_probabilities"][0]["id"] == token_ids[r["letter"]]
        scores = read(root / "scores.json")
        for row in scores["rows"]:
            case = by_case[row["case_id"]]
            observed = [r for r in raw.values() if (r["case_id"], r["mode"], r["variant"]) == (row["case_id"], row["mode"], row["variant"])]
            chosen = {r["role"] for r in observed if r["letter"] == "A"}
            assert chosen == set(row["selected_model"])
            chosen.update(row["selected_fixed"])
            assert chosen & set(case["expected_roles"]) == set(row["matched"])
            assert chosen & set(case.get("negative_roles", [])) == set(row["negative_activations"])
        memory = read(root / "memory.json")
        assert not memory["exceeded"] and memory["error"] is None
        peak = max(s["server"]["rss"] + s["runner"]["rss"] for s in memory["samples"])
        assert peak < plan["memory_limit_bytes"]
        result.update(wire_records_verified=len(raw), sampled_peak_combined_rss=peak,
                      invalid_outputs=0, coverage="all planned calls delivered")
        if paired:
            reference_execution = read(HERE / plan["reference_run"] / "execution.json")
            assert runtime_signature(execution["args"]) == runtime_signature(reference_execution["args"])
            assert execution["model_sha256"] == reference_execution["model_sha256"]
            assert execution["binary_sha256"] == reference_execution["binary_sha256"]
        if slot_mode:
            states = [read(p) for p in sorted((root / "states").glob("S*.json"))]
            transitions = sum(1 for i, j in enumerate(jobs) if i == 0 or j["state"] != jobs[i - 1]["state"])
            assert len(states) == transitions == execution["states_encoded"]
            for state in states:
                assert state["encode"]["timings"]["cache_n"] == 0
                assert state["encode"]["timings"]["prompt_n"] == state["prefix_tokens"]
                assert state["save"]["response"]["n_saved"] == state["prefix_tokens"]
            for j in jobs:
                r = raw[j["id"]]
                timings = r["response"]["timings"]
                assert r["prefix_sha256"] == sha(state_prefix(j).encode())
                assert r["request"]["id_slot"] == 0
                assert r["restore"]["response"]["n_restored"] == r["prefix_tokens"]
                assert r["prefix_reuse_verified"] is True
                assert timings["cache_n"] == r["prefix_tokens"]
                assert timings["cache_n"] + timings["prompt_n"] == r["prompt_tokens"]
            assert execution.get("slot_cleanup") == "removed"
            result.update(prefix_mode="slot-restore", states_verified=len(states), prefix_reuse_verified=len(jobs),
                          server_profile=("identical to the reference except the slot directory" if paired
                                          else "standalone slot-restore run; no paired reference"))
    target = root / ("verification.json" if complete else "preflight-verification.json")
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--complete", action="store_true")
    args = parser.parse_args()
    root = (HERE / args.out).resolve()
    if not root.is_relative_to(HERE / "runs"):
        parser.error("Output must be a benchmark run directory")
    verify(root, args.complete)
