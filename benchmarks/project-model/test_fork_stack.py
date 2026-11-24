"""The measures the benchmark `modal_stack_fork.py` takes of the `stack` step by stack-analyser: the comparison, the fast
scan, the totals. The translation they measure is `daodan/core/stack_recognition.py`, tested in
`tests/test_codebase_map_stack_recognition.py`.

No test starts Node, reaches the network or runs Modal: `stack_analyser.run` is replaced in every one.

    python -B -m pytest -q -p no:cacheprovider benchmarks/project-model/test_fork_stack.py
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE / "tools"), str(HERE), str(ROOT / "daodan/core")]

import container  # noqa: E402
import fork_stack  # noqa: E402
import premap  # noqa: E402
import service_registry  # noqa: E402
import snapshot  # noqa: E402
import stack_analyser  # noqa: E402
import technologies  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

def evidence(tech, kind, value, path, source="stack-analyser", **more):
    return {"tech": tech, "kind": kind, "value": value, "path": path, "source": source, **more}


def component(*items, childs=()):
    return {"name": "main", "path": ["/"], "tech": None, "techs": [], "childs": list(childs), "evidence": list(items)}


def snapshot_of(work: Path, files: dict[str, str]) -> Path:
    """The manifest of a project of `files`, committed."""
    app = work / "app"
    for rel, text in files.items():
        (app / rel).parent.mkdir(parents=True, exist_ok=True)
        (app / rel).write_text(text, encoding="utf-8", newline="\n")
    for command in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
        subprocess.run(command, cwd=app, check=True, capture_output=True)
    manifest = work / "snapshot/manifest.sqlite"
    snapshot.main(["write", str(app), "--out", str(manifest), "--no-engine", "--no-index", "--no-modules"])
    return manifest


FILES = {"api/pay.py": 'import requests\nURL = "https://api.stripe.com/v1/charges"\n',
         "api/requirements.txt": "redis==5.0\n", "api/gen/out.py": "X = 1\n", "Dockerfile": "FROM python:3.12-slim\n",
         ".gitignore": "node_modules/\n"}
FORK = component(evidence("redis", "package", "redis", "/api/requirements.txt", line=1),
                 evidence("python", "image", "python", "/Dockerfile"), evidence("python", "extension", ".py", "/api"),
                 evidence("redis", "package", "redis", "/api/node_modules/x.js"))
# the tool read `node_modules/x.js` by itself, a file the snapshot lacks: said, not silent
OUTSIDE = {"kind": "evidence_outside_snapshot", "count": 1, "paths": ["api/node_modules/x.js"]}


@pytest.fixture(scope="module")
def manifest(tmp_path_factory):
    """The snapshot of FILES; `node_modules` is on the disk and in the `.gitignore`, never in the snapshot."""
    work = tmp_path_factory.mktemp("fork-stack")
    (work / "app/api/node_modules").mkdir(parents=True)
    (work / "app/api/node_modules/x.js").write_text("var a = 1;\n", encoding="utf-8")
    return snapshot_of(work, FILES)


# ---------------------------------------------------------------------------------------------- compare

def tech(ident, name, category="framework"):
    return {"id": ident, "name": name, "kind": "service" if category == "service" else "project", "category": category,
            "signs": [{"sign": "package", "value": ident, "path": "pyproject.toml", "line": 1, "strength": "declared"}]}


def stored(*entries, units=(), gaps=()):
    """A record as the benchmark stores it (`modal_stack._trim`'s form); the one of the fork keeps its gaps."""
    return {"technologies": list(entries), "units": list(units), "gaps": list(gaps)}


EXPECTED = {"frameworks": [{"name": "FastAPI"}], "services": [{"name": "Redis"}, {"name": "Sentry"}]}
FASTAPI, REDIS_TECH, SENTRY = tech("fastapi", "FastAPI"), tech("redis", "Redis", "service"), tech("sentry", "Sentry", "service")
NONE_LOST = {"lost": [], "gained": [], "new": [], "gone": [], "not_in_registry": []}


def test_compare_names_what_is_lost_gained_and_new():
    before = stored(FASTAPI, REDIS_TECH, SENTRY)
    after = stored(FASTAPI, REDIS_TECH, tech("setuptools", "setuptools"),
                   gaps=[{"kind": "declaration_not_sent", "value": "zlib", "path": "conanfile.txt", "ecosystem": "conan",
                          "detail": "the release takes no declaration of type conan"},
                         {"kind": "not_in_registry", "entry": "setuptools"}])
    assert fork_stack.compare(EXPECTED, before, after) == {
        "lost": ["Sentry"], "gained": [], "new": ["setuptools"], "gone": ["sentry"], "not_in_registry": ["setuptools"]}


def test_compare_of_equal_records_is_empty():
    record = stored(FASTAPI, REDIS_TECH, SENTRY)
    assert fork_stack.compare(EXPECTED, record, stored(FASTAPI, REDIS_TECH, SENTRY, gaps=[])) == NONE_LOST


def test_compare_names_what_the_fork_gains():
    before, after = stored(FASTAPI, REDIS_TECH), stored(SENTRY, FASTAPI, REDIS_TECH)
    assert fork_stack.compare(EXPECTED, before, after) == {**NONE_LOST, "gained": ["Sentry"], "new": ["sentry"]}


def test_compare_lists_the_names_as_the_expected_file_spells_them_sorted_in_each_facet_frameworks_first():
    expected = {"frameworks": [{"name": "Vue"}, {"name": "Django"}], "services": [{"name": "Sentry"}, {"name": "Redis"}]}
    before = stored(tech("vue", "Vue"), tech("django", "Django"), SENTRY, REDIS_TECH)
    assert fork_stack.compare(expected, before, stored())["lost"] == ["Django", "Vue", "Redis", "Sentry"]
    assert fork_stack.compare(expected, stored(), before)["gained"] == ["Django", "Vue", "Redis", "Sentry"]


def test_compare_names_a_name_the_expected_file_repeats_once():
    """A framework in two units is two expected items with one name: 36 fixtures of the corpus repeat one."""
    expected = {"frameworks": [{"name": "React", "unit": "a"}, {"name": "React", "unit": "b"}, {"name": "react", "unit": "c"}],
                "services": [{"name": "Redis"}]}
    before = stored(tech("react", "React"), REDIS_TECH)
    assert fork_stack.compare(expected, before, stored()) == {**NONE_LOST, "lost": ["React", "Redis"], "gone": ["react", "redis"]}
    assert fork_stack.compare(expected, stored(), before) == {**NONE_LOST, "gained": ["React", "Redis"], "new": ["react", "redis"]}


def test_compare_counts_a_name_as_the_score_does_by_alias_and_without_the_unit():
    """`Postgres` is PostgreSQL's alias; a framework is found by its name, whatever unit holds it (or none)."""
    expected = {"frameworks": [{"name": "FastAPI", "unit": "orders-api"}], "services": [{"name": "PostgreSQL"}]}
    unit = {"id": "orders", "name": "orders-api", "kind": "python", "paths": ["app"], "technologies": ["fastapi"],
            "technology_evidence": {"fastapi": {"path": "app/main.py"}}}
    before = stored(FASTAPI, tech("postgresql", "Postgres", "service"), units=[unit])
    after = stored(FASTAPI, tech("postgresql", "PostgreSQL", "service"))
    assert fork_stack.compare(expected, before, after) == NONE_LOST


def test_compare_leaves_out_what_the_expected_file_declares_unknown():
    expected = {**EXPECTED, "unknown": ["services"]}
    # no expected name is lost; `gone` is of the records' ids, whatever the expected file says
    assert fork_stack.compare(expected, stored(FASTAPI, REDIS_TECH), stored(FASTAPI)) == {**NONE_LOST, "gone": ["redis"]}


def test_compare_reads_the_gaps_of_the_record_after_only_and_once_each():
    gaps = [{"kind": "not_in_registry", "entry": "zeta"}, {"kind": "not_in_registry", "entry": "alpha"},
            {"kind": "not_in_registry", "entry": "zeta"}]
    before = {**stored(FASTAPI), "gaps": [{"kind": "not_in_registry", "entry": "before-only"}]}
    assert fork_stack.compare(EXPECTED, before, stored(FASTAPI, gaps=gaps))["not_in_registry"] == ["alpha", "zeta"]
    assert fork_stack.compare(EXPECTED, before, {"technologies": [FASTAPI], "units": []})["not_in_registry"] == []


# ---------------------------------------------------------------------------------------------- executed

GIT = "/usr/bin/git -c core.fsmonitor=false -c core.hooksPath=/dev/null "
NODE_BIN, CLI = "/opt/node-v24.22.3-linux-x64/bin/node", "/opt/stack-analyser/package/dist/cli.mjs"


def executed(*spawned):
    return fork_stack.executed(list(spawned), NODE_BIN, CLI, GIT)


def test_a_project_is_not_executed_when_each_process_is_the_perimeter_s_git_or_node_on_the_release():
    assert executed(GIT + "ls-files -z", f"{NODE_BIN} {CLI} /work/app --output /tmp/o.json", GIT + "rev-parse HEAD") == "no"
    assert executed(f"{NODE_BIN} {CLI}") == "no"  # no argument after the program
    assert executed() == "no"  # no process started


def test_a_process_that_is_neither_is_unknown():
    for other in ("/usr/bin/python3 setup.py build", "/usr/bin/git status", "/usr/bin/git -c core.fsmonitor=false log",
                  "/usr/bin/git -c core.hooksPath=/dev/null -c core.fsmonitor=false log", "git ls-files",
                  f"{NODE_BIN} /work/app/cli.mjs", f"{NODE_BIN} /work/app/x.js {CLI}", NODE_BIN,
                  f"{NODE_BIN} {CLI}x /work/app", f"/usr/local/bin/node {CLI} /work/app",
                  f"{NODE_BIN}-x {CLI} /work/app", f"sh -c {NODE_BIN} {CLI}"):
        assert executed(GIT + "ls-files", other) == "unknown", other


def test_the_command_of_a_real_run_is_judged_as_modal_stack_records_it():
    """`modal_stack` keeps each process as one string of at most 200 characters: a long command is cut after the cli."""
    argv = stack_analyser.command(PurePosixPath(NODE_BIN), PurePosixPath(CLI), PurePosixPath("/work/" + "d" * 150),
                                  PurePosixPath("/tmp/daodan-stack-x/output.json"), PurePosixPath("/tmp/x/declarations.json"),
                                  PurePosixPath("/tmp/daodan-stack-x/perimeter.json"))
    line = " ".join(map(str, argv))[:200]
    assert len(line) == 200 and line.startswith(f"{NODE_BIN} {CLI} /work/")
    assert executed(line) == "no"


# ---------------------------------------------------------------------------------------------- summary

def scored(frameworks, services, expected=(3, 2)):
    return {"frameworks_by_name": {"given": True, "expected": expected[0], "found": frameworks, "missed": [], "extra": [],
                                   "wrong": []},
            "services": {"given": True, "expected": expected[1], "found": services, "missed": [], "extra": [], "wrong": []}}


def done(registry_fast, fork_fast, lost=(), before=(3, 2), after=(3, 2), failed=False):
    return {"compare": {**NONE_LOST, "lost": list(lost)}, "fast": {"registry": [], "fork": [], "lost": []},
            "seconds": {"registry_full": 1.0, "fork_full": 2.0, "registry_fast": registry_fast, "fork_fast": fork_fast},
            "executed_project_code": "no", "score": {"before": scored(*before), "after": scored(*after)},
            "fork_failed": failed}


def test_the_totals_count_the_names_found_before_and_after_the_lost_and_the_errors():
    fixtures = {"a": done(0.4, 0.5, before=(3, 2), after=(2, 2), lost=["Django"]),
                "b": done(0.1, 2.0, before=(1, 1), after=(1, 0), lost=["Redis"]),
                "c": done(0.3, 1.0, before=(2, 1), after=(3, 1)),
                "d": {"error": "no answer in 900 s; stood at: ..."}}
    assert fork_stack.summary(fixtures) == {
        "fixtures": 4, "errors": 1, "fixtures_with_lost": 2, "fork_failed": {"count": 0, "fixtures": []},
        "found": {"frameworks": {"expected": 9, "before": 6, "after": 6}, "services": {"expected": 6, "before": 4, "after": 3}},
        "fork_fast": {"median": 1.0, "max": 2.0, "slowest": "b"},
        "registry_fast": {"median": 0.3, "max": 0.4, "slowest": "a"}}


def test_the_median_of_an_even_number_of_fixtures_is_the_mean_of_the_two_in_the_middle():
    fixtures = {"a": done(0.1, 0.25), "b": done(0.2, 0.75)}
    assert fork_stack.summary(fixtures)["fork_fast"] == {"median": 0.5, "max": 0.75, "slowest": "b"}


def test_the_totals_of_fixtures_without_a_result_have_no_seconds_and_no_score():
    assert fork_stack.summary({"a": {"error": "no stored record: KeyError"}}) == {
        "fixtures": 1, "errors": 1, "fixtures_with_lost": 0, "fork_failed": {"count": 0, "fixtures": []},
        "found": {"frameworks": {"expected": 0, "before": 0, "after": 0}, "services": {"expected": 0, "before": 0, "after": 0}},
        "fork_fast": {"median": None, "max": None, "slowest": None},
        "registry_fast": {"median": None, "max": None, "slowest": None}}


def test_a_fixture_whose_fork_run_failed_is_counted_apart_and_is_not_a_loss_nor_a_time_of_the_fork():
    """A run that failed finds nothing and may end at once or after 300 s: not a loss, not a speed. The registry's own
    time on that fixture is a measure all the same."""
    fixtures = {"a": done(0.4, 0.5, before=(3, 2), after=(2, 2), lost=["Django"]),
                "b": done(0.1, 300.0, before=(1, 1), after=(0, 0), lost=["Redis", "Vue"], failed=True),
                "c": done(0.3, 1.0, before=(2, 1), after=(2, 1))}
    assert fork_stack.summary(fixtures) == {
        "fixtures": 3, "errors": 0, "fixtures_with_lost": 1, "fork_failed": {"count": 1, "fixtures": ["b"]},
        "found": {"frameworks": {"expected": 6, "before": 5, "after": 4}, "services": {"expected": 4, "before": 3, "after": 3}},
        "fork_fast": {"median": 0.75, "max": 1.0, "slowest": "c"},
        "registry_fast": {"median": 0.3, "max": 0.4, "slowest": "a"}}


def test_the_failed_fixtures_are_named_in_the_order_of_their_names():
    fixtures = {"z": done(0.1, 0.1, failed=True), "a": done(0.1, 0.1, failed=True), "m": done(0.1, 0.1)}
    assert fork_stack.summary(fixtures)["fork_failed"] == {"count": 2, "fixtures": ["a", "z"]}


def test_a_facet_the_score_leaves_out_is_not_counted():
    """The expected file's `unknown` takes a facet out of the score: nothing is expected of it."""
    only = {"frameworks_by_name": scored(2, 0)["frameworks_by_name"]}
    entry = {**done(0.1, 0.1), "score": {"before": only, "after": only}}
    assert fork_stack.summary({"a": entry})["found"] == {
        "frameworks": {"expected": 3, "before": 2, "after": 2}, "services": {"expected": 0, "before": 0, "after": 0}}


# ---------------------------------------------------------------------------------------------- measure

@pytest.fixture(scope="module")
def scans(manifest):
    """The pre-map's full facts of FILES, and its fast ones with the packages left out."""
    full = premap.ensure(manifest)
    with open_snapshot(manifest) as store:
        fast = premap.derive(manifest, store, runner=None)
    return full, {**fast, "packages": []}


def listed(record):
    return [t["id"] for t in record["technologies"]]


def modules_of(record):
    return [(m["id"], m["paths"]) for m in record["modules"]]


def test_measure_derives_with_each_recogniser_and_scans_fast_with_each(manifest, scans, monkeypatch):
    full, fast = scans
    calls = []

    def run(project, **kwargs):
        calls.append(kwargs["declarations"])
        return component(*FORK["evidence"], evidence("setuptools", "package", "setuptools", "/api/requirements.txt"))

    monkeypatch.setattr(stack_analyser, "run", run)
    answer = fork_stack.measure(manifest, service_registry.load(), full, fast)
    assert list(answer) == ["before", "after", "fast", "fast_gaps", "seconds"]
    assert listed(answer["before"]) == ["docker", "python", "redis"]  # the registry's own checkers
    assert listed(answer["after"]) == ["python", "redis", "setuptools"]  # the fork's evidence, the registry's records
    assert answer["after"]["gaps"] == [OUTSIDE, {"kind": "not_in_registry", "entry": "setuptools"}]
    assert modules_of(answer["after"]) == modules_of(answer["before"]) == [("app", ["."])]  # one graph under both
    # the registry reads the fast facts without the packages: docker (the Dockerfile) and python; the fork, those it was
    # sent: no declaration, and the evidence it returns whatever it was sent
    assert answer["fast"] == {"registry": ["docker", "python"], "fork": ["python", "redis", "setuptools"], "lost": ["docker"]}
    # one run for the full scan, with the declarations of its facts (the package and the Dockerfile's base), one for the
    # fast scan, with those of its own: none
    assert [sorted(d["name"] for d in sent) for sent in calls] == [["python", "redis"], []]
    assert answer["fast_gaps"] == [OUTSIDE, {"kind": "not_in_registry", "entry": "setuptools"}]  # the fast scan's
    assert list(answer["seconds"]) == ["registry_full", "fork_full", "registry_fast", "fork_fast"]


def test_a_mention_alone_is_not_a_technology_of_the_fast_scan(manifest, scans, monkeypatch):
    """The comparison is by the ids a module could hold: an entry with a declared sign (`technologies.derive`'s rule)."""
    full, fast = scans
    monkeypatch.setattr(stack_analyser, "run", lambda project, **kwargs: component(
        evidence("redis", "env", "REDIS_URL", "/api/pay.py", line=2), evidence("python", "image", "python", "/Dockerfile")))
    answer = fork_stack.measure(manifest, service_registry.load(), full, fast)
    assert answer["fast"]["fork"] == ["python"] and listed(answer["after"]) == ["python"]


def test_measure_puts_service_registry_run_back(manifest, scans, monkeypatch):
    full, fast = scans
    original, started = service_registry.run, []
    monkeypatch.setattr(stack_analyser, "run", lambda project, **kwargs: started.append(1) or FORK)
    fork_stack.measure(manifest, service_registry.load(), full, fast)
    assert service_registry.run is original and len(started) == 2

    real, calls = technologies.derive, []

    def derive(*args):
        calls.append(1)
        if len(calls) == 3:  # the one inside the substitution: the warm-up and the registry's come first
            raise RuntimeError("derive broke")
        return real(*args)

    monkeypatch.setattr(technologies, "derive", derive)
    with pytest.raises(RuntimeError):
        fork_stack.measure(manifest, service_registry.load(), full, fast)
    assert service_registry.run is original


def test_a_fork_that_fails_with_a_gap_is_a_result_and_loses_what_only_it_could_have_found(manifest, scans, monkeypatch):
    full, fast = scans

    def broken(project, **kwargs):
        raise container.Gap("stack-analyser failed (exit 1): boom", "analyze again")

    monkeypatch.setattr(stack_analyser, "run", broken)
    answer = fork_stack.measure(manifest, service_registry.load(), full, fast)
    assert listed(answer["after"]) == [] and answer["fast"]["fork"] == [] and answer["fast"]["lost"] == ["docker", "python"]
    assert [g["kind"] for g in answer["after"]["gaps"]] == ["checker_failed"]
    # the failure of the fast scan is told apart from a loss: the same gap, with its cause
    assert answer["fast_gaps"] == [{"kind": "checker_failed", "checker": "stack-analyser",
                                    "detail": "stack-analyser failed (exit 1): boom (analyze again)"}]


def test_the_first_derive_is_a_warm_up_and_neither_timed_derive_builds_the_module_graph(manifest, scans, monkeypatch):
    """`derive` syncs the module graph the first time and finds it the second: timed first, the registry would pay for
    both. So the registry derives once before the timed calls: three runs of the registry in all (that one, the timed
    one, the fast one), and the fork's two."""
    full, fast = scans
    ran = []
    real = service_registry.run
    monkeypatch.setattr(service_registry, "run", lambda *args: ran.append(1) or real(*args))
    monkeypatch.setattr(stack_analyser, "run", lambda project, **kwargs: FORK)
    fork_stack.measure(manifest, service_registry.load(), full, fast)
    assert len(ran) == 3


def test_each_time_is_the_one_of_its_own_call(manifest, scans, monkeypatch):
    full, fast = scans
    real = service_registry.run

    def slow_registry(*args):
        time.sleep(0.2)
        return real(*args)

    def slow_fork(project, **kwargs):
        time.sleep(0.02)
        return FORK

    monkeypatch.setattr(service_registry, "run", slow_registry)
    monkeypatch.setattr(stack_analyser, "run", slow_fork)
    seconds = fork_stack.measure(manifest, service_registry.load(), full, fast)["seconds"]
    assert seconds["registry_full"] >= 0.2 and seconds["registry_fast"] >= 0.2
    assert seconds["fork_full"] >= 0.02 and seconds["fork_fast"] >= 0.02
    assert all(isinstance(value, float) for value in seconds.values())


# ---------------------------------------------------------------------------------------------- the fork's failures

FAILED_RUN = {"kind": "checker_failed", "checker": "stack-analyser", "detail": "stack-analyser gave no answer within 300 s (check)"}
NOT_SENT = {"kind": "declaration_not_sent", "value": "zlib", "path": "conanfile.txt", "ecosystem": "conan", "detail": "no type"}


def test_the_gaps_of_a_scan_are_counted_by_kind_and_the_failure_of_the_tool_is_told_with_its_cause():
    gaps = [NOT_SENT, {**NOT_SENT, "value": "boost"}, FAILED_RUN, {"kind": "not_in_registry", "entry": "setuptools"},
            {"kind": "checker_failed", "checker": "host", "detail": "ValueError: no lines"}]
    assert fork_stack.fork_gaps(gaps) == {
        "kinds": {"checker_failed": 2, "declaration_not_sent": 2, "not_in_registry": 1},
        "failed": ["stack-analyser gave no answer within 300 s (check)"]}  # the host checker's failure is the registry's
    assert fork_stack.fork_gaps([]) == {"kinds": {}, "failed": []}


def stored_result(*, gaps=(), fast_gaps=(), lost=()):
    """What the container stores for a fixture (`modal_stack_fork._measure`): the fork's records trimmed, its fast scan."""
    before, after = stored(FASTAPI, REDIS_TECH, SENTRY), stored(FASTAPI, REDIS_TECH, gaps=gaps)
    return {"fixture": "f", "code": "c", "before": before, "after": after, "fast_gaps": list(fast_gaps),
            "fast": {"registry": ["fastapi", "redis", "sentry"], "fork": ["fastapi", "redis"], "lost": ["sentry"]},
            "seconds": {"registry_full": 0.3, "fork_full": 1.5, "registry_fast": 0.2, "fork_fast": 1.4},
            "spawned": [GIT + "ls-files", f"{NODE_BIN} {CLI} /work/f", GIT + "ls-files"], "model": "recorded",
            "model_missing": 0}


def result_of(stored_record):
    return fork_stack.fixture_result(EXPECTED, stored_record, NODE_BIN, CLI, GIT)


def test_the_result_of_a_fixture_has_the_comparison_the_scores_the_seconds_and_the_gaps_of_the_fork():
    answer = result_of(stored_result(gaps=[NOT_SENT]))
    assert answer["compare"] == {**NONE_LOST, "lost": ["Sentry"], "gone": ["sentry"]}
    assert answer["fast"]["lost"] == ["sentry"] and answer["seconds"]["fork_fast"] == 1.4
    assert answer["executed_project_code"] == "no" and answer["spawned"] == sorted({GIT + "ls-files", f"{NODE_BIN} {CLI} /work/f"})
    assert answer["score"]["before"]["services"]["found"] == 2 and answer["score"]["after"]["services"]["found"] == 1
    assert answer["fork_gaps"] == {"full": {"kinds": {"declaration_not_sent": 1}, "failed": []},
                                   "fast": {"kinds": {}, "failed": []}}
    assert answer["fork_failed"] is False and (answer["model"], answer["model_missing"]) == ("recorded", 0)


def test_a_fork_run_that_failed_in_the_full_scan_is_flagged_with_its_cause():
    answer = result_of(stored_result(gaps=[FAILED_RUN]))
    assert answer["fork_failed"] is True and answer["fork_gaps"]["full"]["failed"] == [FAILED_RUN["detail"]]
    assert answer["fork_gaps"]["fast"]["failed"] == []
    assert answer["compare"]["lost"] == ["Sentry"]  # the comparison is as it is: the flag says it is not a loss


def test_a_fork_run_that_failed_in_the_fast_scan_only_is_flagged_too():
    answer = result_of(stored_result(fast_gaps=[FAILED_RUN]))
    assert answer["fork_failed"] is True and answer["fork_gaps"]["full"]["failed"] == []
    assert answer["fork_gaps"]["fast"] == {"kinds": {"checker_failed": 1}, "failed": [FAILED_RUN["detail"]]}


def test_a_gap_that_is_not_the_tool_s_run_does_not_flag_the_fixture():
    host = {"kind": "checker_failed", "checker": "host", "detail": "ValueError: no lines"}
    assert result_of(stored_result(gaps=[host, NOT_SENT], fast_gaps=[host]))["fork_failed"] is False


def test_evidence_the_snapshot_lacks_is_counted_among_the_fork_s_gaps_and_is_not_a_failed_run():
    outside = {"kind": "evidence_outside_snapshot", "count": 3, "paths": ["node_modules/a.js"]}
    answer = result_of(stored_result(gaps=[outside, NOT_SENT], fast_gaps=[outside]))
    assert answer["fork_gaps"] == {"full": {"kinds": {"declaration_not_sent": 1, "evidence_outside_snapshot": 1}, "failed": []},
                                   "fast": {"kinds": {"evidence_outside_snapshot": 1}, "failed": []}}
    assert answer["fork_failed"] is False


def test_a_stored_record_without_the_fast_gaps_is_not_read_as_a_run_that_did_not_fail():
    record = stored_result()
    del record["fast_gaps"]
    with pytest.raises(KeyError):
        result_of(record)


# ---------------------------------------------------------------------------------------------- the cold start

def test_the_tool_starts_once_on_an_empty_folder_before_any_timing(monkeypatch):
    seen = []

    def run(project, **kwargs):
        seen.append((Path(project), sorted(Path(project).iterdir()), kwargs))
        return component()

    monkeypatch.setattr(stack_analyser, "run", run)
    assert fork_stack.start() is None
    [(project, content, kwargs)] = seen
    assert content == [] and kwargs == {} and not project.exists()  # empty, with nothing sent, and gone afterwards


def test_a_tool_that_cannot_start_is_told_with_its_cause_and_remedy(monkeypatch):
    def broken(project, **kwargs):
        raise container.Gap("stack-analyser could not start: no such file", "check Node in Daodan's tool folder")

    monkeypatch.setattr(stack_analyser, "run", broken)
    assert fork_stack.start() == "stack-analyser could not start: no such file (check Node in Daodan's tool folder)"


# ---------------------------------------------------------------------------------------------- the driver's image

def constants(path, names):
    """The values of the module-level `names` of a file, read from its syntax tree: a literal, or a literal `%` a name."""
    out = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", None) in names:
            value = node.value
            out[node.targets[0].id] = (ast.literal_eval(value.left) % out[value.right.id]
                                       if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Mod)
                                       else ast.literal_eval(value))
    return out


