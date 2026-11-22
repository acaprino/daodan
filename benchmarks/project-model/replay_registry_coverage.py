"""Compare two registries with Daodan's current declared-package and filename checkers, per project.

Reads recorded Renovate packages, CI service images, BuildKit base images and go-enry filenames.
The replay omits checkout-only readers, source text and module attribution. An unmatched expected name means
these inputs did not establish it. The archive and expected.json are opened separately; the answer file is never
an input to the matcher. Use modal_stack.py to measure the full stack with real source trees.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "daodan/core"))
import score
import service_registry
import source_files
from premap import dockerfile, enry, renovate
from tree_scope import DEPENDENCY_DIRS

FACETS = ("frameworks", "services")
REGISTRY = "daodan/data/service-registry.json"
# Some catalogues omit the provider in their label. Only a known product ID disambiguates it.
PRODUCT_NAMES = {"gcp.gcs": "Google Cloud Storage", "gcp.kms": "Google Cloud KMS",
                 "gcp.secretmanager": "Google Secret Manager", "gcp.vertex": "Google Vertex AI",
                 "aws.sqs": "Amazon SQS", "aws.ses": "Amazon SES", "aws.cloudfront": "Amazon CloudFront",
                 "firebase.firestore": "Cloud Firestore", "geminiai": "Google Gemini", "app-store": "Apple App Store",
                 "apachetika": "Apache Tika"}


def product_key(ident, name):
    return score._framework(PRODUCT_NAMES.get(ident, name))


def snapshot_filename(path):
    """Snapshot selection that can be checked from an archived path alone."""
    return (path.name not in {"source.json", "expected.json"}
            and not any(part.startswith(".") or part in DEPENDENCY_DIRS for part in path.parts[:-1])
            and not source_files.is_forbidden(path.name)
            and source_files.is_inventory_path(path))


def recorded_project(runs):
    facts = {"packages": []}
    files, excluded = [], set()
    read = []
    for run in runs:
        command, result = run["command"], run["result"]
        if result["returncode"] != 0:
            continue
        program = command["argv"][0]
        if program == "renovate":
            context = SimpleNamespace(inventory=SimpleNamespace(text=lambda _: ""), stated={})
            facts["packages"].extend(renovate.read(context, [], [result])["facts"].get("packages", ()))
            read.append("renovate")
        elif command["tool"] == "renovate" and program == "sh":
            workflow, _ = renovate._workflows(result, lambda _: None)
            facts.setdefault("services", []).extend(workflow.get("services", ()))
            read.append("workflows")
        elif command["tool"] == dockerfile.TOOL:
            builds = dockerfile.read(None, [command], [result])["facts"]
            facts.setdefault("docker_builds", []).extend(builds.get("docker_builds", ()))
            read.append("buildkit")
        elif program == "daodan-enry":
            for row in json.loads(result["stdout"]):
                path = PurePosixPath(row["path"])
                if any(part.startswith(".") for part in path.parts[:-1]):
                    continue
                if any(row.get(reason) for reason in enry.WHY):
                    excluded.add(row["path"])
                elif snapshot_filename(path):
                    files.append(row["path"])
            read.append("go-enry")
    packages = [p for p in service_registry.step1_packages(None, facts) if p[2] not in excluded]
    return service_registry.Project(packages, sorted(files), lambda _: []), sorted(set(read))


def detected(entries, project):
    by_id = {entry["id"]: entry for entry in entries}
    found = {facet: {} for facet in FACETS}
    for checker in (service_registry.check_packages, service_registry.check_files):
        for ident, value, path, _line in checker(entries, project)["signs"]:
            entry = by_id[ident]
            facet = "services" if service_registry.entry_category(entry) == "service" else "frameworks"
            found[facet].setdefault(product_key(ident, entry["name"]), {"id": ident, "value": value, "path": path})
    return found


def catalogue_inputs(entries):
    """Which sign types the candidate can use for the same scored name and facet."""
    known = {facet: {} for facet in FACETS}
    for entry in entries:
        facet = "services" if service_registry.entry_category(entry) == "service" else "frameworks"
        kinds = known[facet].setdefault(product_key(entry["id"], entry["name"]), set())
        kinds.update(kind for kind, rules in (entry.get("signs") or {}).items() if rules)
    return known


def measure(base, candidate):
    specfy = json.loads((HERE / "results/specfy_stack_analyser.json").read_bytes())
    specfy_names = {e["id"]: e["name"] for e in base if "stack-analyser" in e.get("from", ())}
    known = catalogue_inputs(candidate)
    counts = {facet: Counter() for facet in FACETS}
    cases = {}
    for golden in sorted((HERE / "fixtures").glob("*/expected.json")):
        fixture = golden.parent.name
        expected = json.loads(golden.read_bytes())
        archive = HERE / "results/premap-runs" / f"{fixture}.json.gz"
        case = {"recording": archive.exists()}
        cases[fixture] = case
        if archive.exists():
            with gzip.open(archive, "rt", encoding="utf-8") as stream:
                project, case["sources"] = recorded_project(json.load(stream)["runs"])
            before, after = detected(base, project), detected(candidate, project)
        original = specfy["fixtures"].get(fixture)
        upstream = None
        if original and not original.get("error"):
            # The archived framework face intentionally filters e.g. Vite as a builder. Use all its emitted IDs.
            upstream = {product_key(ident, specfy_names.get(ident, ident)) for ident in original["ids"]}
            upstream.update(score._framework(ident) for ident in original["ids"])
            upstream.update(score._framework(row["name"]) for facet in FACETS for row in original["output"].get(facet, ()))
        for facet in FACETS:
            if facet in (expected.get("unknown") or []):
                continue
            wanted = {score._framework(row["name"]): row["name"] for row in expected.get(facet, ())}
            summary = counts[facet]
            summary["expected_all"] += len(wanted)
            detail = case[facet] = {}
            if upstream is not None:
                summary["expected_on_specfy_recordings"] += len(wanted)
                summary["specfy_found"] += len(wanted.keys() & upstream)
                detail["specfy_missed"] = sorted(wanted[k] for k in wanted.keys() - upstream)
            if not archive.exists():
                detail["unverified"] = sorted(wanted.values())
                continue
            old, new = before[facet], after[facet]
            old_hits, new_hits = wanted.keys() & old.keys(), wanted.keys() & new.keys()
            gained, lost = sorted(new_hits - old_hits), sorted(old_hits - new_hits)
            added_other = sorted(new.keys() - old.keys() - wanted.keys())
            summary.update({"expected_on_replay": len(wanted), "baseline": len(old_hits), "candidate": len(new_hits),
                            "outside_expected_before": len(old.keys() - wanted.keys()),
                            "outside_expected_after": len(new.keys() - wanted.keys()),
                            "gained": len(gained), "lost": len(lost), "added_outside_expected": len(added_other)})
            if upstream is not None:
                missed = wanted.keys() - upstream
                summary.update({"specfy_misses_on_common_recordings": len(missed),
                                "baseline_recovers_specfy_misses": len(missed & old_hits),
                                "candidate_recovers_specfy_misses": len(missed & new_hits)})
                detail["recovered_specfy_misses"] = {wanted[k]: new[k] for k in sorted(missed & new_hits)}
            missing = {}
            for key in sorted(wanted.keys() - new_hits):
                rules = known[facet].get(key)
                if rules is None:
                    reason = "no_catalogue_name_in_facet"
                elif not rules & {"files", "packages", "patterns"}:
                    reason = "no_package_or_file_rule"
                else:
                    reason = "no_matching_recorded_declaration"
                missing[wanted[key]] = reason
                summary[reason] += 1
            detail.update({"gained": {wanted[k]: new[k] for k in gained}, "lost": {wanted[k]: old[k] for k in lost},
                           "missing": missing,
                           "added_outside_expected": [new[k] for k in added_other]})
    return {"cases": len(cases), "recordings": sum(c["recording"] for c in cases.values()),
            "specfy_recordings": sum(1 for e in specfy["fixtures"].values() if not e.get("error")),
            "summary": counts, "fixtures": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, help="Git revision of the original distributed registry")
    parser.add_argument("--registry", type=Path, default=REPO / REGISTRY, help="candidate distributed registry")
    parser.add_argument("--out", required=True, type=Path, help="write case-by-case evidence, gains, losses and gaps")
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options",
                                        args.baseline + "^{commit}"], cwd=REPO, text=True).strip()
    old = json.loads(subprocess.check_output(["git", "show", f"{revision}:{REGISTRY}"], cwd=REPO))
    candidate = args.registry.read_bytes()
    result = measure(old["entries"], json.loads(candidate)["entries"])
    result["baseline_revision"] = revision
    result["candidate_sha256"] = hashlib.sha256(candidate).hexdigest()
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "fixtures"}, indent=2))


if __name__ == "__main__":
    main()
