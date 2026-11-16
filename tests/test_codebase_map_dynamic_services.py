"""The services a project's CI starts beside its tests: read into the pre-map, planned by the dynamic step, started
by the container in the network namespace the tests run in.

    python tests/modal_pytest.py tests/test_codebase_map_dynamic_services.py -q

The engine is the fake Docker-compatible command line of the container's tests (`FAKE_CLI`), with the verbs a
service needs before it (`SERVICES`); the observers are fakes. The last test runs only on Modal (`MODAL_TASK_ID`):
a PostgreSQL service declared as chrisvel/tududi's CI declares it starts beside a network-blocked execution of the
benchmark driver (`benchmarks/project-model/modal_pipeline.py`) and answers the tests at localhost.
"""
from __future__ import annotations

import contextlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import dynamic  # noqa: E402
import premap  # noqa: E402
import snapshot  # noqa: E402
from premap import renovate  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402
from test_codebase_map_container import FAKE_CLI  # noqa: E402
from test_codebase_map_dynamic import SAMPLED_LIB, gaps, static_store, step, write_project  # noqa: E402

# chrisvel/tududi at 71da9d7b34dfd1600657e9c5ddf40420206fd263, .github/workflows/ci.yml as Renovate's YAML library
# prints it: the job that runs the backend's tests and the PostgreSQL its tests reach at localhost
CI = {"name": "CI", "on": {"pull_request": {"branches": ["main"]}, "push": {"branches": ["main"]}},
      "permissions": {"contents": "read"},
      "jobs": {"test": {
          "runs-on": "ubuntu-latest",
          "services": {"postgres": {
              "image": "postgres:16-alpine",
              "env": {"POSTGRES_USER": "tududi", "POSTGRES_PASSWORD": "tududi", "POSTGRES_DB": "tududi_test"},
              "ports": ["5432:5432"],
              "options": '--health-cmd "pg_isready -U tududi" --health-interval 5s --health-timeout 5s '
                         "--health-retries 10"}},
          "env": {"DATABASE_URL": "postgres://tududi:tududi@localhost:5432/tududi_test"},
          "steps": [{"name": "Checkout code", "uses": "actions/checkout@v5"},
                    {"name": "Install dependencies", "run": "npm install"},
                    {"name": "Run backend tests", "run": "npm run backend:test"}]}}}
TUDUDI = {"name": "postgres", "image": "postgres:16-alpine", "declared_in": ".github/workflows/ci.yml#jobs.test.services.postgres",
          "host": "localhost",
          "env": {"POSTGRES_USER": "tududi", "POSTGRES_PASSWORD": "tududi", "POSTGRES_DB": "tududi_test"},
          "ports": ["5432:5432"],
          "options": '--health-cmd "pg_isready -U tududi" --health-interval 5s --health-timeout 5s --health-retries 10',
          "job_env": {"DATABASE_URL": "postgres://tududi:tududi@localhost:5432/tududi_test"}}
SPEC = {"name": "postgres", "image": "postgres:16-alpine", "host": "localhost",
        "env": {"POSTGRES_USER": "tududi", "POSTGRES_PASSWORD": "tududi", "POSTGRES_DB": "tududi_test"},
        "args": ["--health-cmd", "pg_isready -U tududi", "--health-interval", "5s", "--health-timeout", "5s",
                 "--health-retries", "10"], "command": []}
DATABASE_URL = "postgres://tududi:tududi@localhost:5432/tududi_test"


# ------------------------------------------------------------------ the pre-map

@contextlib.contextmanager
def context_of(tmp_path, files: dict):
    project = tmp_path / "proj"
    for rel, text in files.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    with open_snapshot(manifest) as store:
        yield premap.Context(manifest, store)


WORKFLOW = "jobs:\n  test:\n    services:\n      postgres:\n        image: postgres:16-alpine\n"


def test_renovate_reads_the_workflows_with_its_own_yaml_library_where_one_names_services(tmp_path):
    """The workflows sit in a dot folder, outside the snapshot and inside the container's copy (Git tracks them):
    the command reads each one there; a project whose workflows name no service runs Renovate's extraction alone."""
    with context_of(tmp_path / "a", {"package.json": "{}\n", ".github/workflows/ci.yml": WORKFLOW}) as context:
        extract, workflows = renovate.commands(context)
    assert extract["argv"][0] == "renovate" and workflows["network"] == "none" and workflows["cwd"] == "."
    assert workflows["tool"] == "renovate" and renovate.YAML in workflows["argv"][-1]
    assert "command -v renovate" in renovate.YAML and renovate.YAML.endswith('/node_modules/yaml/bin.mjs"')
    for case, files in {"b": {"package.json": "{}\n"},
                        "c": {"package.json": "{}\n", ".github/workflows/ci.yml": "on: push\n"}}.items():
        with context_of(tmp_path / case, files) as context:
            assert [command["argv"][0] for command in renovate.commands(context)] == ["renovate"]