def image_commands(path):
    """What each `run_commands` call of a file is given, as source text."""
    return {ast.unparse(argument) for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run_commands"
            for argument in node.args}


PINS = ("STACK_ANALYSER", "FETCH_STACK_ANALYSER")  # the launcher's, as they are
RUNTIME = ROOT / "daodan/core/indexers/runtime.py"


def test_the_driver_image_holds_the_release_of_the_test_launcher_and_of_daodan():
    """`tests/modal_pytest.py` cannot be imported here (it imports `modal`, and the launcher is not a module for the
    container): its pins and its commands are read from its syntax tree and must be the driver's."""
    driver, launcher = HERE / "modal_stack_fork.py", ROOT / "tests/modal_pytest.py"
    theirs, ours = constants(launcher, PINS), constants(driver, PINS)
    assert ours == theirs
    assert theirs["STACK_ANALYSER"][:2] == (stack_analyser.URL, stack_analyser.SHA256)
    assert constants(driver, ("CLI",))["CLI"] == f"{theirs['STACK_ANALYSER'][2]}/{stack_analyser.PROGRAM}"
    assert image_commands(driver) <= image_commands(launcher)  # the same unpacking commands, the same fetch commands
    assert {"FETCH_NODE", "FETCH_STACK_ANALYSER"} <= image_commands(driver)


