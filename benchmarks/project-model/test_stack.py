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


def test_a_library_and_a_tool_stay_in_the_frameworks_face_and_a_project_of_category_service_is_a_service():
    """`expected.json` lists libraries and tools among its frameworks (Zod, Vite, Jest): the face keeps every class but
    `service`, as before the registry wrote them; Kafka, a `project` of category `service`, is a service."""
    sign = [{"sign": "package", "value": "x", "path": "web/package.json", "line": 3}]
    record = {"technologies": [{"id": "zod", "name": "Zod", "kind": "project", "category": "library", "signs": sign},
                               {"id": "vite", "name": "Vite", "kind": "project", "category": "tool", "signs": sign},
                               {"id": "kafka", "name": "Kafka", "kind": "service", "category": "service", "signs": sign}],
              "units": [{"id": "web", "name": "web", "paths": ["web"], "technologies": ["zod", "vite", "kafka"]}]}
    faces = score.technologies_faces(record)
    assert [(f["name"], f["unit"]) for f in faces["frameworks"]] == [("Zod", "web"), ("Vite", "web")]
    assert faces["services"] == [{"name": "Kafka", "evidence": "web/package.json"}]


def test_a_root_unit_holds_the_signs_of_every_path():
    record = {"technologies": [{"id": "x", "name": "X", "kind": "project", "signs": [
        {"sign": "package", "value": "x", "path": "deep/er/package.json", "line": 1}]}],
        "units": [{"id": "r", "name": "root", "kind": "npm-package", "paths": ["."], "technologies": ["x"]}]}
    assert score.technologies_faces(record)["frameworks"] == [
        {"name": "X", "unit": "root", "evidence": "deep/er/package.json"}]


def test_compaction_keeps_local_declarations_past_the_sample_and_score_ignores_mentions():
    import modal_stack

    signs = [{"sign": "env", "value": "X_TOKEN", "path": f"web/{i}.js", "line": 1, "strength": "mentioned"}
             for i in range(10)]
    signs.extend({"sign": "package", "value": "x", "path": path, "line": 2, "strength": "declared"}
                 for path in ("api/package.json", "web/package.json"))
    record = {"technologies": [{"id": "x", "name": "X", "category": "framework", "kind": "project", "signs": signs}],
              "units": [{"id": name, "name": name, "paths": [name], "technologies": ["x"]} for name in ("web", "api")]}
    expected = [{"name": "X", "unit": name, "evidence": f"{name}/package.json"} for name in ("web", "api")]
    assert score.technologies_faces(modal_stack._trim(record))["frameworks"] == expected
    # Previously stored records did not carry strength and may have already lost the local declaration.
    legacy = {**record["technologies"][0], "signs": [
        {"sign": "env", "path": "web/app.js"}, {"sign": "package", "path": "api/package.json"}]}
    assert score.technologies_faces({**record, "technologies": [legacy]})["frameworks"] == [
        {"name": "X", "unit": "web"}, expected[1]]


def test_configured_services_survive_compaction_without_counting_them_as_catalogue_matches():
    import modal_stack

    configured = [{"name": "mailpit", "path": "compose.override.yml", "declared_in": "compose.override.yml#L3"}]
    trimmed = modal_stack._trim({"technologies": [], "units": [], "configured_services": configured})
    assert trimmed["configured_services"] == configured
    assert score.technologies_faces(trimmed)["services"] == []


def test_modules_with_overlapping_paths_keep_their_own_declaration_in_scored_and_stored_results():
    import modal_stack

    child, parent = "apps/web/next.config.js", "next.config.js"
    record = {"technologies": [{"id": "nextjs", "name": "Next.js", "kind": "project",
                                "signs": [{"sign": "file", "path": path} for path in (child, parent)]}],
              "units": [{"id": name, "name": name, "paths": [directory], "technologies": ["nextjs"],
                         "technology_evidence": {"nextjs": {"path": file}}}
                        for name, directory, file in (("root", ".", parent), ("web", "apps/web", child))]}
    expected = [{"name": "Next.js", "unit": "root", "evidence": parent},
                {"name": "Next.js", "unit": "web", "evidence": child}]
    for result in (record, modal_stack._trim(record)):
        assert score.technologies_faces(result)["frameworks"] == expected


def test_compose_files_in_the_corpus_keep_each_service_name_even_if_built_without_an_image():
    sys.path.insert(0, str(HERE.parents[1] / "daodan/core"))
    from premap.compose import file_services

    cases = {
        "jvm-spring-boot-managed/compose.yaml": {"postgres"},
        "py-fastapi-compose/docker-compose.yml": {"api", "db", "cache"},
        "mix-infra-compose/docker-compose.yml": {"api", "worker", "db", "cache", "queue"},
    }
    for path, names in cases.items():
        rows, gaps = file_services(path, (HERE / "fixtures" / path).read_text(encoding="utf-8"))
        assert not gaps
        assert {row["name"] for row in rows} == names
        assert all(row["declared_in"].startswith(path + "#L") for row in rows)


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
    assert "daodan/data" in paths, paths  # D-287
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