def read_services(tmp_path, documents: str, stderr: str = "") -> dict:
    with context_of(tmp_path, {"package.json": "{}\n", ".github/workflows/ci.yml": WORKFLOW}) as context:
        commands = renovate.commands(context)
        report = {"repositories": {"local": {"packageFiles": {}}}}
        return renovate.read(context, commands, [{"returncode": 0, "stdout": json.dumps(report), "stderr": ""},
                                                  {"returncode": 0, "stdout": documents, "stderr": stderr}])


def test_each_service_a_workflow_job_declares_is_a_fact_as_its_file_writes_it(tmp_path):
    """tududi's job runs on the runner: its service answers at localhost on the ports it maps, and the variables
    the job gives its steps go with it. A job in a container reaches its services by their names; a service
    written as its image alone has that image; one whose image is empty does not start (GitHub's rule)."""
    other = {"env": {"LEVEL": "debug", "PORT": 1}, "jobs": {
        "unit": {"container": "node:22", "env": {"PORT": 2}, "services": {
            "redis": "redis:7", "off": {"image": ""},
            "db": {"image": "mysql:8", "command": "--sql-mode=", "entrypoint": "docker-entrypoint.sh",
                   "volumes": ["/data:/var/lib/mysql"]}}},
        "lint": {"steps": [{"run": "npm run lint"}]}}}
    out = read_services(tmp_path, f".github/workflows/ci.yml\n{json.dumps(CI)}\n"
                                  f".github/workflows/unit.yaml\n{json.dumps(other)}\n")
    assert out["facts"]["services"] == [TUDUDI, {
        "name": "redis", "image": "redis:7", "declared_in": ".github/workflows/unit.yaml#jobs.unit.services.redis",
        "host": "redis", "job_env": {"LEVEL": "debug", "PORT": 2}}, {
        "name": "db", "image": "mysql:8", "declared_in": ".github/workflows/unit.yaml#jobs.unit.services.db",
        "host": "db", "command": "--sql-mode=", "entrypoint": "docker-entrypoint.sh",
        "volumes": ["/data:/var/lib/mysql"], "job_env": {"LEVEL": "debug", "PORT": 2}}]
    assert not out.get("gaps")


def test_a_workflow_the_yaml_library_cannot_read_is_a_gap_with_its_message(tmp_path):
    said = ("file:///usr/local/lib/node_modules/renovate/node_modules/yaml/bin.mjs:10", "  } else if (error) throw error",
            "YAMLParseError: Nested mappings are not allowed in compact mappings at line 3, column 9:", "",
            "    at Composer.onError (/usr/local/lib/node_modules/renovate/node_modules/yaml/dist/compose/composer.js:70)",
            "Node.js v24.22.3")  # as the library prints it, each line after the file's name (`EACH`)
    out = read_services(tmp_path, ".github/workflows/ci.yml\nnull\n",
                        "".join(f".github/workflows/ci.yml: {line}\n" for line in said))
    assert "services" not in out["facts"]
    [gap] = out["gaps"]
    assert gap["kind"] == "model_failed" and gap["path"] == ".github/workflows/ci.yml"
    assert gap["detail"].endswith(": YAMLParseError: Nested mappings are not allowed in compact mappings at line 3, "
                                  "column 9:")


def test_a_service_is_one_fact_per_declaration():
    part = {"source": "renovate", "rank": "reader", "facts": {"services": [TUDUDI, {**TUDUDI, "image": "postgres:17"}]}}
    assert premap.join([part])["services"] == [{**TUDUDI, "sources": ["renovate"]}, {
        **TUDUDI, "image": "postgres:17", "sources": ["renovate"]}]


# ------------------------------------------------------------------ the plan

def test_the_plan_starts_what_the_ci_declares_and_gives_the_tests_the_job_s_variables():
    planned = dynamic.services({"services": [{**TUDUDI, "sources": ["renovate@44.239.1"]}]})
    assert planned == {"services": [SPEC], "env": {"DATABASE_URL": DATABASE_URL}, "gaps": []}
    assert dynamic.services({}) == {"services": [], "env": {}, "gaps": []}