def test_the_driver_measures_on_the_node_the_product_starts_fetched_as_the_launcher_fetches_one():
    """The seconds are the product's on the Node it starts (`indexers.runtime.NODE_VERSION`, not the test image's),
    fetched and checked by the launcher's own command with the driver's pin; the file of `runtime` is read, not imported."""
    driver, launcher = HERE / "modal_stack_fork.py", ROOT / "tests/modal_pytest.py"
    version = constants(RUNTIME, ("NODE_VERSION",))["NODE_VERSION"]
    ours, theirs = constants(driver, ("NODE_VERSION", "NODE", "FETCH_NODE", "NODE_BIN")), constants(launcher, ("NODE", "FETCH_NODE"))
    assert ours["NODE_VERSION"] == version
    assert ours["NODE"][0] == f"https://nodejs.org/dist/{version}/node-{version}-linux-x64.tar.gz"
    assert len(ours["NODE"][1]) == 64 and ours["NODE"] != theirs["NODE"]  # a pin of its own, a sha256
    assert ours["NODE_BIN"] == f"/opt/node-{version}-linux-x64/bin/node"  # where the tarball unpacks
    assert ours["FETCH_NODE"] == theirs["FETCH_NODE"].replace(theirs["NODE"][0], ours["NODE"][0]).replace(
        theirs["NODE"][1], ours["NODE"][1])  # the launcher's command with this pin


