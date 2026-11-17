"""The `stack` step's record (`technologies.json`) in the corpus' two facets, and the driver that measures it.
Run: python tests/modal_pytest.py benchmarks/project-model/test_stack.py (Modal's client is there)."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import score  # noqa: E402

RECORD = {
    "schema": "daodan/technologies/v1",
    "technologies": [
        {"id": "nextjs", "name": "Next.js", "kind": "project", "signs": [
            {"sign": "package", "value": "next", "path": "web/package.json", "line": 5}]},
        {"id": "react", "name": "React", "kind": "project", "signs": [
            {"sign": "package", "value": "react", "path": "web/package.json", "line": 6},
            {"sign": "package", "value": "react", "path": "api/package.json", "line": 6}]},
        {"id": "eslint", "name": "ESLint", "kind": "project", "signs": [
            {"sign": "package", "value": "eslint", "path": "web/package.json", "line": 9}]},
        {"id": "docker", "name": "Docker", "kind": "project", "signs": [
            {"sign": "file", "value": "Dockerfile", "path": "Dockerfile", "line": None}]},
        {"id": "postgresql", "name": "Postgres", "kind": "service", "signs": [
            {"sign": "package", "value": "postgres", "path": "docker-compose.yml", "line": 4}]},
        {"id": "redis", "name": "Redis", "kind": "service", "signs": [
            {"sign": "package", "value": "redis", "path": "api/package.json", "line": 7}]},
    ],
    "units": [
        {"id": "web", "name": "@acme/web", "kind": "npm-package", "paths": ["web"],
         "technologies": ["nextjs", "react", "eslint"]},
        {"id": "api", "name": "@acme/api", "kind": "npm-package", "paths": ["api"], "technologies": ["react", "redis"]},
    ],
}
EXPECTED = {
    "frameworks": [{"name": "Next.js", "unit": "@acme/web", "evidence": "web/package.json"},
                   {"name": "React", "unit": "@acme/web", "evidence": "web/package.json"},
                   {"name": "Fastify", "unit": "@acme/api", "evidence": "api/server.js"}],
    "services": [{"name": "PostgreSQL", "kind": "database", "evidence": "docker-compose.yml"}],
}


def test_a_project_entry_becomes_a_framework_of_each_unit_that_holds_it():
    faces = score.technologies_faces(RECORD)
    held = {(f["name"], f.get("unit")) for f in faces["frameworks"]}
    assert {("Next.js", "@acme/web"), ("React", "@acme/web"), ("React", "@acme/api")} <= held
    react_api = next(f for f in faces["frameworks"] if f["name"] == "React" and f["unit"] == "@acme/api")
    assert react_api["evidence"] == "api/package.json"  # the sign inside that unit, not the first one


def test_an_entry_no_unit_holds_has_no_unit():
    faces = score.technologies_faces(RECORD)
    docker = [f for f in faces["frameworks"] if f["name"] == "Docker"]
    assert docker == [{"name": "Docker", "evidence": "Dockerfile"}]


def test_a_service_entry_is_a_service_with_its_first_evidence_and_no_unit():
    faces = score.technologies_faces(RECORD)
    assert faces["services"] == [{"name": "Postgres", "evidence": "docker-compose.yml"},
                                 {"name": "Redis", "evidence": "api/package.json"}]
    assert not any(f["name"] in ("Postgres", "Redis") for f in faces["frameworks"])


def test_a_root_unit_holds_the_signs_of_every_path():
    record = {"technologies": [{"id": "x", "name": "X", "kind": "project", "signs": [
        {"sign": "package", "value": "x", "path": "deep/er/package.json", "line": 1}]}],
        "units": [{"id": "r", "name": "root", "kind": "npm-package", "paths": ["."], "technologies": ["x"]}]}
    assert score.technologies_faces(record)["frameworks"] == [
        {"name": "X", "unit": "root", "evidence": "deep/er/package.json"}]


def test_the_score_counts_apart_what_expected_does_not_list_as_a_framework():
    result = score.score_technologies(EXPECTED, RECORD)
    frameworks = result["frameworks"]
    assert frameworks["found"] == 2 and frameworks["missed"] == ["fastify"]
    assert frameworks["extra"] == []  # a library or a tool is not a false framework
    assert set(frameworks["counted_apart"]) == {"eslint", "docker", "react"}  # react: not expected in @acme/api


def test_a_service_nobody_expects_stays_an_extra_and_the_alias_matches_the_name():
    services = score.score_technologies(EXPECTED, RECORD)["services"]
    assert services["found"] == 1  # Postgres is PostgreSQL
    assert services["extra"] == ["redis"] and services["missed"] == []


def test_a_facet_the_expected_file_lacks_scores_nothing_missed():
    result = score.score_technologies({}, RECORD)
    assert result["frameworks"]["expected"] == 0 and result["services"]["expected"] == 0
    assert sorted(result["services"]["extra"]) == ["postgresql", "redis"]


def test_a_failed_fixture_has_no_record_and_no_score():
    assert score.score_technologies(EXPECTED, None) is None


def test_the_driver_uploads_the_data_its_scripts_read_beside_their_folder_and_its_own_files():
    import modal_stack
    paths = {repo for _, repo in modal_stack.UPLOADED}
    assert "plugins/codebase-map/skills/map/data" in paths, paths  # D-287
    assert {"benchmarks/project-model/score.py", "benchmarks/project-model/modal_stack.py"} <= paths


def test_the_driver_batches_the_corpus_without_naming_a_fixture():
    import modal_stack
    names = ["js-a", "js-b", "py-a", "real-svc-x", "real-svc-y", "real-app-z", "mix-q"]
    batches = modal_stack.batches(names, hand=2, real=2)
    assert sorted(n for b in batches for n in b) == sorted(names)
    assert all(len(b) <= 2 for b in batches)
    assert all(len({n.split("-", 1)[0] == "real" for n in b}) == 1 for b in batches)  # no mixed batch


def test_the_name_only_score_ignores_the_unit_and_counts_each_name_once():
    expected = {"frameworks": [{"name": "Next.js", "unit": "packages/web"}, {"name": "React", "unit": "packages/web"},
                               {"name": "React", "unit": "packages/api"}]}
    named = score.score_technologies(expected, RECORD)["frameworks_by_name"]
    assert named["expected"] == 2 and named["found"] == 2  # the unit names differ from `RECORD`'s; the names do not
    strict = score.score_technologies(expected, RECORD)["frameworks"]
    assert len(strict["wrong"]) >= 2  # the same detection, scored with the units, is wrong


def test_the_driver_replays_the_recorded_model_commands_and_runs_none():
    import modal_stack
    paths = {repo for _, repo in modal_stack.UPLOADED}
    assert "benchmarks/project-model/results/premap-runs" in paths  # the answers `modal_premap.py --runs` recorded
    assert "benchmarks/project-model/tools/premap_replay.py" in paths
    assert not hasattr(modal_stack, "_runner")  # no runner of commands: a missing recording leaves them not_run


def test_a_fixture_that_does_not_answer_is_cut_off_with_an_error_and_the_batch_goes_on():
    """Two batches of 17 November 2026 (jellyfin, kuvasz and three more) hit Modal's 1800 s on one fixture and lost
    every record of the batch: each fixture now has its own time, in a process of its own."""
    import time

    import modal_stack
    started = time.monotonic()
    cut = modal_stack.bounded(1, time.sleep, 60)["error"]
    assert cut.startswith("no answer in 1 s; stood at:") and "modal_stack.py" in cut  # the record names where it hung
    assert time.monotonic() - started < 20
    assert modal_stack.bounded(30, dict, a=1) == {"a": 1}
    assert modal_stack.bounded(30, int, "x")["error"].startswith("ValueError: ")