def test_what_cannot_run_as_declared_is_a_gap_naming_the_service_and_its_image():
    path = ".github/workflows/ci.yml#jobs.{}.services.{}"
    entries = [
        {"name": "matrix", "image": "postgres:${{ matrix.pg }}", "declared_in": path.format("a", "matrix"),
         "host": "localhost"},
        {"name": "db", "image": "mysql:8", "declared_in": path.format("a", "db"), "host": "db",
         "env": {"MYSQL_ROOT_PASSWORD": "${{ secrets.ROOT }}", "MYSQL_DATABASE": "app", "MYSQL_PORT": 3306},
         "ports": ["3307:3306/tcp", "8080"], "volumes": ["/data:/var/lib/mysql"], "entrypoint": "mysqld-start",
         "command": "--sql-mode= --skip-log-bin",
         "options": "--health-cmd='mysqladmin ping' --tmpfs /var/lib/mysql -e A=1 --no-healthcheck",
         "job_env": {"DB_PORT": "${{ job.services.db.ports['3306'] }}", "TOKEN": "${{ secrets.TOKEN }}",
                     "SHARED": "one", "FLAG": True}},
        {"name": "db", "image": "mysql:9", "declared_in": path.format("b", "db"), "host": "localhost",
         "job_env": {"SHARED": "two", "OTHER": "${{ job.services.db.ports[3306] }}"}}]
    planned = dynamic.services({"services": entries})
    assert planned["services"] == [{
        "name": "db", "image": "mysql:8", "host": "db", "env": {"MYSQL_DATABASE": "app", "MYSQL_PORT": "3306"},
        "args": ["--health-cmd", "mysqladmin ping", "--no-healthcheck", "--entrypoint", "mysqld-start"],
        "command": ["--sql-mode=", "--skip-log-bin"]}]
    assert planned["env"] == {"DB_PORT": "3306", "FLAG": "true", "OTHER": "3306"}
    said = {(gap["kind"], gap["name"], gap["image"], gap["path"]): gap["detail"] for gap in planned["gaps"]}
    assert "the CI computes its image" in said[("service_unavailable", "matrix", "postgres:${{ matrix.pg }}",
                                                path.format("a", "matrix"))]
    incomplete = said[("service_incomplete", "db", "mysql:8", path.format("a", "db"))]
    for part in ("MYSQL_ROOT_PASSWORD", "3307 to its port 3306", "/data:/var/lib/mysql", "--tmpfs /var/lib/mysql -e A=1",
                 "TOKEN"):
        assert part in incomplete
    assert "MYSQL_DATABASE" not in incomplete
    again = said[("service_unavailable", "db", "mysql:9", path.format("b", "db"))]
    assert path.format("a", "db") in again  # the first declaration of the name starts
    [shared] = [gap["detail"] for gap in planned["gaps"] if "SHARED" in gap["detail"]]
    assert "one" in shared and "two" in shared


# ------------------------------------------------------------------ the container

# Before the container's fake: the service verbs. `registry.json` maps a reference to its RepoDigests (absent: the
# pull fails); `states.json` maps an image to the states `inspect` answers in turn, the last one repeated.
SERVICES = r'''
import json as _json, sys as _sys
from pathlib import Path as _Path
_state, _args = _Path(_sys.argv[1]), _sys.argv[2:]


def _log():
    with (_state / "calls.jsonl").open("a", encoding="utf-8") as _f:
        _f.write(_json.dumps(_args) + "\n")


def _read(_name, _default):
    _path = _state / _name
    return _json.loads(_path.read_text()) if _path.is_file() else _default


_box = _args[_args.index("--name") + 1] if "--name" in _args else (_args[-1] if _args else "")
_mine = _box.startswith(("daodan-pod-", "daodan-svc-"))
if _args[:1] == ["pull"]:
    _log()
    if _args[1] not in _read("registry.json", {}):
        _sys.exit("Error response from daemon: pull access denied for " + _args[1])
    _sys.exit(0)
if _args[:2] == ["image", "inspect"]:
    _log()
    print(_json.dumps(_read("registry.json", {})[_args[-1]]))
    _sys.exit(0)
if _args[:1] == ["create"] and _mine:
    _log()
    (_state / "containers" / _box).mkdir(parents=True)
    (_state / "containers" / _box / "image").write_text(next(_a for _a in _args if "@sha256:" in _a))
    print(_box)
    _sys.exit(0)
if _args[:1] == ["start"] and _mine:
    _log()
    _sys.exit(0)
if _args[:1] == ["inspect"] and _mine:
    _log()
    _image = (_state / "containers" / _box / "image").read_text()
    _turns = _state / "containers" / _box / "turns"
    _turn = int(_turns.read_text()) if _turns.is_file() else 0
    _turns.write_text(str(_turn + 1))
    _seq = _read("states.json", {}).get(_image, ["running "])
    print(_seq[min(_turn, len(_seq) - 1)])
    _sys.exit(0)
if _args[:1] == ["logs"] and _mine:
    _log()
    print(_read("logs.json", {}).get((_state / "containers" / _box / "image").read_text(), ""))
    _sys.exit(0)
if _args[:2] == ["healthcheck", "run"] and _mine:
    _log()
    _sys.exit(0)
'''
PINNED = "postgres@sha256:" + "a" * 64