# ---------------------------------------------------------------------------------------------- the last round

ROUND, ACCEPTED = HERE / "results/daodan_stack_fork.json", HERE / "accepted-losses.json"
REGISTRY_DATA = ROOT / "daodan/data/service-registry.json"


def last_round() -> dict:
    return json.loads(ROUND.read_text(encoding="utf-8"))


def test_every_lost_name_of_the_last_round_is_accounted_for():
    """The spec's «Verifica», "nessuna perdita": each `(fixture, name)` in `lost` has exactly one line of
    `accepted-losses.json` and no line is left over (a round with no loss has an empty file); each line has the id the
    registry lost, a verdict, and a reason that names that id or a package or file the registry holds for it."""
    results, lines = last_round(), json.loads(ACCEPTED.read_text(encoding="utf-8"))
    fixtures = results["fixtures"]
    answered = {name: entry for name, entry in fixtures.items() if "error" not in entry}
    assert answered and all(isinstance(entry.get("compare", {}).get("lost"), list) for entry in answered.values())  # not a renamed key
    lost = sorted((name, lost) for name, entry in answered.items() for lost in entry["compare"]["lost"])
    assert results["totals"]["fixtures_with_lost"] == len({name for name, _ in lost})  # the file's own count agrees
    assert [(line["fixture"], line["name"]) for line in lines] == lost  # one each, none over, sorted
    entries = {entry["id"]: entry for entry in json.loads(REGISTRY_DATA.read_text(encoding="utf-8"))["entries"]}
    for line in lines:
        assert set(line) == {"fixture", "name", "id", "reason", "verdict"}, line
        assert line["verdict"] in ("accepted", "to_fix"), line
        assert line["id"] in fixtures[line["fixture"]]["compare"]["gone"], line  # what the registry lost
        signs = entries[line["id"]].get("signs") or {}
        named = {line["id"], *(value for values in (signs.get("packages") or {}).values() for value in values),
                 *(signs.get("files") or ())}
        assert len(line["reason"]) > 40 and any(value in line["reason"] for value in named), line


def test_no_fixture_of_the_last_round_executed_project_code():
    answered = {name: entry for name, entry in last_round()["fixtures"].items() if "error" not in entry}
    assert answered and [name for name, entry in answered.items() if entry["executed_project_code"] != "no"] == []