class PodTest(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="daodan-services-test-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.state = self.scratch / "state"
        (self.state / "containers").mkdir(parents=True)
        (self.state / "images").mkdir()
        fake = self.scratch / "fake_docker.py"
        fake.write_text(SERVICES + FAKE_CLI, encoding="utf-8")
        self.engine = container.Engine("fake", (sys.executable, str(fake), str(self.state)))
        self.project = self.scratch / "project"
        (self.project / "src").mkdir(parents=True)
        (self.project / "src" / "app.js").write_text("module.exports = 1;\n", encoding="utf-8")
        self.out = self.scratch / "out"
        self.registry({"docker.io/library/postgres:16-alpine": [PINNED]})
        for patcher in (mock.patch.object(container, "volume_registry", return_value=self.scratch / "volumes"),
                        mock.patch.object(container, "free_memory", return_value=64 * 2**30),
                        mock.patch.object(container.time, "sleep")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def registry(self, served: dict) -> None:
        (self.state / "registry.json").write_text(json.dumps(served), encoding="utf-8")

    def states(self, image: str, *turns: str, logs: str = "") -> None:
        (self.state / "states.json").write_text(json.dumps({image: list(turns)}), encoding="utf-8")
        (self.state / "logs.json").write_text(json.dumps({image: logs}), encoding="utf-8")

    def calls(self) -> list[list[str]]:
        path = self.state / "calls.jsonl"
        return [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()]

    def created(self, prefix: str) -> list[list[str]]:
        return [call for call in self.calls() if call[0] == "create" and call[call.index("--name") + 1].startswith(prefix)]

    def run_operation(self, services, given: dict | None = None, **options) -> dict:
        with container.beside(services, given or {}) as self.started:
            return container.run_in_container(self.project, ["exit", "0"], image="fake/runtime:1", out_dir=self.out,
                                              engine=self.engine, **options)

    def rows(self) -> list[dict]:
        lines = (self.out / container.RECORD_NAME).read_text(encoding="utf-8").splitlines()
        return [row for row in map(json.loads, lines) if row["phase"] == "service"]

    def test_each_service_runs_in_the_pod_s_network_by_its_pinned_image_and_the_tests_join_it(self):
        """The shape of a Kubernetes pod: one network namespace with no way out, the service listening in it as on
        GitHub's runner, the execution at its localhost. The image is pulled before the preparation, with the
        engine's network, and runs by the digest the registry gave."""
        self.states(PINNED, "running starting", "running starting", "running healthy")
        result = self.run_operation([SPEC], prepare=["exit", "0"])
        self.assertEqual(result["state"], "done", result)
        calls = self.calls()
        pulled = calls.index(["pull", "docker.io/library/postgres:16-alpine"])
        [prepare] = [c for c in self.created("daodan-") if "--network" in c
                     and c[c.index("--network") + 1].startswith("daodan-net-")]
        self.assertLess(pulled, calls.index(prepare))
        [pod] = self.created("daodan-pod-")
        name = pod[pod.index("--name") + 1]
        self.assertEqual(pod[pod.index("--network") + 1], "none")
        self.assertIn(container.PROXY_IMAGE, pod)
        [service] = self.created("daodan-svc-")
        self.assertEqual(service[service.index("--network") + 1], f"container:{name}")
        self.assertEqual(service[-1], PINNED)  # no command: the image's own
        for item in ("POSTGRES_USER=tududi", "POSTGRES_PASSWORD=tududi", "POSTGRES_DB=tududi_test",
                     "pg_isready -U tududi", "--health-retries"):
            self.assertIn(item, service)
        self.assertNotIn("--add-host", " ".join(pod))  # localhost: the job ran on the runner
        execute = [c for c in self.created("daodan-") if c[-2:] == ["exit", "0"]][-1]
        self.assertEqual(execute[execute.index("--network") + 1], f"container:{name}")
        box = service[service.index("--name") + 1]
        self.assertEqual(len([c for c in calls if c[:1] == ["inspect"] and c[-1] == box]), 3)  # healthy at the third
        self.assertLess(calls.index(execute), calls.index(["rm", "-f", box]))
        self.assertLess(calls.index(["rm", "-f", box]), calls.index(["rm", "-f", name]))
        [row] = self.rows()
        self.assertEqual((row["name"], row["image"], row["pinned"], row["outcome"]),
                         ("postgres", "postgres:16-alpine", PINNED, "ready"))
        self.assertEqual(result["services"], [{"name": "postgres", "image": "postgres:16-alpine", "pinned": PINNED,
                                               "outcome": "ready"}])
        self.assertEqual(self.started, result["services"])  # what the step reads, whichever folder the record is in

    def test_the_job_s_variables_reach_both_phases_under_the_caller_s_own(self):
        self.states(PINNED, "running healthy")
        self.run_operation([SPEC], {"DATABASE_URL": DATABASE_URL, "PATH": "/nowhere"}, prepare=["exit", "0"],
                           env={"PATH": "/daodan/bin"})
        phases = [c for c in self.created("daodan-") if c[-2:] == ["exit", "0"]]
        self.assertEqual(len(phases), 2)
        for call in phases:
            self.assertIn(f"DATABASE_URL={DATABASE_URL}", call)
            self.assertIn("PATH=/daodan/bin", call)  # Daodan's tools stay first: a job's PATH is the runner's
            self.assertNotIn("PATH=/nowhere", call)
        self.assertIsNone(container.BESIDE.get())  # outside the step's context, nothing beside a run

    def test_on_podman_each_health_check_runs_from_here_at_its_interval_with_the_engine_s_timer_off(self):
        """Podman runs health checks on systemd's timers, and without systemd it runs none (its build without
        systemd: libpod/healthcheck_nosystemd_linux.go, `createTimer` returns nil): Daodan runs each one
        (`healthcheck run`) at the interval the CI declares, Podman's timer off, its retries counted by Podman."""
        self.engine = self.engine._replace(name="podman")
        self.states(PINNED, "running starting", "running healthy")
        self.run_operation([SPEC])
        [service] = self.created("daodan-svc-")
        self.assertEqual(service[service.index("--health-interval") + 1], "disable")
        box = service[service.index("--name") + 1]
        said = [c[0] for c in self.calls() if c[-1] == box and c[0] in ("healthcheck", "inspect")]
        self.assertEqual(said, ["healthcheck", "inspect", "inspect"])  # the next one 5 s later, as declared
        self.engine = self.engine._replace(name="docker")  # an engine that runs them itself: none from here
        shutil.rmtree(self.out)
        (self.state / "calls.jsonl").unlink()
        self.run_operation([SPEC])
        [service] = self.created("daodan-svc-")
        self.assertEqual(service[service.index("--health-interval") + 1], "5s")
        self.assertEqual([c for c in self.calls() if c[0] == "healthcheck"], [])

    def test_a_service_reached_by_name_has_its_name_in_the_pod_s_hosts(self):
        self.run_operation([{**SPEC, "host": "postgres", "args": []}])
        [pod] = self.created("daodan-pod-")
        self.assertIn("--add-host=postgres:127.0.0.1", pod)

    def test_a_service_that_cannot_start_is_recorded_with_its_cause_and_the_tests_run_without_it(self):
        cases = {"pull": ({}, (), "pull access denied"),
                 "unhealthy": ({"docker.io/library/postgres:16-alpine": [PINNED]},
                               ("running starting", "running unhealthy"), "its health check failed"),
                 "exited": ({"docker.io/library/postgres:16-alpine": [PINNED]}, ("exited ",), "it exited"),
                 "starting": ({"docker.io/library/postgres:16-alpine": [PINNED]}, ("running starting",), "starting")}
        for case, (served, turns, cause) in cases.items():
            with self.subTest(case=case), mock.patch.object(container, "SERVICE_WAIT", 0 if case == "starting" else 600):
                shutil.rmtree(self.out, ignore_errors=True)
                self.registry(served)
                self.states(PINNED, *turns, logs="FATAL:  role \"tududi\" does not exist")
                result = self.run_operation([SPEC])
                self.assertEqual(result["state"], "done", result)
                [row] = self.rows()
                self.assertEqual(row["outcome"], "failed")
                self.assertIn(cause, row["cause"])
                if case in ("unhealthy", "exited"):
                    self.assertIn('role "tududi" does not exist', row["cause"])
                [service] = result["services"]
                self.assertEqual((service["name"], service["outcome"]), ("postgres", "failed"))

    def test_without_services_nothing_of_a_pod(self):
        self.run_operation(())
        self.assertEqual(self.created("daodan-pod-") + self.created("daodan-svc-"), [])
        self.assertEqual([c for c in self.calls() if c[0] == "pull"], [])
        execute = self.created("daodan-")[-1]
        self.assertEqual(execute[execute.index("--network") + 1], "none")

    def test_an_image_name_gets_the_registry_docker_reads_into_it(self):
        self.assertEqual([container.qualified(name) for name in (
            "postgres:16", "bitnami/redis:7", "ghcr.io/acme/db:1", "localhost:5000/db", "registry:5000/a/b",
            "postgres@sha256:" + "b" * 64)], [
            "docker.io/library/postgres:16", "docker.io/bitnami/redis:7", "ghcr.io/acme/db:1", "localhost:5000/db",
            "registry:5000/a/b", "docker.io/library/postgres@sha256:" + "b" * 64])


# ------------------------------------------------------------------ the step

def observer_of(seen: dict, runs: list[list[dict]], state: str = "ran"):
    """A Python observer with a container run per item of `runs`, each starting the services with those outcomes
    (as `container.run_in_container` does within `container.beside`), that keeps what it was planned."""
    def observe(project, planned, out_dir, engine):
        services, env, started = container.BESIDE.get()
        seen.update(planned, services=services, env=env)
        for outcomes in runs:
            started += outcomes
        return {"state": state, "sites": [], "gaps": [], "runs": [{"root": ".", "runner": "pytest", "state": "ran"}]} \
            if state == "ran" else {"state": state, "cause": "no engine", "remedy": "start one"}
    return SimpleNamespace(ENTRY="dynamic-fake-python", VERSION="1", LANGUAGES=("python",),
                           external=lambda callee: {"manager": "python", "package": "x", "version": None},
                           plan=lambda record, files, read: {"runs": [{"root": ".", "runner": "pytest"}], "gaps": []},
                           observe=observe)


def run_step(tmp_path, entries: list[dict], runs: list[list[dict]], state: str = "ran"):
    _project, manifest = write_project(tmp_path, {"lib.py": SAMPLED_LIB})
    static_store(manifest)
    seen: dict = {}
    with mock.patch.object(premap, "ensure", return_value={"services": entries, "tests": []}), \
            mock.patch.object(dynamic, "observers", return_value=[observer_of(seen, runs, state)]):
        _result, events, _asked = step(manifest)
    return seen, events


def test_the_step_starts_the_services_beside_every_container_run_and_says_which_did_not_start(tmp_path):
    broken = {**TUDUDI, "name": "cache", "image": "redis:7", "declared_in": "ci.yml#jobs.test.services.cache",
              "ports": ["6380:6379"], "options": "", "env": {}}
    run = [{"name": "postgres", "image": "postgres:16-alpine", "outcome": "ready"},
           {"name": "cache", "image": "redis:7", "outcome": "failed",
            "cause": "pull of docker.io/library/redis:7 failed with code 1: pull access denied"}]
    seen, events = run_step(tmp_path, [TUDUDI, broken], [run, run])  # two builds, as the JVM observer's
    assert seen["services"] == [SPEC, {"name": "cache", "image": "redis:7", "host": "localhost", "env": {},
                                       "args": [], "command": []}]
    assert seen["env"] == {"DATABASE_URL": DATABASE_URL}
    assert container.BESIDE.get() is None  # only the observers' runs start them
    [failed] = gaps(events, "service_unavailable")
    assert (failed["name"], failed["image"], failed["path"]) == ("cache", "redis:7", "ci.yml#jobs.test.services.cache")
    assert "pull access denied" in failed["detail"]
    [partial] = gaps(events, "service_incomplete")
    assert partial["name"] == "cache" and "6380 to its port 6379" in partial["detail"]


def test_an_observer_that_starts_no_service_is_said_and_one_without_a_container_is_not(tmp_path):
    seen, events = run_step(tmp_path / "a", [TUDUDI], [])
    [gap] = gaps(events, "service_unavailable")
    assert gap["name"] == "postgres" and "starts no service" in gap["detail"] and "dynamic-fake-python" in gap["detail"]
    seen, events = run_step(tmp_path / "b", [TUDUDI], [], state="gap")
    assert gaps(events, "service_unavailable") == []


# ------------------------------------------------------------------ the JavaScript observer

def test_the_javascript_observer_says_a_refused_connection_without_saying_no_service_starts(tmp_path):
    from test_codebase_map_dynamic_javascript import Played, observe
    played = Played({"tests-0.log": "Error: connect ECONNREFUSED 127.0.0.1:6379\n"},
                    {"execute.log": "DAODAN-DYNAMIC 0 exit 1 3\n"})
    result = observe(tmp_path, played)
    [gap] = [gap for gap in result["gaps"] if gap["kind"] == "services_unreachable"]
    assert "starts no service" not in gap["detail"]
    assert "only the services the project's CI declares" in gap["detail"]


# ------------------------------------------------------------------ on Modal

PROBE = r'''import json, os, socket, struct, urllib.parse
url = urllib.parse.urlsplit(os.environ["DATABASE_URL"])
said = {"host": url.hostname, "port": url.port}
with socket.create_connection((url.hostname, url.port), timeout=10) as s:
    s.sendall(struct.pack("!ii", 8, 80877103))
    said["ssl"] = s.recv(1).decode()
    body = b"user\0" + url.username.encode() + b"\0database\0" + url.path[1:].encode() + b"\0\0"
    s.sendall(struct.pack("!ii", 8 + len(body), 196608) + body)
    kind, size, code = struct.unpack("!cii", s.recv(9))
    said["reply"], said["auth"] = kind.decode(), code
    while code == 0 and said.get("session") is None:  # trusted: the session opens on the job's database, or not
        kind, size = struct.unpack("!ci", s.recv(5))
        data = b""
        while len(data) < size - 4:
            data += s.recv(size - 4 - len(data))
        said["session"] = {b"Z": "ready", b"E": data.decode(errors="replace")}.get(kind)
try:
    socket.create_connection(("1.1.1.1", 443), timeout=5)
    said["outside"] = "reached"
except OSError as error:
    said["outside"] = type(error).__name__
os.makedirs("/daodan/out", exist_ok=True)
with open("/daodan/out/probe.json", "w") as f:
    json.dump(said, f)
'''


@contextlib.contextmanager
def the_driver():
    """The benchmark driver, its volume's `commit` sending what a test wrote under /results (the driver's
    function holds the volume there, a test does not); this run's scratch folder removed afterwards, never another
    run's: Docker's binaries stay, as the driver keeps them."""
    sys.path.insert(0, str(HERE.parent / "benchmarks/project-model"))
    import modal_pipeline
    volume, sent = modal_pipeline.volume, set()

    def commit():
        root = Path("/results")
        with volume.batch_upload(force=True) as batch:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    sent.add("/" + path.relative_to(root).as_posix())
                    batch.put_file(str(path), "/" + path.relative_to(root).as_posix())

    try:
        with mock.patch.object(volume, "commit", commit):
            yield modal_pipeline
    finally:
        scratch = f"/{modal_pipeline.SCRATCH}/"
        for folder in sorted({scratch + path[len(scratch):].split("/")[0] for path in sent if path.startswith(scratch)}):
            volume.remove_file(folder, recursive=True)


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_on_modal_the_postgres_tududi_s_ci_declares_answers_the_tests_at_localhost(tmp_path):
    """The driver's Sandboxes as the pipeline runs them: the preparation pulls and pins the image, the execution,
    network blocked, starts it in its own namespace and awaits its health check, then the tests (a probe that
    speaks PostgreSQL's protocol to DATABASE_URL, as the job gives it) reach it at localhost and nothing outside."""
    from indexers import typescript
    planned = dynamic.services({"services": [TUDUDI]})
    assert planned["gaps"] == []
    project = tmp_path / "proj"
    project.mkdir()
    (project / "probe.py").write_text(PROBE, encoding="utf-8")
    with the_driver() as modal_pipeline, container.beside(planned["services"], planned["env"]):
        result = modal_pipeline.sandbox_run(project, ["python3", "/work/probe.py"], image=typescript.IMAGE,
                                            out_dir=tmp_path / "out", prepare=["true"], outputs=["/daodan/out"],
                                            env={"PATH": "/usr/local/bin:/usr/bin:/bin"}, timeout=600,
                                            prepare_timeout=900)
    rows = [json.loads(line) for line in (tmp_path / "out" / container.RECORD_NAME).read_text().splitlines()]
    print(json.dumps(rows, indent=1), flush=True)
    assert result["state"] == "done" and result["exit_code"] == 0, result
    [service] = [row for row in rows if row["phase"] == "service"]
    assert service["outcome"] == "ready" and "postgres@sha256:" in service["pinned"], service
    said = json.loads((tmp_path / "out" / "out" / "probe.json").read_text())
    print(said, flush=True)
    assert (said["host"], said["port"], said["ssl"], said["reply"]) == ("localhost", 5432, "N", "R")
    assert said["auth"] in (0, 3, 5, 10) and said.get("session", "ready") == "ready"  # trusted, or a password asked
    assert said["outside"] != "reached"


POD = r'''import json, sys
from pathlib import Path
sys.path.insert(0, "/daodan/scripts")
import container
spec, url, engine = json.loads(sys.argv[1]), sys.argv[2], container.Engine("docker", (sys.argv[3] + "/docker",))
said = {}
for host in ("localhost", "postgres"):  # on the runner, and from a job's container, by the service's name
    out = Path(f"/tmp/out-{host}")
    with container.beside([{**spec, "host": host}], {"DATABASE_URL": url.replace("@localhost:", f"@{host}:")}):
        result = container.run_in_container(Path("/tmp/project"), ["python3", "/work/probe.py"], engine=engine,
                                            image=container.PROXY_IMAGE, out_dir=out, outputs=["/daodan/out"],
                                            env={"PATH": "/usr/local/bin:/usr/bin:/bin"}, timeout=300)
    probe = out / "out" / "probe.json"
    said[host] = {"result": result, "probe": json.loads(probe.read_text()) if probe.is_file() else None,
                  "rows": [json.loads(line) for line in (out / container.RECORD_NAME).read_text().splitlines()]}
said["left"] = container.cli(engine, "ps", "-a", "--format", "{{.Names}}").stdout.decode().split()
print(json.dumps(said))
'''


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_on_a_real_docker_the_pod_gives_the_tests_the_service_at_localhost_and_by_name_and_nothing_outside():
    """`container.run_in_container` itself on a real engine: Docker (`modal_pipeline.DOCKER`) in a Modal VM
    Sandbox as the driver starts it. The service of tududi's CI starts in the pod (`--network container:<pod>`) and
    is awaited; the tests, in the pod too, reach it at localhost and, as a job in a container does, by its name
    (the pod's hosts); the pod has no network; no container stays."""
    import base64

    import modal
    image = (modal.Image.debian_slim(python_version="3.13").apt_install("git")
             .add_local_dir(SCRIPTS, "/daodan/scripts", ignore=["**/__pycache__"]))
    with the_driver() as modal_pipeline:
        bundle = modal_pipeline._bundle()
        box = modal.Sandbox.create(image=image, app=modal.App.lookup("daodan-pipeline-sandboxes",
                                                                       create_if_missing=True),
                                   volumes={"/results": modal_pipeline.volume},
                                   experimental_options=modal_pipeline.VM, timeout=1200, cpu=2, memory=6144)
        try:
            modal_pipeline._daemon(box, bundle)
            for path, text in (("/tmp/project/probe.py", PROBE), ("/tmp/pod.py", POD)):
                assert box.exec("sh", "-c", f"mkdir -p {Path(path).parent.as_posix()} && echo "
                                f"{base64.b64encode(text.encode()).decode()} | base64 -d > {path}").wait() == 0
            process = box.exec("python3", "/tmp/pod.py", json.dumps(SPEC), DATABASE_URL, modal_pipeline.ENGINE,
                               timeout=900)
            out, err = process.stdout.read(), process.stderr.read()
            assert process.wait() == 0, err[-3000:]
        finally:
            box.terminate()
    said = json.loads(out)
    print(json.dumps(said, indent=1), flush=True)
    for host in ("localhost", "postgres"):
        result, probe, rows = said[host]["result"], said[host]["probe"], said[host]["rows"]
        assert result["state"] == "done" and result["exit_code"] == 0, result
        assert [s["outcome"] for s in result["services"]] == ["ready"], result
        [service, execute] = rows
        assert service["pinned"].startswith("postgres@sha256:") and service["network"].startswith("container:daodan-pod-")
        assert execute["phase"] == "execute" and execute["network"] == service["network"]
        assert (probe["host"], probe["port"], probe["session"]) == (host, 5432, "ready")
        assert probe["outside"] != "reached"
    assert said["left"] == []
