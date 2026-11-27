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
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import dynamic  # noqa: E402
import premap  # noqa: E402
import snapshot  # noqa: E402
import container_runner  # noqa: E402
from premap import compose, renovate  # noqa: E402
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
                    {"name": "Setup Node.js", "uses": "actions/setup-node@v5",
                     "with": {"node-version": "22", "cache": "npm"}},
                    {"name": "Install dependencies", "run": "npm install"},
                    {"name": "Run linting", "run": "npm run lint"},
                    {"name": "Bootstrap an empty database and run pending migrations", "working-directory": "backend",
                     "run": "node scripts/db-prepare.js\nnpx sequelize-cli db:migrate --config config/database.js\n"
                            "node scripts/db-prepare.js\n", "env": {"NODE_ENV": "production"}},
                    {"name": "Run backend tests", "run": "npm run backend:test"},
                    {"name": "Build frontend", "run": "npm run build"}]}}}
# its package.json's scripts that the CI's steps name
TUDUDI_SCRIPTS = {"test": "npm run backend:test", "backend:test": "cd backend && cross-env NODE_ENV=test jest --maxWorkers=4",
                  "frontend:test": "jest", "lint": "npm run frontend:lint && npm run backend:lint",
                  "frontend:lint": "eslint 'frontend/**/*.{js,jsx,ts,tsx}'", "backend:lint": "cd backend && eslint .",
                  "build": "webpack --mode production"}
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
    snapshot.read_project(project, manifest)
    with open_snapshot(manifest) as store:
        yield premap.Context(manifest, store)


WORKFLOW = "jobs:\n  test:\n    services:\n      postgres:\n        image: postgres:16-alpine\n"


def test_renovate_reads_declared_workflow_files_with_its_existing_yaml_library(tmp_path):
    """The workflow path selects the container's YAML reader even for reusable workflows without shell steps."""
    with context_of(tmp_path / "a", {"package.json": "{}\n", ".github/workflows/ci.yml": WORKFLOW}) as context:
        extract, workflows = renovate.commands(context)
    assert extract["argv"][0] == "renovate" and workflows["network"] == "none" and workflows["cwd"] == "."
    assert workflows["tool"] == "renovate" and renovate.YAML in workflows["argv"][-1]
    assert "command -v renovate" in renovate.YAML and renovate.YAML.endswith('/node_modules/yaml/bin.mjs"')
    with context_of(tmp_path / "b", {"package.json": "{}\n", ".github/workflows/ci.txt": "on: push\n"}) as context:
        only_link = context.root / ".github/workflows/linked.yaml"
        only_link.symlink_to(context.root / "package.json")
        assert [command["argv"][0] for command in renovate.commands(context)] == ["renovate"]
    reusable = "on: push\njobs:\n  build:\n    uses: org/repo/.github/workflows/build.yml@v1\n"
    with context_of(tmp_path / "c", {"package.json": "{}\n", ".github/workflows/ci.yaml": reusable}) as context:
        with mock.patch.object(Path, "read_text", side_effect=AssertionError("workflow bytes read on host")):
            assert [command["argv"][0] for command in renovate.commands(context)] == ["renovate", "sh"]
    steps = "jobs:\n  t:\n    runs-on: ubuntu-latest\n    steps:\n      - run: npm test\n"  # its steps, its tests
    with context_of(tmp_path / "d", {"package.json": "{}\n", ".github/workflows/ci.yml": steps}) as context:
        assert [command["argv"][0] for command in renovate.commands(context)] == ["renovate", "sh"]


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


# A GitLab pipeline as Renovate's YAML library prints it: a job extends a hidden one, others take `default:`'s
# services or none, one inherits a single global variable; its variables reference each other and GitLab's own.
GITLAB = {
    "include": [{"template": "Security/SAST.gitlab-ci.yml"}, "ci/extra.yml"],
    "stages": ["test"],
    "variables": {"POSTGRES_DB": "app", "POSTGRES_USER": "runner", "POSTGRES_HOST_AUTH_METHOD": "trust",
                  "DATABASE_URL": "postgres://$POSTGRES_USER@postgres:5432/${POSTGRES_DB}",
                  "CACHE_DIR": "$CI_PROJECT_DIR/.cache", "PRICE": "5$$",
                  "LEVEL": {"value": "debug", "description": "the log level"}, "RAW": {"value": "$HOME", "expand": False}},
    "default": {"services": ["redis:7"]},
    ".db": {"services": [{"name": "postgres:16-alpine", "alias": "db, pg"}], "variables": {"NODE_ENV": "test"}},
    "test": {"extends": ".db", "image": "node:22", "variables": {"NODE_ENV": "ci"}, "script": ["npm test"]},
    "e2e": {"services": [{"name": "registry.example.com:5000/team/mailer:2", "entrypoint": ["/bin/mailer", "--fast"],
                          "command": ["serve"], "variables": {"MAIL_PORT": 1025}}],
            "inherit": {"variables": ["POSTGRES_DB"]}, "script": ["npm run e2e"]},
    "lint": {"inherit": {"default": False}, "script": ["npm run lint"]},
    "unit": {"script": ["npm run unit"]}}
GLOBAL = {"POSTGRES_DB": "app", "POSTGRES_USER": "runner", "POSTGRES_HOST_AUTH_METHOD": "trust",
          "DATABASE_URL": "postgres://runner@postgres:5432/app", "CACHE_DIR": "$CI_PROJECT_DIR/.cache", "PRICE": "5$",
          "LEVEL": "debug", "RAW": "$HOME"}
GITLAB_DB = {"name": "db", "image": "postgres:16-alpine", "declared_in": ".gitlab-ci.yml#test.services.0", "host": "db",
             "aliases": ["pg", "postgres"], "env": {**GLOBAL, "NODE_ENV": "ci"}, "job_env": {**GLOBAL, "NODE_ENV": "ci"},
             "computed": ["CACHE_DIR"], "wait": "ports"}
GITLAB_MAILER = {"name": "registry.example.com__team__mailer", "image": "registry.example.com:5000/team/mailer:2",
                 "declared_in": ".gitlab-ci.yml#e2e.services.0", "host": "registry.example.com__team__mailer",
                 "aliases": ["registry.example.com-team-mailer"], "env": {"POSTGRES_DB": "app", "MAIL_PORT": 1025},
                 "entrypoint": ["/bin/mailer", "--fast"], "command": ["serve"], "job_env": {"POSTGRES_DB": "app"},
                 "wait": "ports"}


def test_renovate_reads_gitlab_s_pipeline_where_it_names_services_includes_files_or_runs_scripts(tmp_path):
    """A job's script may run the tests, and the lines before them are the job's steps (`ci_steps`)."""
    for case, text, read in (("a", "test:\n  services: [postgres]\n", True), ("b", "include: ci/x.yml\n", True),
                             ("c", "test:\n  script: [make]\n", True), ("d", "stages: [test]\n", False)):
        with context_of(tmp_path / case, {"package.json": "{}\n", ".gitlab-ci.yml": text}) as context:
            commands = renovate.commands(context)
        assert [command["argv"][0] for command in commands] == ["renovate", *(["sh"] if read else [])], case
        assert not read or renovate.GITLAB in commands[1]["argv"][-1]


def test_each_service_a_gitlab_job_runs_with_is_a_fact_with_the_names_and_variables_its_runner_gives_it(tmp_path):
    """GitLab's rules (docs.gitlab.com/ci/services, /ci/yaml): a job's services are its own, its templates'
    (`extends`) or `default:`'s unless it inherits none; the runner names a service by its aliases and by its
    image without tag and registry port (`/` as `__`, then as `-`), passes it the job's variables and its own,
    and awaits the ports its image exposes. Variables expand one another once (the runner's `ExpandValue`, `$$`
    a dollar); one that references a variable the file does not define is the CI's (`computed`). An included file
    is not read: a gap names it."""
    out = read_services(tmp_path, f".gitlab-ci.yml\n{json.dumps(GITLAB)}\n")
    assert out["facts"]["services"] == [GITLAB_DB, GITLAB_MAILER, {
        "name": "redis", "image": "redis:7", "declared_in": ".gitlab-ci.yml#unit.services.0", "host": "redis",
        "env": GLOBAL, "job_env": GLOBAL, "computed": ["CACHE_DIR"], "wait": "ports"}]
    assert [(gap["kind"], gap["path"], gap["include"]) for gap in out["gaps"]] == [
        ("include_not_read", ".gitlab-ci.yml", {"template": "Security/SAST.gitlab-ci.yml"}),
        ("include_not_read", ".gitlab-ci.yml", "ci/extra.yml")]


def mark(*path):
    """A `!reference [path]` as the reader's visitor of Renovate's YAML library prints it (`renovate.REFERENCE`)."""
    return {"!reference": list(path)}


REFERENCED = {  # a pipeline that reuses its templates' sections with `!reference`
    ".setup": {"script": ["npm ci"], "services": ["postgres:16"], "variables": {"DB": "app"}},
    ".snippets": {"one": ["node scripts/migrate.js"], "two": [mark(".snippets", "one"), "node scripts/seed.js"],
                  "three": [mark(".snippets", "two")]},
    "test": {"services": mark(".setup", "services"), "variables": mark(".setup", "variables"),
             "script": [mark(".setup", "script"), mark(".snippets", "three"), "npm test"]},
    "lint": {"services": [mark(".setup", "services")], "script": ["npm run lint"]},
    "e2e": {"services": mark(".from_an_include", "services"), "script": ["npm run frontend:test"]}}


def test_a_gitlab_reference_is_the_section_it_names_and_one_not_in_the_file_is_a_gap(tmp_path):
    """GitLab resolves `!reference [<job>, <key>, ...]` when it loads the pipeline, before `extends`: the value at
    that path, its own references resolved too (ten levels at most), a list in a script's lines flattened
    (docs.gitlab.com/ci/yaml/yaml_optimization). Renovate's YAML library does not know the tag and would print
    its path as the value (`[".setup", "services"]`, a service named `.setup`): the reader's visitor marks it, and
    the reader resolves it. A list built from references is only a script's, so a `services:` one gives none, as
    GitLab rejects it; a path the file does not hold (in a file it includes, which Daodan does not read) is a gap
    naming the job, and nothing of that job is stated."""
    assert "--visit" in renovate.EACH and "!reference" in renovate.REFERENCE
    tests = [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"},
             {"root": "frontend", "runner": "jest", "declared_in": "package.json#scripts.frontend:test"}]
    files = {"package.json": json.dumps({"scripts": {"test": "jest", "frontend:test": "cd frontend && jest",
                                                     "lint": "eslint ."}})}
    out = read_steps(tmp_path, files, tests, {".gitlab-ci.yml": {"include": "ci/e2e.yml", **REFERENCED}})
    assert [(service["name"], service["image"], service["declared_in"], service["env"])
            for service in out["facts"]["services"]] == [
        ("postgres", "postgres:16", ".gitlab-ci.yml#test.services.0", {"DB": "app"})]
    assert out["facts"]["ci_steps"] == [
        {"declared_in": ".gitlab-ci.yml#test.script.0", "tests": "package.json#scripts.test", "name": "test",
         "cwd": ".", "run": "npm ci\nnode scripts/migrate.js\nnode scripts/seed.js", "env": {"DB": "app"}},
        {"declared_in": ".gitlab-ci.yml#test.script.2", "tests": "package.json#scripts.test", "name": "test",
         "test": True, "env": {"DB": "app"}}]
    [gap] = [gap for gap in out["gaps"] if gap["kind"] == "reference_not_found"]
    assert (gap["path"], gap["reference"]) == (".gitlab-ci.yml#e2e", [".from_an_include", "services"])
    assert gap["detail"] == (".gitlab-ci.yml#e2e references [.from_an_include, services], which .gitlab-ci.yml does "
                             "not hold: it may be in a file it includes, which Daodan does not read; Daodan reads "
                             "nothing of the job")
    loop = {".a": {"script": [mark(".b", "script")]}, ".b": {"script": [mark(".a", "script")]},
            "t": {"script": [mark(".a", "script"), "npm test"]}}
    out = read_steps(tmp_path / "loop", files, tests, {".gitlab-ci.yml": loop})
    assert "ci_steps" not in out["facts"] and [gap["detail"] for gap in out["gaps"]
                                               if gap["kind"] == "reference_not_found"] == [
        ".gitlab-ci.yml#t references [.a, script], which nests more than ten references: GitLab does not resolve "
        "it; Daodan reads nothing of the job"]


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="runs in the Modal test container")
def test_on_modal_renovate_s_yaml_library_with_the_reader_s_visitor_marks_each_gitlab_reference():
    """yaml 2.9.1, the library Renovate 44.239.1 pins, run as `EACH` runs it on a pipeline with `!reference`: its
    JSON holds the marks the reader resolves, and its warning stays on stderr."""
    import modal
    pipeline = ("include: ci/e2e.yml\n.setup:\n  script: [npm ci]\n  services: ['postgres:16']\n"
                "test:\n  services: !reference [.setup, services]\n  script:\n    - !reference [.setup, script]\n"
                "    - npm test\n")
    app = modal.App.lookup("daodan-pipeline-sandboxes", create_if_missing=True)
    box = modal.Sandbox.create(image=modal.Image.from_registry("node:22-bookworm-slim"), app=app, timeout=600)
    try:
        each = renovate.EACH.replace(renovate.YAML, "/tmp/node_modules/yaml/bin.mjs")
        script = (f"cd /tmp && npm install --silent yaml@2.9.1 >/dev/null 2>&1 && mkdir -p /p && cd /p && "
                  f"cat > {renovate.GITLAB} <<'EOF'\n{pipeline}EOF\n{each}")
        run = box.exec("sh", "-c", script)
        stdout, stderr = run.stdout.read(), run.stderr.read()
        run.wait()
    finally:
        box.terminate()
    print(stdout, stderr[:400], flush=True)
    assert run.returncode == 0 and stdout.splitlines()[0] == renovate.GITLAB, stderr
    doc = json.loads(stdout.splitlines()[1])
    assert doc["test"] == {"services": mark(".setup", "services"), "script": [mark(".setup", "script"), "npm test"]}
    found, gaps = renovate._gitlab(renovate.GITLAB, renovate._referenced(doc))
    assert [service["image"] for service in found] == ["postgres:16"]


def test_a_service_is_one_fact_per_declaration():
    part = {"source": "renovate", "rank": "reader", "facts": {"services": [TUDUDI, {**TUDUDI, "image": "postgres:17"}]}}
    assert premap.join([part])["services"] == [{**TUDUDI, "sources": ["renovate"]}, {
        **TUDUDI, "image": "postgres:17", "sources": ["renovate"]}]


# ------------------------------------------------------------------ a compose file a CI step starts

# fastapi/full-stack-fastapi-template at aabb90126964a164e02aff39e7c385bb0598236d: its backend's job starts two
# services of its compose files, and its tests read the project's `.env`
BACKEND = {"name": "Test Backend", "jobs": {"test-backend": {"runs-on": "ubuntu-latest", "steps": [
    {"name": "Checkout", "uses": "actions/checkout@v7"}, {"name": "Set up Python", "uses": "actions/setup-python@v7"},
    {"name": "Install uv", "uses": "astral-sh/setup-uv@v10"}, {"run": "docker compose down -v --remove-orphans"},
    {"run": "docker compose up -d --wait db mailpit"},
    {"name": "Migrate DB", "run": "uv run bash scripts/prestart.sh", "working-directory": "backend"},
    {"name": "Run tests", "run": 'uv run bash scripts/tests-start.sh "Coverage for ${{ github.sha }}"',
     "working-directory": "backend"},
    {"run": "docker compose down -v --remove-orphans"}]}}}
STEP = ".github/workflows/test-backend.yml#jobs.test-backend.steps.4"
UP = {"declared_in": STEP, "cwd": ".", "argv": ["docker", "compose", "up", "-d", "--wait", "db", "mailpit"]}
COMPOSE_YML = """---
services:
  db:
    image: postgres:18
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d app"]
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s
    volumes:
      - app-db-data:/var/lib/postgresql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:?Variable not set}
      - POSTGRES_DB=app
  backend:
    build: ./backend
    depends_on:
      db:
        condition: service_healthy
volumes:
  app-db-data:
"""  # the template's, with a bind mount
OVERRIDE_YML = ('services:\n  db:\n    ports:\n      - "5432:5432"\n  mailpit:\n    image: axllent/mailpit\n'
                '    ports:\n      - "8025:8025"\n      - "1025:1025"\n')
DOTENV = "POSTGRES_PASSWORD=changethis\nDATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5432/app\n"
# `docker-compose config --format json db mailpit` (Compose 5.6.1) on those files, the project at /work
CONFIG = {"name": "work", "networks": {"default": {"name": "work_default", "ipam": {}}}, "services": {
    "db": {"command": None, "entrypoint": None, "environment": {"POSTGRES_DB": "app", "POSTGRES_PASSWORD": "changethis"},
           "image": "postgres:18", "networks": {"default": None},
           "volumes": [{"type": "volume", "source": "app-db-data", "target": "/var/lib/postgresql", "volume": {}},
                       {"type": "bind", "source": "/work/init.sql", "target": "/docker-entrypoint-initdb.d/init.sql",
                        "read_only": True, "bind": {}}],
           "healthcheck": {"test": ["CMD-SHELL", "pg_isready -U postgres -d app"], "timeout": "10s", "interval": "10s",
                           "retries": 5, "start_period": "30s"},
           "ports": [{"mode": "ingress", "target": 5432, "published": "5432", "protocol": "tcp"}]},
    "mailpit": {"command": None, "entrypoint": None, "image": "axllent/mailpit", "networks": {"default": None},
                "ports": [{"mode": "ingress", "target": 8025, "published": "8025", "protocol": "tcp"},
                          {"mode": "ingress", "target": 1025, "published": "1025", "protocol": "tcp"}]}},
    "volumes": {"app-db-data": {"name": "work_app-db-data"}}}
COMPOSE_DB = {"name": "db", "image": "postgres:18", "declared_in": STEP + ".services.db", "host": "localhost",
              "env": {"POSTGRES_DB": "app", "POSTGRES_PASSWORD": "changethis"}, "ports": ["5432:5432"],
              "healthcheck": CONFIG["services"]["db"]["healthcheck"],
              "binds": ["init.sql:/docker-entrypoint-initdb.d/init.sql:ro"]}
COMPOSE_MAILPIT = {"name": "mailpit", "image": "axllent/mailpit", "declared_in": STEP + ".services.mailpit",
                   "host": "localhost", "ports": ["8025:8025", "1025:1025"]}


def test_the_shell_words_of_a_step_say_which_docker_compose_up_it_runs():
    assert compose.invocations("docker compose down -v --remove-orphans\ndocker compose up -d --wait db mailpit\n") == (
        [["docker", "compose", "up", "-d", "--wait", "db", "mailpit"]], [])
    assert compose.invocations("sudo docker-compose -f a.yml -f b.yml up -d && npm test") == (
        [["docker-compose", "-f", "a.yml", "-f", "b.yml", "up", "-d"]], [])
    assert compose.invocations("if true; then COMPOSE_PROFILES=ci docker compose --profile x \\\n  up -d redis; fi") == (
        [["COMPOSE_PROFILES=ci", "docker", "compose", "--profile", "x", "up", "-d", "redis"]], [])
    assert compose.invocations("echo 'docker compose up' # docker compose up\ndocker compose run --rm test") == ([], [])
    assert compose.invocations('docker compose -f "$FILE" up -d\ndocker compose -f $(pwd)/a.yml up') == (
        [], ['docker compose -f "$FILE" up -d', "docker compose -f $(pwd)/a.yml up"])
    assert compose.options(["CI=1", "docker", "compose", "-f", "a.yml", "--profile", "up", "--dry-run", "up", "-d",
                            "--wait", "--scale", "db=2", "-t", "5", "--no-deps", "db"]) == (
        ["-f", "a.yml", "--profile", "up", "--dry-run"], ["db"], True, {"CI": "1"})


def test_a_step_that_starts_docker_compose_is_a_fact_with_where_it_runs_and_its_variables(tmp_path):
    """GitHub runs a step in its `working-directory`, else the job's or the workflow's default; Compose reads the
    variables the step gets that the workflow writes (an expression is the CI's); the tests' are the job's."""
    other = {"env": {"MODE": "ci"}, "defaults": {"run": {"working-directory": "deploy"}}, "jobs": {"e2e": {
        "env": {"TOKEN": "${{ secrets.T }}"}, "steps": [
            {"run": "docker compose -f stack.yml up -d api", "env": {"TAG": 1}},
            {"run": 'docker compose -f "$STACK" up -d', "working-directory": "."}]}}}
    out = read_services(tmp_path, f".github/workflows/test-backend.yml\n{json.dumps(BACKEND)}\n"
                                  f".github/workflows/e2e.yml\n{json.dumps(other)}\n")
    assert out["facts"]["compose"] == [UP, {
        "declared_in": ".github/workflows/e2e.yml#jobs.e2e.steps.0", "cwd": "deploy",
        "argv": ["docker", "compose", "-f", "stack.yml", "up", "-d", "api"], "env": {"MODE": "ci", "TAG": "1"},
        "job_env": {"MODE": "ci", "TOKEN": "${{ secrets.T }}"}}]
    [gap] = out["gaps"]
    assert (gap["kind"], gap["path"]) == ("compose_not_read", ".github/workflows/e2e.yml#jobs.e2e.steps.1")
    assert 'docker compose -f "$STACK" up -d' in gap["detail"]
    with context_of(tmp_path / "b", {"package.json": "{}\n", ".github/workflows/t.yml": "run: docker compose up\n"}) \
            as context:
        assert [command["argv"][0] for command in renovate.commands(context)] == ["renovate", "sh"]


MAKEFILE = """\
DOCKER_COMPOSE_CMD ?= docker compose
DOCKER_COMPOSE_FILES=-f compose.yaml
FILES := $(DOCKER_COMPOSE_FILES) \\
\t-f compose.tests.yaml
.PHONY: lint start run-telemetry-tests e2e
lint:
\tnpm run lint
start:
ifneq ($(strip $(service)),)
\t$(DOCKER_COMPOSE_CMD) $(FILES) up -d $(service)
else
\t@$(DOCKER_COMPOSE_CMD) $(FILES) up --detach
endif
run-telemetry-tests: start
\tdocker build -t telemetry-tests ./test/telemetry
e2e:
\t$(MAKE) -C deploy up
"""


def test_a_makefile_target_that_starts_docker_compose_is_a_gap_naming_the_target_and_its_file(tmp_path):
    """otel-demo's telemetry job runs `make run-telemetry-tests`, whose prerequisite `start` runs Compose through a
    make variable: read from the Makefile's text (GNU make's file names, `-C`, `-f`, variables, prerequisites, a
    recipe's `$(MAKE)`; nothing run), each such target is a `compose_not_read` gap; one that reaches no Compose,
    and a Makefile that is not there, are not."""
    files = {"package.json": "{}\n", "Makefile": MAKEFILE, "deploy/Makefile": "up:\n\tdocker-compose up -d\n"}
    steps = [{"run": "make lint"}, {"run": "make run-telemetry-tests"}, {"run": "make -f Makefile SERVICE=x e2e"},
             {"run": "make"}, {"run": "make -C nowhere start"}]
    out = read_steps(tmp_path, files, [], {".github/workflows/t.yml": {"jobs": {"t": {"steps": steps}}}})
    said = [(gap["path"], gap["detail"]) for gap in out["gaps"] if gap["kind"] == "compose_not_read"]
    assert said == [
        ("Makefile#start", ".github/workflows/t.yml#jobs.t.steps.1 runs `make run-telemetry-tests`, whose target "
                           "run-telemetry-tests reaches start in Makefile, which runs Docker Compose through make "
                           "(Makefile:10 `$(DOCKER_COMPOSE_CMD) $(FILES) up -d $(service)`): Daodan does not read it, "
                           "and the services it starts do not start beside the tests"),
        ("deploy/Makefile#up", ".github/workflows/t.yml#jobs.t.steps.2 runs `make -f Makefile SERVICE=x e2e`, whose "
                               "target e2e reaches up in deploy/Makefile, which runs Docker Compose through make "
                               "(deploy/Makefile:2 `docker-compose up -d`): Daodan does not read it, and the services "
                               "it starts do not start beside the tests")]
    assert "compose" not in out["facts"]


def test_an_npm_test_script_that_starts_docker_compose_is_a_fact_too(tmp_path):
    """npm runs a script's `pre` script first, in the package's folder: the one the `tests` entry names starts the
    services there."""
    package = json.dumps({"scripts": {"pretest": "docker compose up -d --wait db", "test": "jest",
                                      "pree2e": "docker compose -f $STACK up -d", "e2e": "playwright test"}})
    with context_of(tmp_path, {"web/package.json": package, ".github/workflows/ci.yml": WORKFLOW}) as context:
        context.stated = {"tests": [{"root": "web", "runner": "jest", "declared_in": "web/package.json#scripts.test"},
                                    {"root": "web", "runner": "npm", "declared_in": "web/package.json#scripts.e2e"}]}
        commands = renovate.commands(context)
        report = {"repositories": {"local": {"packageFiles": {}}}}
        out = renovate.read(context, commands, [{"returncode": 0, "stdout": json.dumps(report), "stderr": ""},
                                                {"returncode": 0, "stdout": "", "stderr": ""}])
    assert out["facts"]["compose"] == [{"declared_in": "web/package.json#scripts.pretest", "cwd": "web",
                                        "argv": ["docker", "compose", "up", "-d", "--wait", "db"]}]
    [gap] = out["gaps"]
    assert (gap["kind"], gap["path"]) == ("compose_not_read", "web/package.json#scripts.pree2e")


def test_compose_reads_each_step_s_files_with_its_own_config_where_the_step_runs():
    e2e = {"declared_in": ".github/workflows/e2e.yml#jobs.e2e.steps.0", "cwd": "deploy",
           "argv": ["CI=1", "docker", "compose", "-f", "stack.yml", "up", "-d", "api"], "env": {"MODE": "ci"}}
    assert compose.commands(SimpleNamespace(stated={"compose": [UP, e2e]})) == [
        {"tool": "compose", "argv": ["docker-compose", "config", "--format", "json", "db", "mailpit"], "cwd": ".",
         "env": {}, "network": "none"},
        {"tool": "compose", "argv": ["docker-compose", "-f", "stack.yml", "config", "--format", "json", "api"],
         "cwd": "deploy", "env": {"MODE": "ci", "CI": "1"}, "network": "none"}]
    assert compose.commands(SimpleNamespace(stated={})) is None
    assert "compose" in container_runner.TOOLS and compose.DOWNLOAD[0].endswith("/v5.6.1/docker-compose-linux-x86_64")


def test_each_service_compose_starts_for_a_step_is_a_fact_as_compose_gives_it():
    """What `up` starts: the services the step names and those they depend on, as Compose's own `config` gives
    them; a bind mount relative to the project; a failure, and a variable Compose does not find, are gaps naming
    the step."""
    context = SimpleNamespace(stated={"compose": [UP, {**UP, "declared_in": STEP + "x"}, {**UP, "declared_in": "y"}]})
    warned = 'time="2026-11-16" level=warning msg="The \\"TAG\\" variable is not set. Defaulting to a blank string."'
    out = compose.read(context, compose.commands(context), [
        {"returncode": 0, "stdout": json.dumps(CONFIG), "stderr": "", "root": "/work"},
        {"returncode": 1, "stdout": "", "root": "/work",
         "stderr": "error while interpolating services.db.environment.[]: required variable POSTGRES_PASSWORD is "
                   "missing a value: Variable not set\n"},
        {"returncode": 0, "stdout": json.dumps({"services": {}}), "stderr": warned + "\n", "root": "/work"}])
    assert out["facts"]["services"] == [COMPOSE_DB, COMPOSE_MAILPIT]
    failed, partial = out["gaps"]
    assert (failed["kind"], failed["path"]) == ("model_failed", STEP + "x") and "POSTGRES_PASSWORD" in failed["detail"]
    assert (partial["kind"], partial["path"]) == ("model_partial", "y") and "TAG" in partial["detail"]


def test_compose_s_start_order_and_its_bind_mounts_are_facts_as_compose_gives_them():
    """`depends_on` is `after`, each service with the condition `up` waits for; a bind mount inside the project
    is relative to it, one outside as Compose gives it."""
    config = {"services": {"api": {
        "image": "example/api:1", "depends_on": {
            "db": {"condition": "service_healthy", "required": True, "restart": True},
            "migrate": {"condition": "service_completed_successfully", "required": True}},
        "volumes": [{"type": "bind", "source": "/var/run/docker.sock", "target": "/var/run/docker.sock",
                     "bind": {"create_host_path": True}},
                    {"type": "bind", "source": "/work/api/conf", "target": "/etc/api", "read_only": True, "bind": {}},
                    {"type": "tmpfs", "target": "/tmp"}]}}}
    context = SimpleNamespace(stated={"compose": [UP]})
    out = compose.read(context, compose.commands(context),
                       [{"returncode": 0, "stdout": json.dumps(config), "stderr": "", "root": "/work"}])
    [api] = out["facts"]["services"]
    assert api["after"] == {"db": "service_healthy", "migrate": "service_completed_successfully"}
    assert api["binds"] == ["/var/run/docker.sock:/var/run/docker.sock", "api/conf:/etc/api:ro"]
    assert "ignored" not in api


def test_a_shell_script_a_step_or_a_test_script_runs_is_read_for_docker_compose_as_its_caller_is(tmp_path):
    """A word that names a shell script of the checkout (`.sh`, or a shell's `#!`) is followed, three levels
    deep: its `docker compose up` runs where its caller runs, with its caller's variables; one that changes
    folder first is a gap."""
    workflow = {"jobs": {"test": {"env": {"CI": "1"}, "steps": [
        {"run": "uv run bash scripts/ci.sh", "working-directory": "backend"}, {"run": "./tools/moved"}]}}}
    package = json.dumps({"scripts": {"test": "bash scripts/test.sh && jest"}})
    files = {"backend/scripts/ci.sh": ("#!/usr/bin/env bash\nset -e\ndocker compose up -d --wait db\n"
                                       "sh scripts/stack.sh cache\npytest\n"),
             "backend/scripts/stack.sh": "docker compose up -d --wait \"$1\"\n",
             "tools/moved": "#!/bin/sh\ncd deploy\ndocker compose up -d\n",
             "web/package.json": package, "web/scripts/test.sh": "docker compose -f test.yml up -d\n",
             ".github/workflows/ci.yml": WORKFLOW}
    with context_of(tmp_path, files) as context:
        context.stated = {"tests": [{"root": "web", "runner": "jest", "declared_in": "web/package.json#scripts.test"}]}
        commands = renovate.commands(context)
        report = {"repositories": {"local": {"packageFiles": {}}}}
        out = renovate.read(context, commands, [{"returncode": 0, "stdout": json.dumps(report), "stderr": ""}, {
            "returncode": 0, "stdout": f".github/workflows/ci.yml\n{json.dumps(workflow)}\n", "stderr": ""}])
    assert out["facts"]["compose"] == [
        {"declared_in": "backend/scripts/ci.sh", "cwd": "backend", "argv": ["docker", "compose", "up", "-d", "--wait",
                                                                            "db"],
         "env": {"CI": "1"}, "job_env": {"CI": "1"}},
        {"declared_in": "web/scripts/test.sh", "cwd": "web", "argv": ["docker", "compose", "-f", "test.yml", "up", "-d"]}]
    said = {gap["path"]: gap["detail"] for gap in out["gaps"]}
    assert set(said) == {"backend/scripts/stack.sh", "tools/moved"}
    assert '"$1"' in said["backend/scripts/stack.sh"]  # its words hold its caller's argument
    assert "changes folder" in said["tools/moved"]


# ------------------------------------------------------------------ the steps of the CI's job before its tests

TUDUDI_STEPS = [
    {"declared_in": ".github/workflows/ci.yml#jobs.test.steps.2", "tests": "package.json#scripts.test",
     "name": "Install dependencies", "cwd": ".", "run": "npm install", "env": {"DATABASE_URL": DATABASE_URL}},
    {"declared_in": ".github/workflows/ci.yml#jobs.test.steps.3", "tests": "package.json#scripts.test",
     "name": "Run linting", "cwd": ".", "run": "npm run lint", "env": {"DATABASE_URL": DATABASE_URL}},
    {"declared_in": ".github/workflows/ci.yml#jobs.test.steps.4", "tests": "package.json#scripts.test",
     "name": "Bootstrap an empty database and run pending migrations", "cwd": "backend",
     "run": CI["jobs"]["test"]["steps"][4]["run"], "env": {"DATABASE_URL": DATABASE_URL, "NODE_ENV": "production"}}]
FASTAPI_SCRIPTS = {  # fastapi/full-stack-fastapi-template's, at the commit of BACKEND
    "backend/scripts/prestart.sh": "#! /usr/bin/env bash\n\nset -e\nset -x\n\n# Run migrations\nalembic upgrade head\n\n"
                                   "# Create initial data in DB\npython app/initial_data.py\n",
    "backend/scripts/tests-start.sh": '#! /usr/bin/env bash\nset -e\nset -x\n\nbash scripts/test.sh "$@"\n',
    "backend/scripts/test.sh": "#!/usr/bin/env bash\n\nset -e\nset -x\n\nFASTAPI_ENV=development coverage run -m pytest "
                               'tests/\ncoverage report\ncoverage html --title "${@-coverage}"\n'}


def read_steps(tmp_path, files: dict, tests: list[dict], workflows: dict) -> dict:
    """What the workflow reader states of `workflows` (`{path: document}`, as Renovate's YAML library prints them)
    for a project of `files` whose `tests` entries the readers before it state."""
    with context_of(tmp_path, {**files, ".github/workflows/ci.yml": WORKFLOW}) as context:
        context.stated = {"tests": tests}
        commands = renovate.commands(context)
        report = {"repositories": {"local": {"packageFiles": {}}}}
        printed = "".join(f"{path}\n{json.dumps(doc)}\n" for path, doc in workflows.items())
        return renovate.read(context, commands, [{"returncode": 0, "stdout": json.dumps(report), "stderr": ""},
                                                 {"returncode": 0, "stdout": printed, "stderr": ""}])


def test_the_steps_a_job_runs_before_its_tests_are_facts_with_where_and_how_github_runs_them(tmp_path):
    """The job's test step is its first that runs a `tests` entry: an npm script that starts what the entry's
    starts (tududi's `npm run backend:test`, its `test`'s), or the entry's runner, in the shell scripts it runs
    too (FastAPI's `uv run bash scripts/tests-start.sh`, whose `scripts/test.sh` runs pytest). Each `run:` step
    before it is a fact: its folder, its text, the variables the workflow, the job and the step give it. The
    checkout, a toolchain's setup action and Docker Compose's `up` and `down` (its services are the `compose`
    facet's) are not; nothing after the tests is. The test step is a fact with `test` and the variables it gives
    the tests: the workflow's, the job's, the step's and those set on the command that starts the runner, in the
    scripts it runs too (FastAPI's `FASTAPI_ENV=development coverage run -m pytest tests/`)."""
    tests = [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"},
             {"root": ".", "runner": "jest", "declared_in": "package.json#scripts.frontend:test"},
             {"root": "backend", "runner": "pytest", "declared_in": "backend/pyproject.toml"}]
    files = {"package.json": json.dumps({"scripts": TUDUDI_SCRIPTS}), **FASTAPI_SCRIPTS}
    out = read_steps(tmp_path, files, tests, {".github/workflows/ci.yml": CI,
                                              ".github/workflows/test-backend.yml": BACKEND})
    assert out["facts"]["ci_steps"] == [*TUDUDI_STEPS, {
        "declared_in": ".github/workflows/ci.yml#jobs.test.steps.5", "tests": "package.json#scripts.test",
        "name": "Run backend tests", "test": True, "env": {"DATABASE_URL": DATABASE_URL}}, {
        "declared_in": ".github/workflows/test-backend.yml#jobs.test-backend.steps.5", "tests": "backend/pyproject.toml",
        "name": "Migrate DB", "cwd": "backend", "run": "uv run bash scripts/prestart.sh"}, {
        "declared_in": ".github/workflows/test-backend.yml#jobs.test-backend.steps.6", "tests": "backend/pyproject.toml",
        "name": "Run tests", "test": True, "env": {"FASTAPI_ENV": "development"}}]
    assert "gaps" not in out


def test_a_step_before_the_tests_that_daodan_does_not_run_is_a_fact_with_its_cause(tmp_path):
    """An action other than the checkout and a toolchain's setup, a condition, an expression of the CI (its
    secrets among them), a shell other than bash and sh, Docker Compose run against its own services: a fact with
    its `cause`. A job whose steps run no `tests` entry states nothing."""
    workflow = {"jobs": {"lint": {"steps": [{"run": "npm run lint"}]}, "unit": {
        "defaults": {"run": {"shell": "bash"}}, "env": {"TOKEN": "x"}, "steps": [
            {"uses": "actions/checkout@v5"}, {"uses": "pnpm/action-setup@v4"},
            {"uses": "actions/cache@v4", "with": {"path": "~/.npm"}},
            {"name": "Seed", "run": "make seed", "if": "github.event_name == 'push'"},
            {"name": "Token", "run": "echo ${{ secrets.NPM_TOKEN }} > .npmrc"},
            {"name": "Windows", "run": "Write-Host hi", "shell": "pwsh"},
            {"name": "Query", "run": "docker compose exec -T db psql -c 'select 1'"},
            {"name": "Build", "run": "npm run build", "env": {"MODE": "ci"}},
            {"run": "docker compose up -d db"},
            {"name": "Tests", "run": "LEVEL=debug SHA=$GITHUB_SHA npm test",
             "env": {"KEY": "${{ secrets.KEY }}"}}]}}}
    tests = [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"}]
    files = {"package.json": json.dumps({"scripts": {"test": "jest", "lint": "eslint .", "build": "tsc"}})}
    out = read_steps(tmp_path, files, tests, {".github/workflows/unit.yml": workflow})
    path = ".github/workflows/unit.yml#jobs.unit.steps."
    facts = {item["declared_in"].removeprefix(path): item for item in out["facts"]["ci_steps"]}
    assert sorted(facts, key=int) == ["2", "3", "4", "5", "6", "7", "9"]
    assert facts["9"] == {"declared_in": path + "9", "tests": "package.json#scripts.test", "name": "Tests", "test": True,
                          "env": {"TOKEN": "x", "KEY": "${{ secrets.KEY }}", "LEVEL": "debug",
                                  "SHA": "$GITHUB_SHA"}, "computed": ["SHA"]}  # a value the shell computes
    assert facts["7"] == {"declared_in": path + "7", "tests": "package.json#scripts.test", "name": "Build", "cwd": ".",
                          "run": "npm run build", "env": {"TOKEN": "x", "MODE": "ci"}, "shell": "bash"}
    for number, said in (("2", "actions/cache@v4"), ("3", "github.event_name == 'push'"),
                         ("4", "${{ secrets.NPM_TOKEN }}"), ("5", "pwsh"), ("6", "docker compose exec")):
        assert said in facts[number]["cause"] and "run" not in facts[number], (number, facts[number])
    assert facts["3"]["name"] == "Seed"


def test_an_observer_s_runs_get_the_steps_before_their_tests_and_a_gap_for_each_that_does_not_run():
    """The steps before the tests an observer runs (`declared_in` of its runs), once each, in the job's order;
    a `ci_step_not_run` gap for one with a `cause`. The variables their test steps give the tests reach them,
    but one the CI or the shell computes, or two test steps give apart, which is a `ci_step_incomplete` gap."""
    def fact(number: int, tests: str, **more) -> dict:
        return {"declared_in": f"ci.yml#jobs.t.steps.{number}", "tests": tests, "cwd": ".", "run": f"echo {number}",
                **more}
    record = {"ci_steps": [fact(10, "a"), fact(2, "a"), fact(2, "b"), fact(3, "c"),
                           {"declared_in": "ci.yml#jobs.t.steps.4", "tests": "b", "name": "Cache",
                            "cause": "it uses actions/cache@v4: Daodan runs no action"},
                           {"declared_in": "ci.yml#jobs.t.steps.11", "tests": "a", "test": True,
                            "env": {"MODE": "test", "KEY": "${{ secrets.KEY }}", "SHA": "$(git rev-parse HEAD)",
                                    "LEVEL": "1", "PORT": 1}, "computed": ["SHA"]},
                           {"declared_in": "ci.yml#jobs.u.steps.3", "tests": "b", "test": True,
                            "env": {"MODE": "test", "LEVEL": "2"}}]}
    planned = dynamic.ci_steps(record, [{"root": ".", "runner": "jest", "declared_in": "a"},
                                        {"root": ".", "runner": "jest", "declared_in": "b"}])
    assert [step["run"] for step in planned["steps"]] == ["echo 2", "echo 10"]
    assert planned["steps"][0] == {"declared_in": "ci.yml#jobs.t.steps.2", "cwd": ".", "run": "echo 2"}
    gap, first, second = planned["gaps"]
    assert (gap["kind"], gap["path"]) == ("ci_step_not_run", "ci.yml#jobs.t.steps.4")
    assert "Cache" in gap["detail"] and "actions/cache@v4" in gap["detail"]
    assert planned["env"] == {"MODE": "test", "PORT": "1"}
    assert [(item["kind"], item["path"]) for item in (first, second)] == [
        ("ci_step_incomplete", "ci.yml#jobs.t.steps.11"), ("ci_step_incomplete", "ci.yml#jobs.u.steps.3")]
    assert "KEY" in first["detail"] and "SHA" in first["detail"] and "LEVEL" in second["detail"]
    assert dynamic.ci_steps({}, [{"root": ".", "runner": "go"}]) == {"steps": [], "gaps": [], "env": {}}


def test_a_test_step_without_variables_is_a_fact_too_so_a_run_no_workflow_runs_is_said(tmp_path):
    """Every test step is a fact (`test`), its `env` only when it gives the tests variables: a run whose
    `declared_in` no fact names, in a project whose workflows run some of its tests, is a `tests_not_in_ci` gap
    naming those (tududi's `frontend:test`, beside the `test` its CI runs): what fails there the CI never ran.
    Where no workflow Daodan reads runs a test, nothing is said."""
    workflow = {"jobs": {"unit": {"steps": [{"uses": "actions/checkout@v5"}, {"name": "Tests", "run": "npm test"}]}}}
    tests = [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"},
             {"root": ".", "runner": "jest", "declared_in": "package.json#scripts.frontend:test"}]
    files = {"package.json": json.dumps({"scripts": {"test": "cd backend && jest", "frontend:test": "jest"}})}
    out = read_steps(tmp_path, files, tests, {".github/workflows/unit.yml": workflow})
    assert out["facts"]["ci_steps"] == [{"declared_in": ".github/workflows/unit.yml#jobs.unit.steps.1",
                                         "tests": "package.json#scripts.test", "name": "Tests", "test": True}]
    planned = dynamic.ci_steps(out["facts"], tests)
    assert (planned["steps"], planned["env"]) == ([], {})
    [gap] = planned["gaps"]
    assert (gap["kind"], gap["path"]) == ("tests_not_in_ci", "package.json#scripts.frontend:test")
    assert gap["detail"] == ("package.json#scripts.frontend:test: no workflow Daodan reads runs these tests (its CI "
                             "runs package.json#scripts.test): a failure of theirs is one the project's CI never sees")
    assert dynamic.ci_steps({"ci_steps": []}, tests)["gaps"] == []


PIPELINE = {  # a GitLab pipeline whose jobs run the tests of two entries
    "variables": {"POSTGRES_DB": "app", "DATABASE_URL": "postgres://u:p@postgres/$POSTGRES_DB"},
    "default": {"before_script": ["npm ci"]},
    "lint": {"script": ["npm run lint"]},
    "test": {"services": ["postgres:16"], "variables": {"NODE_ENV": "test"},
             "script": ["node scripts/migrate.js", ["node scripts/seed.js"], "SHA=$CI_COMMIT_SHA npm test",
                        "npm run build"]},
    "e2e": {"inherit": {"default": False}, "before_script": ["docker compose up -d"],
            "script": ["npm run frontend:test"]}}


def test_the_lines_a_gitlab_job_runs_before_its_tests_are_one_step_and_its_test_line_the_test_step(tmp_path):
    """GitLab runs a job's `before_script` (its own or `default:`'s) and `script` lines in one shell in the
    project's folder, nested lists flattened, stopping at the first that fails: the lines before the first that
    runs a `tests` entry are one step, with the job's variables as its runner expands them; that line is the test
    step, with those variables and the ones it sets. A line before the tests that starts Docker Compose, which runs
    on the Docker the job starts, is a cause: Daodan runs no line of that job."""
    tests = [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"},
             {"root": "frontend", "runner": "jest", "declared_in": "package.json#scripts.frontend:test"}]
    files = {"package.json": json.dumps({"scripts": {"test": "jest", "frontend:test": "cd frontend && jest",
                                                     "lint": "eslint .", "build": "tsc"}})}
    out = read_steps(tmp_path, files, tests, {".gitlab-ci.yml": PIPELINE})
    variables = {"POSTGRES_DB": "app", "DATABASE_URL": "postgres://u:p@postgres/app", "NODE_ENV": "test"}
    assert out["facts"]["ci_steps"] == [
        {"declared_in": ".gitlab-ci.yml#test.before_script.0", "tests": "package.json#scripts.test", "name": "test",
         "cwd": ".", "run": "npm ci\nnode scripts/migrate.js\nnode scripts/seed.js", "env": variables},
        {"declared_in": ".gitlab-ci.yml#test.script.2", "tests": "package.json#scripts.test", "name": "test",
         "test": True, "env": {**variables, "SHA": "$CI_COMMIT_SHA"}, "computed": ["SHA"]},
        {"declared_in": ".gitlab-ci.yml#e2e.before_script.0", "tests": "package.json#scripts.frontend:test",
         "name": "e2e", "cause": "it runs `docker compose up -d`, on the Docker the job starts, which Daodan does not "
                                 "read: Daodan runs no line of the job"},
        {"declared_in": ".gitlab-ci.yml#e2e.script.0", "tests": "package.json#scripts.frontend:test", "name": "e2e",
         "test": True, "env": {"POSTGRES_DB": "app", "DATABASE_URL": "postgres://u:p@postgres/app"}}]
    planned = dynamic.ci_steps(out["facts"], tests)
    assert [step["declared_in"] for step in planned["steps"]] == [".gitlab-ci.yml#test.before_script.0"]
    assert planned["env"] == {"POSTGRES_DB": "app", "DATABASE_URL": "postgres://u:p@postgres/app", "NODE_ENV": "test"}
    assert [(gap["kind"], gap["path"]) for gap in planned["gaps"]] == [
        ("ci_step_incomplete", ".gitlab-ci.yml#test.script.2"), ("ci_step_not_run", ".gitlab-ci.yml#e2e.before_script.0")]


PLAYWRIGHT = {"jobs": {"test-playwright": {"steps": [  # the template's playwright.yml, its job's steps
    {"uses": "actions/checkout@v7"}, {"uses": "oven-sh/setup-bun@v2"},
    {"name": "Setup tmate session", "uses": "mxschmitt/action-tmate@v3",
     "if": "${{ github.event_name == 'workflow_dispatch' }}"},
    {"run": "uv sync", "working-directory": "backend"}, {"run": "bun ci", "working-directory": "frontend"},
    {"run": "docker compose build"}, {"run": "docker compose run --rm backend bash scripts/prestart.sh"},
    {"name": "Run Playwright tests", "run": "docker compose run --rm playwright bunx playwright test "
                                            "--fail-on-flaky-tests --shard=${{ matrix.shardIndex }}/4"},
    {"run": "docker compose down -v --remove-orphans"}]}}}


def test_a_job_that_runs_its_tests_inside_docker_compose_says_its_test_step_and_each_step_before_it_not_run(tmp_path):
    """FastAPI's playwright job runs the frontend's tests in `docker compose run … playwright`, in a container
    Compose builds: Daodan does not read inside it, so the job's test step is a fact with its cause, naming the
    service and the command, and each step before it one that does not run, with its own cause or that one."""
    frontend = {"root": "frontend", "runner": "npm", "declared_in": "frontend/package.json#scripts.test"}
    files = {"frontend/package.json": json.dumps({"scripts": {"test": "bunx playwright test"}})}
    out = read_steps(tmp_path, files, [frontend], {".github/workflows/playwright.yml": PLAYWRIGHT})
    path = ".github/workflows/playwright.yml#jobs.test-playwright.steps."
    facts = {item["declared_in"].removeprefix(path): item for item in out["facts"]["ci_steps"]}
    assert sorted(facts, key=int) == ["2", "3", "4", "6", "7"] and all("run" not in item for item in facts.values())
    assert all(item["tests"] == frontend["declared_in"] for item in facts.values())
    tested = facts["7"]
    assert tested["name"] == "Run Playwright tests" and "Compose service playwright" in tested["cause"]
    assert "bunx playwright test --fail-on-flaky-tests" in tested["cause"]
    assert "action-tmate" in facts["2"]["cause"] and "docker compose run --rm backend" in facts["6"]["cause"]
    assert facts["3"]["cause"] == facts["4"]["cause"] and path + "7" in facts["3"]["cause"]
    planned = dynamic.ci_steps(out["facts"], [frontend])
    assert planned["steps"] == [] and [gap["path"] for gap in planned["gaps"]] == [path + n for n in "23467"]


# ------------------------------------------------------------------ the .env files Git tracks

def git_project(root: Path, files: dict, tracked: list[str]) -> Path:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "--", *tracked], check=True)
    return root


def test_the_copy_carries_the_env_files_git_tracks_and_names_each_file_it_withholds(tmp_path):
    """As the CI's checkout: the `.env` files Git tracks reach the container's copy (`dotenv` names them); a file
    Daodan never reads that Git does not track, or that is no `.env` file, stays out as a `file_withheld` gap
    naming it and the rule; what Git ignores is no checkout's, and no gap."""
    project = git_project(tmp_path / "p", {
        ".env": DOTENV, "backend/.env.test": "MODE=test\n", "certs/server.pem": "x\n", ".env.local": "TOKEN=mine\n",
        ".env.prod": "TOKEN=prod\n", ".gitignore": ".env.prod\n", "app.py": "print(1)\n"},
        [".env", "backend/.env.test", "certs/server.pem", ".gitignore", "app.py"])
    digest = container.copy_perimeter(project, tmp_path / "copy.tar")
    with tarfile.open(tmp_path / "copy.tar") as bundle:
        assert {member.name for member in bundle.getmembers() if member.isfile()} == {
            "work/.env", "work/backend/.env.test", "work/.gitignore", "work/app.py"}
    assert digest["dotenv"] == [".env", "backend/.env.test"]
    withheld = {gap["path"]: gap["detail"] for gap in digest["gaps"] if gap["kind"] == "file_withheld"}
    assert sorted(withheld) == [".env.local", "certs/server.pem"] and len(digest["gaps"]) == 2
    assert "*.pem" in withheld["certs/server.pem"] and "Git does not track it" in withheld[".env.local"]


def test_in_the_pre_map_s_container_each_value_of_a_tracked_env_file_is_its_name(tmp_path):
    """The pre-map keeps no value of a tracked `.env` file: before its commands, its container writes in each such
    file of the copy, in place of each value, a placeholder naming the file and the variable (`container.named`),
    which Compose interpolates as it would the value; comments stay, the further lines of a value over several go."""
    work = tmp_path / "work"
    (work / "deploy").mkdir(parents=True)
    (work / ".env").write_text("# the stack\nexport SECRET_KEY='s3cr3t value'\nMULTI=\"a\nb=c\nd\"\n\nPORT = 8000\n",
                               encoding="utf-8", newline="\n")
    (work / "deploy" / ".env.ci").write_text("TOKEN=abc\n", encoding="utf-8", newline="\n")
    kept = tmp_path / "state" / "dotenv-values.json"
    subprocess.run(["sh", "-c", container.named(str(work), str(kept))], check=True)
    assert json.loads(kept.read_text(encoding="utf-8")) == {  # in the container only, before the names
        ".env": {"SECRET_KEY": "s3cr3t value", "MULTI": "a\nb=c\nd", "PORT": "8000"}, "deploy/.env.ci": {"TOKEN": "abc"}}
    subprocess.run(["sh", "-c", container.named(str(work), str(kept))], check=True)  # again: the values stay
    assert json.loads(kept.read_text(encoding="utf-8"))[".env"]["SECRET_KEY"] == "s3cr3t value"
    assert (work / ".env").read_text(encoding="utf-8") == (
        f"# the stack\nexport SECRET_KEY={placed('.env', 'SECRET_KEY')}\nMULTI={placed('.env', 'MULTI')}\n"
        f"b={placed('.env', 'b')}\n\nPORT ={placed('.env', 'PORT')}\n")
    assert (work / "deploy" / ".env.ci").read_text(encoding="utf-8") == f"TOKEN={placed('deploy/.env.ci', 'TOKEN')}\n"
    with mock.patch.object(container, "run_in_container", return_value={"state": "done"}) as ran:
        container.run_commands(tmp_path / "p", [{"tool": "t", "argv": ["true"], "network": "registries"},
                                                {"tool": "t", "argv": ["true"]}], image="i", out_dir=tmp_path / "out",
                               values=True)  # the values beside the copy: Daodan's helper alone (D-311)
    assert ran.call_args.args[1][2].startswith(container.named(values=container.DOTENV_VALUES)) and ran.call_args.kwargs["prepare"][2].startswith(
        container.named(values=container.DOTENV_VALUES))


def placed(file: str, name: str) -> str:
    """What the pre-map's container writes in place of a value (`container.named`): no colon Compose splits on."""
    return f"./daodan-dotenv-{file.encode().hex()}-{name.encode().hex()}"


PLACED = json.loads(json.dumps(CONFIG).replace('"changethis"', f'"{placed(".env", "POSTGRES_PASSWORD")}"'))


def test_a_value_compose_takes_from_a_tracked_env_file_is_a_fact_with_its_name_and_its_file():
    """Compose's `config` over the placeholders: the fact keeps `${NAME}` where the value stood and, in `dotenv`,
    the file each name comes from; the plan carries both, and the run puts the value in place where it starts the
    service (`container.filled`)."""
    context = SimpleNamespace(stated={"compose": [UP]})
    out = compose.read(context, compose.commands(context), [
        {"returncode": 0, "stdout": json.dumps(PLACED), "stderr": "", "root": "/work"}])
    db = out["facts"]["services"][0]
    assert db == {**COMPOSE_DB, "env": {"POSTGRES_DB": "app", "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}"},
                  "dotenv": {"POSTGRES_PASSWORD": ".env"}}
    spec = dynamic.services({"services": [db]})["services"][0]
    assert spec["env"]["POSTGRES_PASSWORD"] == "${POSTGRES_PASSWORD}" and spec["dotenv"] == {"POSTGRES_PASSWORD": ".env"}
    filled = container.filled({**spec, "args": ["--health-cmd", "pg_isready -U ${POSTGRES_PASSWORD} ${OTHER}"]},
                              {".env": {"POSTGRES_PASSWORD": "changethis"}})
    assert filled["env"]["POSTGRES_PASSWORD"] == "changethis" and filled["args"][1] == "pg_isready -U changethis ${OTHER}"
    assert container.filled(SPEC, {".env": {"POSTGRES_PASSWORD": "x"}}) == SPEC


def test_the_values_of_a_tracked_env_file_are_read_as_compose_reads_them(tmp_path):
    """`container.RESOLVE`, which runs in a container of Daodan's over the copy's tracked `.env` files: each
    variable's value as Compose's own reader gives it, quotes, comments and references to those before it read."""
    (tmp_path / ".env").write_text(
        DOTENV + 'PROJECT_NAME="Full Stack FastAPI Project" # its name\nexport KEY=\'a ${B}\'\nMULTI="one\\ntwo\n'
        'three"\nPLAIN=x y # a comment\nDEFAULT=${MISSING:-fallback}\n', encoding="utf-8", newline="\n")
    said = subprocess.run([sys.executable, "-c", container.RESOLVE, ".env"], cwd=tmp_path, capture_output=True,
                          text=True, timeout=60)
    assert container.dotenv_answer(said.stdout, said.returncode) == {".env": {
        "POSTGRES_PASSWORD": "changethis", "DATABASE_URL": "postgresql://postgres:changethis@localhost:5432/app",
        "PROJECT_NAME": "Full Stack FastAPI Project", "KEY": "a ${B}", "MULTI": "one\ntwo\nthree", "PLAIN": "x y",
        "DEFAULT": "fallback"}}
    with pytest.raises(RuntimeError, match=r"\.env"):
        container.dotenv_answer("Traceback (most recent call last):\n", 1)


def test_an_example_env_file_is_public_by_its_name_and_only_the_true_files_values_are_secret():
    """`.env.example`, `.env.sample`, `.env.template`, `.env.dist`, with a name between (`.env.local.example`),
    in any case, are examples the project publishes; `.env`, `.env.local`, `.env.example.local` are not."""
    for name, public in ((".env.example", True), (".env.sample", True), (".env.template", True),
                         (".env.dist", True), (".env.local.example", True), (".ENV.Example", True),
                         (".env", False), (".env.local", False), (".env.example.local", False),
                         (".env.production", False), ("env.example", False)):
        assert container.example(name) is public, name
    values = {".env.example": {"URL": "http://localhost:3000"}, "web/.env.local.example": {"A": "abcdef"},
              ".env": {"KEY": "changethis"}}
    assert container.secret(values) == {".env": {"KEY": "changethis"}}


def test_each_value_of_a_tracked_env_file_is_masked_wherever_it_stands_and_a_short_one_as_a_whole_word():
    """What a run keeps names the variable in place of its value wherever it stands, inside a longer word too
    (`-DVERSION=1.28.0x`); a value shorter than four characters only as a whole word, as it would mask the text's
    own words inside longer ones; a boolean word or a number of five digits at most stays, as the text's own words
    and ports would be masked with it. `partial` says once which values a run may keep."""
    values = {".env": {
        "SECRET_KEY": "changethis", "FIRST_SUPERUSER_PASSWORD": "changethis", "SMTP_TLS": "False", "SMTP_PORT": "1025",
        "DB": "app", "MAIL": "admin@example.com", "DATABASE_URL": "postgresql://postgres:changethis@db:5432/app",
        "VERSION": "1.28.0"}}
    hide = container.masker(values)
    assert hide("url postgresql://postgres:changethis@db:5432/app, key changethis, admin@example.com; False 1025 app "
                "notchangethis -DVERSION=1.28.0x application /app/") == (
        "url [.env:DATABASE_URL], key [.env:FIRST_SUPERUSER_PASSWORD,.env:SECRET_KEY], [.env:MAIL]; False 1025 "
        "[.env:DB] not[.env:FIRST_SUPERUSER_PASSWORD,.env:SECRET_KEY] -DVERSION=[.env:VERSION]x application "
        "/[.env:DB]/")
    assert container.masker({".env": {"TLS": "False", "PORT": "5432"}}) is None and container.masker({}) is None
    [gap] = container.partial(values)
    assert (gap["kind"], gap["variables"]) == ("mask_partial", [".env:DB", ".env:SMTP_PORT", ".env:SMTP_TLS"])
    assert gap["detail"] == (
        "Daodan masks the value of .env:DB, shorter than four characters, only where it stands as a whole word, and "
        "does not mask those of .env:SMTP_PORT, .env:SMTP_TLS, a boolean word or a number of five digits at most: "
        "what the run keeps may hold them")
    assert container.partial({".env": {"KEY": "changethis", "EMPTY": ""}}) == []


def test_an_output_keeps_no_value_masked_as_text_or_as_json_or_is_withheld(tmp_path):
    """A `-DVERSION=<value>` build: its log is masked as text; its compilation database as JSON, string by string,
    so it stays JSON whatever escapes the value takes there, a number that is a value too; an output that is not
    text and holds a value (an index, an object file) is never patched: it is removed, a gap naming the variables
    and the output."""
    values = {".env": {"VERSION": "clé-1.28.0", "BUILD": "20261116", "DEBUG": "true"}}
    hide = container.masker(values)
    out = tmp_path / "out"
    (out / "build").mkdir(parents=True)
    files = {"build/build.log": "-- VERSION clé-1.28.0\n".encode(),
             "build/compile_commands.json": json.dumps(
                 [{"directory": "/work/build", "file": "main.cpp", "output": "main.o",
                   "command": 'c++ -DVERSION=\\"clé-1.28.0\\" -DDEBUG=true -c main.cpp'}], indent=2).encode(),
             "build/index.scip": b"\n\x08main.cpp\x12\x0bcl\xc3\xa9-1.28.0\x00",
             "build/count.json": json.dumps({"build": 20261116}).encode(),
             "build/notes.txt": "vclé-1.28.0\n".encode(),
             "build/clean.json": json.dumps({"ok": True}).encode()}
    for rel, data in files.items():
        (out / rel).write_bytes(data)
    paths = [str(out / rel) for rel in files]
    kept, gaps = container.scrubbed(paths, hide, values, out)
    assert kept == [str(out / rel) for rel in ("build/build.log", "build/compile_commands.json", "build/count.json",
                                               "build/notes.txt", "build/clean.json")]
    assert (out / "build/notes.txt").read_text(encoding="utf-8") == "v[.env:VERSION]\n"  # inside a longer word
    assert (out / "build/build.log").read_text(encoding="utf-8") == "-- VERSION [.env:VERSION]\n"
    [database] = json.loads((out / "build/compile_commands.json").read_text(encoding="utf-8"))
    assert database["command"] == 'c++ -DVERSION=\\"[.env:VERSION]\\" -DDEBUG=true -c main.cpp'
    assert (out / "build/clean.json").read_bytes() == files["build/clean.json"]  # nothing masked: as written
    assert json.loads((out / "build/count.json").read_text(encoding="utf-8")) == {"build": "[.env:BUILD]"}  # D-311
    assert [(gap["kind"], gap["path"], gap["variables"]) for gap in gaps] == [
        ("output_withheld", "build/index.scip", [".env:VERSION"])]
    assert gaps[0]["detail"] == ("build/index.scip holds the value of .env:VERSION, which Daodan keeps nowhere: the "
                                 "output is not kept")
    assert sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()) == [
        "build/build.log", "build/clean.json", "build/compile_commands.json", "build/count.json", "build/notes.txt"]
    assert not any(b"cl\xc3\xa9-1.28.0" in p.read_bytes() or b"20261116" in p.read_bytes()
                   for p in out.rglob("*") if p.is_file())
    assert container.scrubbed(paths[:1], None, {}, out) == (paths[:1], [])  # no value: nothing read


def test_a_value_the_project_s_other_files_hold_is_public_and_text_is_masked_never_withheld(tmp_path):
    """A private project, 18 November 2026 (D-311): go-enry's answer, which lists the paths, was withheld for
    `VERTEX_LOCATION=global` beside `globalTheme.ts`, and the language scan failed. The reader of the tracked
    `.env` files (`RESOLVE` with `DAODAN_PUBLIC`, its seconds) says which values the other files hold, in a path or
    in their content, the `.env*` files aside, reading each file by pieces: those are public (`secret`). Text is
    masked and kept, a JSON output string by string and number by number; only another output that holds a
    secret value is withheld."""
    files = {".env.dev": "VERTEX_LOCATION=global\nMONGODB_DATABASE=acme\nAPI_KEY=sk-live-9f31\n"
                         "BUILD_NUMBER=98317713\n",
             ".env.prod": "ACME_ENV=prod\nREGION=europe-west8\n", ".env.example": "OTHER=sk-live-9f31\n",
             "react-app/src/lib/globalTheme.ts": "export {}\n", "assets/product.svg": "<svg/>\n",
             "package.json": '{"name": "acme-app"}\n'}
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8", newline="\n")
    (tmp_path / "big.bin").write_bytes(b"x" * (2**20 - 5) + b"europe-west8\n")  # across the first piece's end
    dotenv = [".env.dev", ".env.prod", ".env.example"]

    def read(seconds: str | None):
        said = subprocess.run([sys.executable, "-c", container.RESOLVE, *dotenv], cwd=tmp_path, capture_output=True,
                              text=True, timeout=60, env={**os.environ, **({"DAODAN_PUBLIC": seconds} if seconds else {})})
        return container.dotenv_answer(said.stdout, said.returncode), container.published(said.stdout)

    values, public = read(str(container.PUBLIC_SECONDS))
    assert public == {"global", "acme", "prod", "europe-west8"}  # the key stands only in .env files
    assert container.secret(values, public) == {".env.dev": {"API_KEY": "sk-live-9f31", "BUILD_NUMBER": "98317713"}}
    assert read("0")[1] == set() and read(None)[1] == set()  # nothing read in time, or not asked: all stays secret
    assert container.secret(values) == {path: found for path, found in values.items() if path != ".env.example"}
    kept = container.secret(values, public)
    out = tmp_path / "out"
    (out / "results/1").mkdir(parents=True)
    answer = json.dumps([{"path": "react-app/src/lib/globalTheme.ts", "language": "TypeScript"},
                         {"path": "assets/product.svg", "language": "SVG"}]).encode()
    written = {"stdout": answer, "stderr": b"warning: sk-live-9f31\n", "count.json": b'{"build": 98317713}',
               "public.scip": b"\x08global\x00prod\x00", "index.scip": b"\x08sk-live-9f31\x00"}
    for name, data in written.items():
        (out / "results/1" / name).write_bytes(data)
    produced = [str(out / "results/1" / name) for name in written]
    left, gaps = container.scrubbed(produced, container.masker(kept), kept, out)
    assert left == produced[:4]
    assert [(gap["path"], gap["variables"]) for gap in gaps] == [("results/1/index.scip", [".env.dev:API_KEY"])]
    assert (out / "results/1/stdout").read_bytes() == answer  # the public words as they were
    assert (out / "results/1/public.scip").read_bytes() == written["public.scip"]
    assert (out / "results/1/stderr").read_text(encoding="utf-8") == "warning: [.env.dev:API_KEY]\n"
    assert json.loads((out / "results/1/count.json").read_text(encoding="utf-8")) == {
        "build": "[.env.dev:BUILD_NUMBER]"}
    project = git_project(tmp_path / "project", {".env.dev": "A=b\n", "src/acme.md": "x\n", "notes.txt": "y\n"},
                          [".env.dev", "src/acme.md"])
    digest = container.copy_perimeter(project, tmp_path / "copy.tar")
    assert digest["dotenv"] == [".env.dev"] and digest["published"] == ["src/acme.md"]  # what Git tracks alone


def test_a_pre_map_command_never_sees_a_value_and_only_daodan_s_helper_gets_them(tmp_path):
    """D-311: the pre-map's commands run over placeholders (`named`), so no value is read for them and what they
    wrote is kept as written (`blind`); the true values are written beside the copy (`DOTENV_VALUES`) only in the
    container of Daodan's helper that reads them (`daodan-dockerfile`, which runs no code of the project), whose
    run keeps the check. Gradle, Maven, npm or CMake, which run the project's code, never find them."""
    commands = [{"tool": "t", "argv": ["true"], "network": "registries"}, {"tool": "t", "argv": ["true"]}]
    with mock.patch.object(container, "run_in_container", return_value={"state": "done"}) as ran:
        container.run_commands(tmp_path / "p", commands, image="i", out_dir=tmp_path / "out")
        container.run_commands(tmp_path / "p", commands, image="i", out_dir=tmp_path / "out", values=True)
    plain, helper = ran.call_args_list
    for script in (plain.args[1][2], plain.kwargs["prepare"][2]):
        assert script.startswith(container.named()) and container.DOTENV_VALUES not in script
    assert plain.kwargs["blind"] is True and helper.kwargs["blind"] is False
    assert helper.args[1][2].startswith(container.named(values=container.DOTENV_VALUES))
    assert [tool for tool, spec in container_runner.TOOLS.items() if spec.get("values")] == ["daodan-dockerfile"]
    assert not {"runs_on", "restores"} & set(container_runner.TOOLS["daodan-dockerfile"])  # no project toolchain
    project = tmp_path / "project"
    project.mkdir()
    (project / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    manifest = tmp_path / "snap" / "manifest.sqlite"
    snapshot.read_project(project, manifest)
    given = []

    def recorded(project, commands, **options):
        given.append(options.get("values", False))
        return {"state": "done", "root": "/work", "results": [{"returncode": 0, "stdout": "", "stderr": ""}] * len(
            commands)}

    with mock.patch.object(container, "run_commands", recorded), \
            mock.patch.object(container_runner, "fetched", lambda url, sha, name: Path("/host") / name):
        for tool in ("daodan-dockerfile", "renovate", "cargo"):
            container_runner.runner(manifest)([{"tool": tool, "argv": [tool], "cwd": ".", "env": {}}])
    assert given == [True, False, False]


def test_the_readers_on_the_host_never_read_a_file_daodan_never_reads(tmp_path):
    """A step that sources `./.env` does not make the host read it: the readers have no such file."""
    with context_of(tmp_path, {"ci.sh": "#!/bin/sh\n. ./.env\ndocker compose up -d db\n",
                               ".env": "#!/bin/sh\ndocker compose up -d x\n"}) as context:
        read = compose.reader(context)
        assert read(".env") is None and read("./.env") is None and "docker compose" in read("ci.sh")
        found, said = compose.started("ci.sh", read("ci.sh"), ".", read)
    assert [argv[-1] for _, argv in found] == ["db"] and not said


def test_on_the_host_the_readers_start_no_program_and_run_nothing_of_the_project(tmp_path):
    """AGENTS.md's rule: on the host Daodan reads the project's CI, its scripts and its compose files as text, and
    Compose, Renovate and its YAML library run in the container (the runner's commands). Each file here leaves a
    mark if run; with every way to start a program refused, the reading states its facts and no mark appears."""
    mark = tmp_path / "mark"
    leave = f'touch "{mark.as_posix()}"'
    files = {"package.json": json.dumps({"scripts": {"pretest": "bash scripts/ci.sh", "test": "jest"}}),
             "scripts/ci.sh": f"#!/bin/sh\n{leave}\ndocker compose up -d db\n", ".github/workflows/ci.yml": WORKFLOW}
    workflow = {"jobs": {"test": {"steps": [{"run": "bash scripts/ci.sh"}, {"run": "npm test"}]}}}
    config = {"services": {"db": {"image": "postgres:16", "healthcheck": {"test": ["CMD-SHELL", leave]},
                                  "command": ["sh", "-c", leave]}}}
    refused = mock.Mock(side_effect=AssertionError("a program started on the host"))
    with context_of(tmp_path / "p", files) as context, mock.patch.object(subprocess, "run", refused), \
            mock.patch.object(subprocess, "Popen", refused), mock.patch.object(os, "system", refused):
        context.stated = {"tests": [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"}]}
        commands = renovate.commands(context)
        report = {"repositories": {"local": {"packageFiles": {}}}}
        out = renovate.read(context, commands, [{"returncode": 0, "stdout": json.dumps(report), "stderr": ""}, {
            "returncode": 0, "stdout": f".github/workflows/ci.yml\n{json.dumps(workflow)}\n", "stderr": ""}])
        context.stated = {**context.stated, **out["facts"]}
        described = compose.commands(context)
        services = compose.read(context, described, [{"returncode": 0, "stdout": json.dumps(config), "stderr": "",
                                                      "root": "/work"}] * len(described))["facts"]["services"]
        planned = dynamic.services({"services": services}), dynamic.ci_steps(out["facts"], context.stated["tests"])
    assert {item["declared_in"] for item in out["facts"]["compose"]} == {"scripts/ci.sh"}
    assert all(item["network"] == "none" for item in [*commands, *described])  # what the container runs
    assert planned[0]["services"][0]["args"][:2] == ["--health-cmd", leave]  # the engine runs it, in the service
    assert [step["run"] for step in planned[1]["steps"]] == ["bash scripts/ci.sh"]
    assert not mark.exists() and refused.call_count == 0


def test_a_command_source_reads_what_the_sources_before_it_state(tmp_path):
    seen = {}
    first = SimpleNamespace(NAME="steps", VERSION="1", RANK="reader",
                            commands=lambda context: [{"tool": "t", "argv": ["true"], "cwd": ".", "env": {},
                                                       "network": "none"}],
                            read=lambda context, commands, results: {"facts": {"compose": [UP]}})
    later = SimpleNamespace(NAME="later", VERSION="1", RANK="model",
                            commands=lambda context: seen.update(context.stated) or None)
    with context_of(tmp_path, {"package.json": "{}\n"}) as context:
        premap.derive(context.manifest, context.store, sources=[first, later],
                      runner=lambda commands: [{"returncode": 0, "stdout": "", "stderr": "", "root": "/work"}])
    assert seen["compose"] == [{**UP, "sources": ["steps@1"]}]


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_on_modal_compose_s_own_config_gives_the_services_the_fastapi_template_s_step_starts(tmp_path):
    """Compose 5.6.1 itself (`compose.DOWNLOAD`, checked by its sha256), with no engine, on the template's files,
    its tracked `.env` with the names the pre-map's container writes in place of the values (`container.named`):
    the facts name each variable a value comes from, as interpolated and as an `env_file` gives it, and hold no
    value of the file."""
    binary = tmp_path / "bin" / "docker-compose"
    binary.parent.mkdir()
    shutil.copy(container_runner.fetched(*compose.DOWNLOAD, "docker-compose"), binary)
    binary.chmod(0o755)
    project = tmp_path / "work"
    for rel, text in {"compose.yml": COMPOSE_YML, "compose.override.yml": OVERRIDE_YML,
                      ".env": DOTENV + "HOST_FILESYSTEM=/\n",
                      "init.sql": "select 1;\n", "files.yml": "services:\n  app:\n    image: app:1\n    env_file: .env\n"
                      "    volumes:\n      - ${HOST_FILESYSTEM}:/hostfs:ro\n"}.items():  # as otel-demo's short syntax
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    subprocess.run(["sh", "-c", container.named(str(project))], check=True)
    files = {**UP, "declared_in": "files", "argv": ["docker", "compose", "-f", "files.yml", "up", "-d", "app"]}
    context = SimpleNamespace(stated={"compose": [UP, files]})
    commands = compose.commands(context)
    results = []
    for command in commands:
        said = subprocess.run([str(binary), *command["argv"][1:]], cwd=project / command["cwd"], capture_output=True,
                              text=True, timeout=120, env={"PATH": "/usr/bin:/bin", **command["env"]})
        print(said.stdout, said.stderr, flush=True)
        results.append({"returncode": said.returncode, "stdout": said.stdout, "stderr": said.stderr,
                        "root": str(project)})
    out = compose.read(context, commands, results)
    print(json.dumps(out, indent=1), flush=True)
    db, mailpit, app = out["facts"]["services"]
    assert [db, mailpit] == [{**COMPOSE_DB, "env": {"POSTGRES_DB": "app", "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}"},
                              "dotenv": {"POSTGRES_PASSWORD": ".env"}}, COMPOSE_MAILPIT] and not out.get("gaps")
    assert app["env"] == {"POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}", "DATABASE_URL": "${DATABASE_URL}",
                          "HOST_FILESYSTEM": "${HOST_FILESYSTEM}"}
    assert app["dotenv"] == {"POSTGRES_PASSWORD": ".env", "DATABASE_URL": ".env", "HOST_FILESYSTEM": ".env"}
    assert app["binds"] == ["${HOST_FILESYSTEM}:/hostfs:ro"] and "changethis" not in str(results)


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


def test_a_compose_service_starts_with_its_health_check_and_one_compose_builds_does_not():
    built = {"name": "backend", "image": "", "declared_in": STEP + ".services.backend", "host": "localhost",
             "build": "backend"}
    odd = {**COMPOSE_MAILPIT, "name": "zz", "declared_in": STEP + ".services.zz", "ignored": ["privileged", "user"],
           "after": {"db": "service_healthy"}, "binds": ["/var/run/docker.sock:/var/run/docker.sock", "../x:/x"]}
    planned = dynamic.services({"services": [COMPOSE_DB, COMPOSE_MAILPIT, built, odd]})
    assert planned["services"][0] == {
        "name": "db", "image": "postgres:18", "host": "localhost",
        "env": {"POSTGRES_DB": "app", "POSTGRES_PASSWORD": "changethis"},
        "args": ["--health-cmd", "pg_isready -U postgres -d app", "--health-interval", "10s", "--health-timeout", "10s",
                 "--health-retries", "5", "--health-start-period", "30s"], "command": [],
        "files": [["init.sql", "/docker-entrypoint-initdb.d/init.sql"]]}  # the project's file, in it before it starts
    assert [spec["name"] for spec in planned["services"]] == ["db", "mailpit", "zz"]
    assert planned["services"][2]["after"] == {"db": "service_healthy"} and "files" not in planned["services"][2]
    said = {(gap["kind"], gap["name"]): gap["detail"] for gap in planned["gaps"]}
    assert "Compose builds its image from backend" in said[("service_unavailable", "backend")]
    assert ("service_incomplete", "db") not in said
    assert "privileged, user" in said[("service_incomplete", "zz")]
    assert "/var/run/docker.sock:/var/run/docker.sock, ../x:/x" in said[("service_incomplete", "zz")]
    assert dynamic._healthcheck({"test": ["CMD", "redis-cli", "ping"], "interval": "1s"}) == [
        "--health-cmd", "redis-cli ping", "--health-interval", "1s"]
    assert dynamic._healthcheck({"disable": True}) == dynamic._healthcheck({"test": ["NONE"]}) == ["--no-healthcheck"]


def test_a_gitlab_service_starts_with_its_names_and_its_runner_s_wait_and_without_what_the_ci_computes():
    planned = dynamic.services({"services": [GITLAB_DB, GITLAB_MAILER, {**GITLAB_DB, "declared_in": ".gitlab-ci.yml#"
                                             "x.services.0", "image": "postgres:$PG", "name": "pg2", "host": "pg2"}]})
    known = {key: value for key, value in GLOBAL.items() if key != "CACHE_DIR"}
    assert planned["services"] == [  # by declaration: `e2e` before `test`
        {"name": "registry.example.com__team__mailer", "image": "registry.example.com:5000/team/mailer:2",
         "host": "registry.example.com__team__mailer", "aliases": ["registry.example.com-team-mailer"],
         "env": {"POSTGRES_DB": "app", "MAIL_PORT": "1025"}, "args": ["--entrypoint", "/bin/mailer"],
         "command": ["--fast", "serve"], "wait": "ports"},
        {"name": "db", "image": "postgres:16-alpine", "host": "db", "aliases": ["pg", "postgres"],
         "env": {**known, "NODE_ENV": "ci"}, "args": [], "command": [], "wait": "ports"}]
    assert planned["env"] == {**known, "NODE_ENV": "ci"}
    said = {(gap["kind"], gap["name"]): gap["detail"] for gap in planned["gaps"]}
    assert "the CI computes its image" in said[("service_unavailable", "pg2")]
    assert "it does not get CACHE_DIR, which the CI computes ($CI_PROJECT_DIR/.cache)" in said[("service_incomplete", "db")]
    assert "the tests do not get CACHE_DIR" in said[("service_incomplete", "db")]


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
    _asked = "ports.json" if "{{json .Config.ExposedPorts}}" in _args else "registry.json"
    print(_json.dumps(_read(_asked, {}).get(_args[-1])))
    _sys.exit(0)
if _args[:1] == ["run"] and "--rm" in _args:  # a check of a service's ports: `reach.json`, its codes in turn
    _log()
    _key = " ".join(_args[_args.index("-c") + 2:])
    _turns = _state / ("reach-" + _key.replace(" ", "-"))
    _turn = int(_turns.read_text()) if _turns.is_file() else 0
    _turns.write_text(str(_turn + 1))
    _codes = _read("reach.json", {}).get(_key, [0])
    _sys.exit(_codes[min(_turn, len(_codes) - 1)])
if _args[:2] == ["network", "disconnect"] and (_state / "no-disconnect").exists():  # as Kiri 0.2.0 answers
    _log()
    _sys.exit("Error response from daemon: Kiri cannot disconnect a container from its first network (" + _args[2] + ")")
if _args[:2] == ["start", "-a"]:
    _command = _state / "containers" / _args[-1] / "command.json"
    _command = _json.loads(_command.read_text()) if _command.is_file() else []
    if _command[:1] in (["sh"], ["python3"]):  # a shell or Python script, run for real in the container's /work
        import os as _os
        import subprocess as _subprocess
        _log()
        print("started", _args[-1], flush=True)
        if _command[:1] == ["python3"] and (_state / "no-dotenv").exists():  # the reader of .env files fails
            _sys.exit("Traceback (most recent call last):")
        _created = [_json.loads(_line) for _line in (_state / "calls.jsonl").read_text().splitlines()]
        _created = next(_c for _c in _created if _c[:1] == ["create"] and _c[_c.index("--name") + 1] == _args[-1])
        _given = dict(_created[_n + 1].split("=", 1) for _n, _a in enumerate(_created) if _a == "-e")
        _program = [_sys.executable, *_command[1:]] if _command[:1] == ["python3"] else _command
        _sys.exit(_subprocess.run(_program, cwd=_state / "containers" / _args[-1] / "fs" / "work",
                                  env={**_os.environ, **_given}).returncode)
if _args[:1] == ["create"] and _mine:
    _log()
    (_state / "containers" / _box).mkdir(parents=True)
    (_state / "containers" / _box / "image").write_text(next(_a for _a in _args if "@sha256:" in _a))
    print(_box)
    _sys.exit(0)
if _args[:1] == ["start"] and _mine:
    _log()
    _sys.exit(0)
if _args[:1] == ["inspect"] and _mine and "{{.State.ExitCode}}" in _args:  # `codes.json`, else 0
    _log()
    print(_read("codes.json", {}).get((_state / "containers" / _box / "image").read_text(), 0))
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

    def run_operation(self, services, given: dict | None = None, steps=(), **options) -> dict:
        with container.beside(services, given or {}, steps) as self.said:
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
        self.assertEqual(self.said.services, result["services"])  # what the step reads, wherever the record is

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
        self.run_operation([{**SPEC, "host": "postgres", "args": []}, {**SPEC, "name": "cache", "host": "db",
                                                                         "aliases": ["pg", "postgres"], "args": []}])
        [pod] = self.created("daodan-pod-")
        self.assertEqual([arg for arg in pod if arg.startswith("--add-host")],
                         ["--add-host=db:127.0.0.1", "--add-host=pg:127.0.0.1", "--add-host=postgres:127.0.0.1"])

    def test_a_service_of_gitlab_waits_until_the_ports_its_image_exposes_accept_a_connection(self):
        """GitLab's runner waits for the TCP ports the service's image exposes (docs.gitlab.com/ci/services): a
        check runs in the pod's namespace, from the pod's own image, until they answer."""
        waiting = {**SPEC, "args": [], "wait": "ports"}
        (self.state / "ports.json").write_text(json.dumps({PINNED: {"5432/tcp": {}, "53/udp": {}}}), encoding="utf-8")
        (self.state / "reach.json").write_text(json.dumps({"5432": [1, 1, 0]}), encoding="utf-8")
        result = self.run_operation([waiting])
        self.assertEqual(result["services"][0]["outcome"], "ready", result)
        checks = [c for c in self.calls() if c[:1] == ["run"]]
        self.assertEqual(len(checks), 3)  # the ports answer at the third
        [pod] = self.created("daodan-pod-")
        self.assertEqual(checks[0][checks[0].index("--network") + 1], f"container:{pod[pod.index('--name') + 1]}")
        self.assertIn(container.PROXY_IMAGE, checks[0])
        self.assertEqual(checks[0][-1], "5432")  # TCP only
        with mock.patch.object(container, "SERVICE_WAIT", 0):
            shutil.rmtree(self.out)
            (self.state / "reach.json").write_text(json.dumps({"5432": [1]}), encoding="utf-8")
            for turns in self.state.glob("reach-*"):
                turns.unlink()
            result = self.run_operation([waiting])
        [service] = result["services"]
        self.assertEqual(service["outcome"], "failed")
        self.assertIn("its ports 5432 accepted no connection", service["cause"])
        shutil.rmtree(self.out)
        (self.state / "calls.jsonl").unlink()
        (self.state / "ports.json").write_text(json.dumps({PINNED: None}), encoding="utf-8")
        self.assertEqual(self.run_operation([waiting])["services"][0]["outcome"], "ready")  # nothing exposed
        self.assertEqual([c for c in self.calls() if c[:1] == ["run"]], [])

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

    def order(self, states: dict, codes: dict | None = None, **after) -> dict:
        """Four services `api`, `db`, `migrate`, `web` of images `example/<name>:1`, `after` each one's."""
        pinned = {name: f"example/{name}@sha256:" + letter * 64
                  for name, letter in (("api", "b"), ("db", "c"), ("migrate", "d"), ("web", "e"))}
        self.registry({f"docker.io/example/{name}:1": [image] for name, image in pinned.items()})
        (self.state / "states.json").write_text(json.dumps({pinned[name]: turns for name, turns in states.items()}))
        (self.state / "codes.json").write_text(json.dumps({pinned[name]: code for name, code in (codes or {}).items()}))
        (self.state / "logs.json").write_text(json.dumps({pinned["db"]: "FATAL: role does not exist"}))
        result = self.run_operation([{"name": name, "image": f"example/{name}:1", "host": "localhost", "env": {},
                                      "args": [], "command": [], **({"after": after[name]} if name in after else {})}
                                     for name in sorted(pinned)])
        self.boxes = {call[call.index("--name") + 1]: call[-1].split("@")[0].split("/")[1]
                      for call in self.created("daodan-svc-")}
        return result

    def test_a_service_starts_after_those_it_depends_on_as_compose_s_condition_says(self):
        """Compose's `depends_on`: `api` is created once `db` is healthy and `migrate`, which it waits for to
        complete, has exited with code 0; `web` once `api` has started."""
        result = self.order({"db": ["running starting", "running healthy"], "migrate": ["running ", "exited "]},
                            api={"db": "service_healthy", "migrate": "service_completed_successfully"},
                            web={"api": "service_started"})
        self.assertEqual([s["outcome"] for s in result["services"]], ["ready"] * 4, result["services"])
        self.assertEqual(list(self.boxes.values()), ["db", "migrate", "api", "web"])
        calls, box = self.calls(), {name: box for box, name in self.boxes.items()}
        api = next(n for n, c in enumerate(calls) if c[0] == "create" and box["api"] in c)
        for name in ("db", "migrate"):
            last = max(n for n, c in enumerate(calls) if c[0] == "inspect" and c[-1] == box[name])
            self.assertLess(last, api, name)
        self.assertIn("{{.State.ExitCode}}", calls[last])  # migrate's last: it completed

    def test_a_service_whose_dependency_fails_does_not_start_and_its_cause_names_it(self):
        result = self.order({"db": ["running unhealthy"], "migrate": ["exited "]}, {"migrate": 3},
                            api={"db": "service_healthy"}, web={"migrate": "service_completed_successfully"})
        said = {s["name"]: (s["outcome"], s.get("cause", "")) for s in result["services"]}
        self.assertEqual(said["db"][0], "failed")
        self.assertEqual(said["api"], ("failed", "it waits for db to be healthy, which failed"))
        self.assertIn("exited with code 3", said["migrate"][1])
        self.assertEqual(said["web"], ("failed", "it waits for migrate to complete, which failed"))
        self.assertEqual(sorted(self.boxes.values()), ["db", "migrate"])  # neither of the two is created

    def test_a_service_has_the_project_s_files_its_bind_mounts_name_before_it_starts(self):
        """The service's files from the execution's copy of the project, put in it before it starts: a source the
        copy does not hold is an empty folder, as the engine makes one."""
        self.states(PINNED, "running ")
        result = self.run_operation([{**SPEC, "files": [["src/app.js", "/etc/app/app.js"], ["src", "/srv/src"],
                                                        ["data", "/var/lib/data"]]}])
        self.assertEqual([s["outcome"] for s in result["services"]], ["ready"])
        [service] = self.created("daodan-svc-")
        box = service[service.index("--name") + 1]
        fs = self.state / "containers" / box / "fs"
        self.assertEqual((fs / "etc/app/app.js").read_text(encoding="utf-8"), "module.exports = 1;\n")
        self.assertEqual((fs / "srv/src/app.js").read_text(encoding="utf-8"), "module.exports = 1;\n")
        self.assertTrue((fs / "var/lib/data").is_dir())
        self.assertEqual(list((fs / "var/lib/data").iterdir()), [])
        calls = self.calls()
        copied = calls.index(["cp", "-", f"{box}:/"])
        self.assertLess(calls.index(service), copied)
        self.assertLess(copied, calls.index(["start", box]))

    STEPS = [{"declared_in": "ci.yml#jobs.test.steps.4", "name": "Migrate", "cwd": "backend",
              "run": 'echo "migrated $NODE_ENV $DATABASE_URL CI=$CI in $(basename "$PWD")"',
              "env": {"NODE_ENV": "production"}},
             {"declared_in": "ci.yml#jobs.test.steps.5", "name": "Seed", "cwd": ".", "run": "echo broken >&2\nexit 3"},
             {"declared_in": "ci.yml#jobs.test.steps.6", "cwd": ".", "run": "echo after > after.txt", "shell": "sh"}]

    def phases(self) -> list[list[str]]:
        """The create calls of the preparation and the execution, in order."""
        return [c for c in self.created("daodan-") if re.fullmatch(r"daodan-[0-9a-f]{12}", c[c.index("--name") + 1])]

    def stepped(self) -> list[dict]:
        lines = (self.out / container.RECORD_NAME).read_text(encoding="utf-8").splitlines()
        return [row for row in map(json.loads, lines) if row["phase"] == "ci_step"]

    def test_the_ci_s_steps_run_after_the_preparation_beside_the_services_and_the_pod_leaves_its_network(self):
        """As GitHub's runner runs a job: each step before the tests in order, in its folder, with its job's and its
        own variables and CI=true, the services beside it, the registries through the proxy. A step that fails is
        said and the next one runs. Then the proxy goes and the pod leaves the preparation's network: the tests
        reach the same services, and only them."""
        (self.project / "backend").mkdir()
        (self.project / "backend" / "app.js").write_text("module.exports = 2;\n", encoding="utf-8")
        self.states(PINNED, "running healthy")
        result = self.run_operation([SPEC], {"DATABASE_URL": DATABASE_URL}, self.STEPS, prepare=["true"],
                                    timeout=120)
        self.assertEqual(result["state"], "done", result)
        calls = self.calls()
        [network] = [c[-1] for c in calls if c[:3] == ["network", "create", "--internal"]]
        [pod] = self.created("daodan-pod-")
        name = pod[pod.index("--name") + 1]
        self.assertEqual(pod[pod.index("--network") + 1], network)  # the registries' network, while it prepares
        [probe] = [c for c in self.created("daodan-probe-")]
        self.assertIn(["network", "disconnect", network, probe[probe.index("--name") + 1]], calls)
        [service] = self.created("daodan-svc-")
        [prepare, execute] = self.phases()
        self.assertEqual(prepare[prepare.index("--network") + 1], f"container:{name}")
        self.assertEqual(execute[execute.index("--network") + 1], f"container:{name}")
        self.assertLess(calls.index(["start", service[service.index("--name") + 1]]), calls.index(prepare))
        [proxy] = [c[-1] for c in calls if c[:2] == ["network", "connect"]]
        left = calls.index(["network", "disconnect", network, name])
        self.assertLess(calls.index(["rm", "-f", proxy]), left)
        self.assertLess(left, calls.index(execute))
        log = (self.out / "prepare.log").read_text(encoding="utf-8")
        self.assertIn(f"migrated production {DATABASE_URL} CI=true in backend", log)
        rows = self.stepped()
        self.assertEqual([(r["declared_in"], r["outcome"], r["exit_code"]) for r in rows],
                         [("ci.yml#jobs.test.steps.4", "exited", 0), ("ci.yml#jobs.test.steps.5", "exited", 3),
                          ("ci.yml#jobs.test.steps.6", "exited", 0)])
        self.assertTrue(all(isinstance(r["duration_seconds"], int) for r in rows))
        self.assertEqual(rows[1]["cause"], "it exited with code 3: broken")
        self.assertEqual(self.said.ci_steps, result["ci_steps"])
        self.assertEqual([s["outcome"] for s in result["ci_steps"]], ["exited"] * 3)
        [limits] = [row["limits"] for row in map(json.loads, (self.out / container.RECORD_NAME).read_text(
            encoding="utf-8").splitlines()) if row["phase"] == "prepare"]
        self.assertEqual(limits["seconds"], 1800 + 120)  # the steps within the observer's own time limit

    def test_a_step_that_does_not_end_in_the_time_left_is_stopped_and_the_next_ones_do_not_start(self):
        steps = [{"declared_in": "s.0", "cwd": ".", "run": "sleep 30"}, {"declared_in": "s.1", "cwd": ".", "run": "true"}]
        result = self.run_operation([], None, steps, prepare=["true"], timeout=2)
        self.assertEqual(result["state"], "done", result)
        first, second = result["ci_steps"]
        self.assertEqual((first["outcome"], first["exit_code"]), ("timeout", None))
        self.assertIn("did not end in the 2 s", first["cause"])
        self.assertEqual((second["outcome"], second["duration_seconds"]), ("timeout", 0))
        self.assertLess(first["duration_seconds"], 20)

    def test_a_run_without_a_preparation_runs_no_step_and_says_each(self):
        result = self.run_operation([], None, self.STEPS[2:])
        self.assertEqual(result["state"], "done", result)
        [step] = result["ci_steps"]
        self.assertEqual((step["outcome"], step["declared_in"]), ("not_run", "ci.yml#jobs.test.steps.6"))
        self.assertIn("no preparation", step["cause"])
        self.assertEqual(self.said.ci_steps, result["ci_steps"])

    def test_without_services_the_steps_run_in_the_preparation_s_own_network(self):
        result = self.run_operation([], None, self.STEPS[2:], prepare=["true"])
        self.assertEqual([s["outcome"] for s in result["ci_steps"]], ["exited"])
        calls = self.calls()
        self.assertEqual(self.created("daodan-pod-") + self.created("daodan-probe-"), [])
        self.assertFalse([c for c in calls if c[:2] == ["network", "disconnect"]])
        [prepare, _execute] = self.phases()
        self.assertTrue(prepare[prepare.index("--network") + 1].startswith("daodan-net-"))

    def test_an_engine_that_cannot_take_the_pod_off_its_network_runs_no_step_beside_the_services(self):
        """Kiri 0.2.0 refuses to disconnect a container from its first network (crates/kiri/src/daemon/
        engine.rs:2357) and to connect one on `none`: the pod cannot leave the preparation's network, so no step runs
        beside the services, each said with the engine's answer; the services start for the tests as without steps."""
        (self.state / "no-disconnect").write_text("", encoding="utf-8")
        self.states(PINNED, "running healthy")
        result = self.run_operation([SPEC], None, self.STEPS[2:], prepare=["true"])
        self.assertEqual(result["state"], "done", result)
        [step] = result["ci_steps"]
        self.assertEqual(step["outcome"], "not_run")
        self.assertIn("Kiri cannot disconnect a container from its first network", step["cause"])
        [pod] = self.created("daodan-pod-")
        self.assertEqual(pod[pod.index("--network") + 1], "none")
        [prepare, _execute] = self.phases()
        self.assertTrue(prepare[prepare.index("--network") + 1].startswith("daodan-net-"))
        self.assertEqual([s["outcome"] for s in result["services"]], ["ready"])

    def dotenv_project(self) -> Path:
        return git_project(self.scratch / "tracked", {".env": "SECRET_KEY=changethis\nPOSTGRES_PASSWORD=changethis\n",
                                                      "app.js": "module.exports = 1;\n"}, [".env", "app.js"])

    def test_a_tracked_env_file_s_values_start_the_service_and_never_reach_what_the_run_keeps(self):
        """The values are read in a container of Daodan's (`RESOLVE` in the proxy's image, with no network); the
        service starts with them in place of its names; the logs, the outputs that are text, the record and the
        result name the variable where the run printed its value."""
        self.states(PINNED, "exited ", logs="FATAL: password changethis rejected")
        spec = {**SPEC, "env": {"POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}"}, "dotenv": {"POSTGRES_PASSWORD": ".env"}}
        script = ("mkdir -p ../daodan/out && echo key $(sed -n 's/^SECRET_KEY=//p' .env) > ../daodan/out/tests-0.log"
                  " && cat .env")
        with container.beside([spec], {}) as said:
            result = container.run_in_container(self.dotenv_project(), ["sh", "-c", script], image="fake/runtime:1",
                                                out_dir=self.out, engine=self.engine, outputs=["/daodan/out"])
        reader = [call for call in self.created("daodan-dotenv-")]
        assert len(reader) == 1 and container.PROXY_IMAGE in reader[0] and reader[0][-2:] == [container.RESOLVE, ".env"]
        assert "none" == reader[0][reader[0].index("--network") + 1]
        [service] = self.created("daodan-svc-")
        assert "POSTGRES_PASSWORD=changethis" in service
        kept = "\n".join(path.read_text(encoding="utf-8") for path in self.out.rglob("*") if path.is_file())
        assert "changethis" not in kept and (self.out / "out" / "tests-0.log").is_file()
        assert "[.env:POSTGRES_PASSWORD,.env:SECRET_KEY]" in (self.out / "execute.log").read_text(encoding="utf-8")
        assert "changethis" not in json.dumps(result) and "changethis" not in json.dumps(said)
        assert result["state"] == "done" and "[.env:" in result["services"][0]["cause"]

    def test_the_variables_a_caller_names_reach_both_phases_with_their_values_and_never_what_the_run_keeps(self):
        """`dotenv_env`: a Dockerfile stage's ARG from the tracked .env is in the environment of every RUN after it,
        as BuildKit gives it: the preparation's (its `${NAME}` words) and the execution's (the stage's RUN the
        analyzer runs), which writes it into a file the test reads back with the variable in place of its value."""
        script = 'mkdir -p ../daodan/out && echo "arg=$SECRET_KEY" > ../daodan/out/arg.txt && echo "$SECRET_KEY"'
        result = container.run_in_container(self.dotenv_project(), ["sh", "-c", script], image="fake/runtime:1",
                                            out_dir=self.out, engine=self.engine, prepare=["exit", "0"],
                                            outputs=["/daodan/out"],
                                            dotenv_env=[("SECRET_KEY", ".env"), ("MISSING", ".env")])
        [prepared, executed] = [call for call in self.created("daodan-") if "fake/runtime:1" in call]
        assert "SECRET_KEY=changethis" in prepared and "SECRET_KEY=changethis" in executed
        assert not any(word.startswith("MISSING=") for call in (prepared, executed) for word in call)
        assert result["state"] == "done", result
        [arg] = [Path(path) for path in result["outputs"] if path.endswith("arg.txt")]
        masked = "[.env:POSTGRES_PASSWORD,.env:SECRET_KEY]"  # the value both variables hold
        assert arg.read_text(encoding="utf-8") == f"arg={masked}\n"
        assert masked in (self.out / "execute.log").read_text(encoding="utf-8")
        kept = "\n".join(path.read_text(encoding="utf-8") for path in self.out.rglob("*") if path.is_file())
        assert "changethis" not in kept and "changethis" not in json.dumps(result)

    def test_an_output_that_holds_a_value_after_masking_is_withheld_with_a_gap_and_off_the_record(self):
        """The execution's `-DVERSION=$SECRET_KEY` build writes its compilation database, masked as JSON, and an
        index that holds the value, which the run neither keeps, nor lists, nor puts on record: a gap names it."""
        script = ('mkdir -p ../daodan/out && printf \'[{"command": "c++ -DVERSION=%s -c a.cpp"}]\' "$SECRET_KEY" '
                  '> ../daodan/out/compile_commands.json && printf "scip\\000%s\\001" "$SECRET_KEY" '
                  '> ../daodan/out/index.scip')
        result = container.run_in_container(self.dotenv_project(), ["sh", "-c", script], image="fake/runtime:1",
                                            out_dir=self.out, engine=self.engine, outputs=["/daodan/out"],
                                            dotenv_env=[("SECRET_KEY", ".env")])
        assert result["state"] == "done", result
        assert [Path(path).name for path in result["outputs"]] == ["compile_commands.json"]
        [database] = json.loads(Path(result["outputs"][0]).read_text(encoding="utf-8"))
        assert database["command"] == "c++ -DVERSION=[.env:POSTGRES_PASSWORD,.env:SECRET_KEY] -c a.cpp"
        [gap] = [gap for gap in result["gaps"] if gap["kind"] == "output_withheld"]
        assert gap["path"].endswith("index.scip") and gap["variables"] == [".env:POSTGRES_PASSWORD", ".env:SECRET_KEY"]
        rows = [json.loads(line) for line in (self.out / container.RECORD_NAME).read_text().splitlines()]
        assert not any("index.scip" in path for row in rows for path in row.get("outputs") or ())
        assert not any(b"changethis" in path.read_bytes() for path in self.out.rglob("*") if path.is_file())

    def test_an_example_env_file_s_values_are_public_and_an_output_that_holds_them_is_kept(self):
        """hoppscotch's `.env.example` (D-291): a tracked example file's values are public, as its name says, so an
        index that holds one is kept as written and no gap names it; one that holds the value of a true `.env` is
        withheld; a value both hold stays masked, named by the true file's variable only."""
        project = git_project(self.scratch / "example", {
            ".env.example": "VITE_BASE_URL=http://localhost:3000\nSHARED=sharedsecret\n",
            ".env.local.sample": "PROXY_APP_URL=http://localhost:9159\n",
            ".env": "SECRET_KEY=changethis\nSHARED=sharedsecret\n", "app.js": "\n"},
            [".env.example", ".env.local.sample", ".env", "app.js"])
        script = ('mkdir -p ../daodan/out && printf "scip\\000%s %s\\001" "$(sed -n "s/^VITE_BASE_URL=//p" '
                  '.env.example)" "$(sed -n "s/^PROXY_APP_URL=//p" .env.local.sample)" > ../daodan/out/public.scip'
                  ' && printf "scip\\000%s\\001" "$(sed -n "s/^SECRET_KEY=//p" .env)" > ../daodan/out/secret.scip'
                  ' && echo shared $(sed -n "s/^SHARED=//p" .env.example)')
        result = container.run_in_container(project, ["sh", "-c", script], image="fake/runtime:1", out_dir=self.out,
                                            engine=self.engine, outputs=["/daodan/out"])
        assert result["state"] == "done", result
        assert [Path(path).name for path in result["outputs"]] == ["public.scip"]
        assert Path(result["outputs"][0]).read_bytes() == b"scip\x00http://localhost:3000 http://localhost:9159\x01"
        assert [(gap["path"], gap["variables"]) for gap in result["gaps"] if gap["kind"] == "output_withheld"] == [
            ("out/secret.scip", [".env:SECRET_KEY"])]
        assert "shared [.env:SHARED]" in (self.out / "execute.log").read_text(encoding="utf-8")
        assert not any(b"changethis" in path.read_bytes() or b"sharedsecret" in path.read_bytes()
                       for path in self.out.rglob("*") if path.is_file())

    def test_a_run_says_once_which_values_it_masks_only_as_whole_words_or_not_at_all(self):
        """A short value is masked where it stands whole (`DB=app` in the log, `application` as it was); the result
        says so once, as `partial` words it."""
        project = git_project(self.scratch / "short", {".env": "DB=app\nDEBUG=true\nSECRET_KEY=changethis\n",
                                                       "main.js": "\n"}, [".env", "main.js"])  # no path holds `app`
        result = container.run_in_container(project, ["sh", "-c", "cat .env && echo application"],
                                            image="fake/runtime:1", out_dir=self.out, engine=self.engine)
        assert result["state"] == "done", result
        log = (self.out / "execute.log").read_text(encoding="utf-8")
        assert "DB=[.env:DB]" in log and "application" in log and "SECRET_KEY=[.env:SECRET_KEY]" in log
        assert [(gap["kind"], gap["variables"]) for gap in result["gaps"] if gap["kind"] == "mask_partial"] == [
            ("mask_partial", [".env:DB", ".env:DEBUG"])]

    def acme_project(self) -> Path:
        """A private project's words (D-311): its `.env.dev` and `.env.prod` hold values its files' names hold;
        the API key stands in a note Git does not track, which publishes nothing."""
        return git_project(self.scratch / "acme", {
            ".env.dev": "VERTEX_LOCATION=global\nMONGODB_DATABASE=acme\nAPI_KEY=sk-live-9f31\n",
            ".env.prod": "ACME_ENV=prod\n", "react-app/src/lib/globalTheme.ts": "export {}\n",
            "references/acme.md": "# notes\n", "product.svg": "<svg/>\n", "notes.txt": "sk-live-9f31\n"},
            [".env.dev", ".env.prod", "react-app/src/lib/globalTheme.ts", "references/acme.md",
             "product.svg"])

    def test_a_value_the_project_publishes_is_no_secret_and_an_answer_listing_the_paths_is_kept(self):
        """A private project, 18 November 2026: go-enry's answer listed `globalTheme.ts` and was withheld for
        `VERTEX_LOCATION=global`. A value the project's tracked files hold, by name or by content, is its public
        text: the answer, an index and the log keep it as written, and no gap names it."""
        answer = ('[{"path": "react-app/src/lib/globalTheme.ts"}, {"path": "references/acme.md"}, '
                  '{"path": "product.svg"}]')
        script = (f"mkdir -p ../daodan/out && printf '%s' '{answer}' > ../daodan/out/stdout"
                  " && printf 'scip\\000global prod acme\\001' > ../daodan/out/index.scip && echo region global env prod")
        result = container.run_in_container(self.acme_project(), ["sh", "-c", script], image="fake/runtime:1",
                                            out_dir=self.out, engine=self.engine, outputs=["/daodan/out"])
        assert result["state"] == "done", result
        assert sorted(Path(path).name for path in result["outputs"]) == ["index.scip", "stdout"]
        assert (self.out / "out" / "stdout").read_text(encoding="utf-8") == answer
        assert (self.out / "out" / "index.scip").read_bytes() == b"scip\x00global prod acme\x01"
        assert not [gap for gap in result.get("gaps") or () if gap["kind"] in ("output_withheld", "mask_partial")]
        assert "region global env prod" in (self.out / "execute.log").read_text(encoding="utf-8")
        [reader] = self.created("daodan-dotenv-")
        assert f"DAODAN_PUBLIC={container.PUBLIC_SECONDS}" in reader

    def test_a_value_only_the_env_files_hold_is_masked_in_text_and_withholds_an_output_that_is_not(self):
        """The API key stands in no tracked file but `.env.dev`: what the run printed and a JSON answer name the
        variable in its place, and an index that holds it is withheld, the gap naming the variable."""
        script = ("mkdir -p ../daodan/out && key=$(sed -n 's/^API_KEY=//p' .env.dev) && echo \"key $key\""
                  " && printf '{\"key\": \"%s\"}' \"$key\" > ../daodan/out/answer.json"
                  " && printf 'scip\\000%s\\001' \"$key\" > ../daodan/out/index.scip")
        result = container.run_in_container(self.acme_project(), ["sh", "-c", script], image="fake/runtime:1",
                                            out_dir=self.out, engine=self.engine, outputs=["/daodan/out"])
        assert result["state"] == "done", result
        assert [Path(path).name for path in result["outputs"]] == ["answer.json"]
        assert json.loads((self.out / "out" / "answer.json").read_text(encoding="utf-8")) == {
            "key": "[.env.dev:API_KEY]"}
        assert "key [.env.dev:API_KEY]" in (self.out / "execute.log").read_text(encoding="utf-8")
        [gap] = [gap for gap in result["gaps"] if gap["kind"] == "output_withheld"]
        assert gap["path"] == "out/index.scip" and gap["variables"] == [".env.dev:API_KEY"]
        assert not any(b"sk-live-9f31" in path.read_bytes() for path in self.out.rglob("*") if path.is_file())

    def test_a_command_that_never_saw_a_value_keeps_what_it_wrote_untouched(self):
        """Over the placeholders (`named`), as a pre-map command runs (`run_commands`, `blind`): no reader starts,
        and what it wrote, text or not, is kept as written, with no mask and no gap."""
        script = (container.named(".") + "mkdir -p ../daodan/out && cat .env > ../daodan/out/stdout"
                  " && printf 'scip\\000%s\\001' \"$(cat .env)\" > ../daodan/out/index.scip && cat .env")
        result = container.run_in_container(self.dotenv_project(), ["sh", "-c", script], image="fake/runtime:1",
                                            out_dir=self.out, engine=self.engine, outputs=["/daodan/out"], blind=True)
        assert result["state"] == "done", result
        assert self.created("daodan-dotenv-") == []
        printed = (f"SECRET_KEY={placed('.env', 'SECRET_KEY')}\n"
                   f"POSTGRES_PASSWORD={placed('.env', 'POSTGRES_PASSWORD')}\n")
        assert (self.out / "out" / "stdout").read_text(encoding="utf-8") == printed
        assert (self.out / "out" / "index.scip").read_bytes() == b"scip\x00" + printed.rstrip("\n").encode() + b"\x01"
        assert sorted(Path(path).name for path in result["outputs"]) == ["index.scip", "stdout"]
        assert not result.get("gaps") and printed in (self.out / "execute.log").read_text(encoding="utf-8")
        assert not any(b"changethis" in path.read_bytes() for path in self.out.rglob("*") if path.is_file())

    def test_a_tracked_env_file_whose_values_cannot_be_read_stops_the_run_with_its_cause(self):
        (self.state / "no-dotenv").write_text("", encoding="utf-8")
        result = container.run_in_container(self.dotenv_project(), ["exit", "0"], image="fake/runtime:1",
                                            out_dir=self.out, engine=self.engine)
        assert result["state"] == "failed" and ".env" in result["cause"]
        assert not [call for call in self.calls() if call[0] == "create" and "fake/runtime:1" in call]
        assert not [call for call in self.created("daodan-dotenv-") if not [
            other for other in self.calls() if other[:2] == ["rm", "-f"] and other[-1] == call[call.index("--name") + 1]]]

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

def observer_of(seen: dict, runs: list[list[dict]], state: str = "ran", stepped: list[list[dict]] = (),
                found: list[dict] = ()):
    """A Python observer with a container run per item of `runs`, each starting the services with those outcomes
    and the CI's steps with those of `stepped` (as `container.run_in_container` does within `container.beside`),
    that keeps what it was planned and says the gaps `found`."""
    def observe(project, planned, out_dir, engine):
        services, env, steps, said = container.BESIDE.get()
        seen.update(planned, services=services, env=env, steps=steps)
        for outcomes in runs:
            said.services.extend(outcomes)
        for outcomes in stepped:
            said.ci_steps.extend(outcomes)
        return {"state": state, "sites": [], "gaps": [dict(gap) for gap in found],
                "runs": [{"root": ".", "runner": "pytest", "state": "ran"}]} \
            if state == "ran" else {"state": state, "cause": "no engine", "remedy": "start one"}
    return SimpleNamespace(NAME="dynamic-fake-python", VERSION="1", LANGUAGES=("python",),
                           external=lambda callee: {"manager": "python", "package": "x", "version": None},
                           plan=lambda record, files, read: {"runs": [{"root": ".", "runner": "pytest",
                                                                       "declared_in": "pyproject.toml"}], "gaps": []},
                           observe=observe)


def run_step(tmp_path, entries: list[dict], runs: list[list[dict]], state: str = "ran", ci_steps=(), stepped=(),
             found=()):
    _project, manifest = write_project(tmp_path, {"lib.py": SAMPLED_LIB})
    static_store(manifest)
    seen: dict = {}
    record = {"services": entries, "tests": [], "ci_steps": list(ci_steps)}
    with mock.patch.object(premap, "ensure", return_value=record), \
            mock.patch.object(dynamic, "observers", return_value=[observer_of(seen, runs, state, stepped, found)]):
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


def test_the_step_runs_the_ci_s_steps_before_each_observer_s_tests_and_says_those_that_did_not(tmp_path):
    """The steps before the tests the observer runs reach its container runs; one that failed in its runs is a
    `ci_step_failed` gap once, one that cannot run a `ci_step_not_run` gap."""
    facts = [{"declared_in": "ci.yml#jobs.test.steps.2", "tests": "pyproject.toml", "name": "Migrate", "cwd": ".",
              "run": "alembic upgrade head"},
             {"declared_in": "ci.yml#jobs.test.steps.3", "tests": "pyproject.toml", "name": "Cache",
              "cause": "it uses actions/cache@v4: Daodan runs no action"},
             {"declared_in": "ci.yml#jobs.web.steps.1", "tests": "web/package.json#scripts.test", "cwd": "web",
              "run": "npm ci"}]
    failed = [{"declared_in": "ci.yml#jobs.test.steps.2", "name": "Migrate", "outcome": "exited", "exit_code": 1,
               "duration_seconds": 3, "cause": "it exited with code 1: FATAL: no such table"}]
    unprepared = [{**failed[0], "outcome": "not_run", "exit_code": None, "duration_seconds": 0,
                   "cause": "the run has no preparation, at whose end Daodan runs the CI's steps"}]
    facts.append({"declared_in": "ci.yml#jobs.test.steps.4", "tests": "pyproject.toml", "name": "Tests", "test": True,
                  "env": {"FASTAPI_ENV": "development", "KEY": "${{ secrets.KEY }}"}})
    seen, events = run_step(tmp_path, [], [], ci_steps=facts, stepped=[failed, unprepared, failed])
    assert seen["steps"] == [{"declared_in": "ci.yml#jobs.test.steps.2", "name": "Migrate", "cwd": ".",
                              "run": "alembic upgrade head"}]
    assert seen["env"] == {"FASTAPI_ENV": "development"}  # the test step's, as the CI gives them its runner
    [unset] = gaps(events, "ci_step_incomplete")
    assert unset["path"] == "ci.yml#jobs.test.steps.4" and "KEY" in unset["detail"]
    [said] = gaps(events, "ci_step_failed")
    assert said["path"] == "ci.yml#jobs.test.steps.2" and "Migrate" in said["detail"] and "no such table" in said["detail"]
    [skipped] = gaps(events, "ci_step_not_run")
    assert skipped["path"] == "ci.yml#jobs.test.steps.3"
    assert container.BESIDE.get() is None


REFUSED = {"kind": "services_unreachable", "path": ".",
           "addresses": {"127.0.0.1:80": 11, "api.example.com:443": 2, "localhost:5432": 1, "postgres:6379": 1},
           "detail": "npm run frontend:test in .: 15 lines of its log report a refused connection or an unreachable "
                     "host (127.0.0.1:80 ×11, api.example.com:443 ×2, localhost:5432 ×1): the tests run with no "
                     "network and with only the services the project's CI declares"}


def test_a_refused_local_address_no_declared_service_answers_at_is_said_with_the_ports_they_answer_on(tmp_path):
    """Of the addresses the tests could not reach (`addresses`), the step names the local ones no service the CI
    declares answers at, beside the tests on its container's port: tududi's frontend tests, which its CI does not
    run, reach jsdom's default `http://localhost/` beside postgres on 5432, and no network would change that."""
    run = [{"name": "postgres", "image": "postgres:16-alpine", "outcome": "ready"}]
    _seen, events = run_step(tmp_path, [TUDUDI], [run], found=[REFUSED])
    [said] = gaps(events, "services_unreachable")
    assert said["detail"] == REFUSED["detail"] + (
        "; no service the project's CI declares answers at 127.0.0.1:80, postgres:6379 (postgres on 5432)")
    _seen, events = run_step(tmp_path / "none", [], [], found=[REFUSED])
    [said] = gaps(events, "services_unreachable")
    assert said["detail"].endswith("; no service the project's CI declares answers at 127.0.0.1:80, localhost:5432 "
                                   "(it declares none)")
    unported = {**TUDUDI, "ports": []}  # a port it answers on that the CI does not declare: nothing is said
    _seen, events = run_step(tmp_path / "unported", [unported], [run], found=[REFUSED])
    [said] = gaps(events, "services_unreachable")
    assert said["detail"] == REFUSED["detail"]


# ------------------------------------------------------------------ the JavaScript observer

def test_the_javascript_observer_says_a_refused_connection_without_saying_no_service_starts(tmp_path):
    from test_codebase_map_dynamic_javascript import Played, observe
    played = Played({"tests-0.log": "Error: connect ECONNREFUSED 127.0.0.1:6379\nError: getaddrinfo ENOTFOUND redis\n"
                                    "Error: connect ECONNREFUSED 127.0.0.1:6379\n"},
                    {"execute.log": "DAODAN-DYNAMIC 0 exit 1 3\n"})
    result = observe(tmp_path, played)
    [gap] = [gap for gap in result["gaps"] if gap["kind"] == "services_unreachable"]
    assert "starts no service" not in gap["detail"] and "(127.0.0.1:6379 ×2, redis ×1)" in gap["detail"]
    assert "only the services the project's CI declares" in gap["detail"]
    assert gap["addresses"] == {"127.0.0.1:6379": 2, "redis": 1}


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


SQL = r'''import json, os, socket, struct, sys, urllib.parse
url = urllib.parse.urlsplit(os.environ["DATABASE_URL"])


def read(s):
    kind, size = struct.unpack("!ci", s.recv(5, socket.MSG_WAITALL))
    return kind, s.recv(size - 4, socket.MSG_WAITALL) if size > 4 else b""


rows = []
with socket.create_connection((url.hostname, url.port), timeout=10) as s:  # a trusted session, one simple query
    body = b"user\0" + url.username.encode() + b"\0database\0" + url.path[1:].encode() + b"\0\0"
    s.sendall(struct.pack("!ii", 8 + len(body), 196608) + body)
    for query in (None, sys.argv[1].encode() + b"\0"):
        if query:
            s.sendall(b"Q" + struct.pack("!i", 4 + len(query)) + query)
        kind, data = read(s)
        while kind != b"Z":
            assert kind != b"E", data
            if kind == b"D":
                at, row = 2, []
                for _ in range(struct.unpack("!h", data[:2])[0]):
                    size = struct.unpack("!i", data[at:at + 4])[0]
                    row.append(None if size < 0 else data[at + 4:at + 4 + size].decode())
                    at += 4 + max(size, 0)
                rows.append(row)
            kind, data = read(s)
said = {"rows": rows}
if len(sys.argv) > 2:
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=5)
        said["outside"] = "reached"
    except OSError as error:
        said["outside"] = type(error).__name__
    os.makedirs(os.path.dirname(sys.argv[2]), exist_ok=True)
    with open(sys.argv[2], "w") as f:
        json.dump(said, f)
print(json.dumps(said))
'''


@contextlib.contextmanager
def the_driver():
    """The benchmark driver with a scratch folder of this test's own (`SCRATCH`), so tests that run at once (`-n`)
    share none; its volume's `commit` sends what the test wrote there, and Docker's binaries (the driver's function
    holds the volume at /results, a test does not). The folder is removed afterwards; the binaries stay, as the
    driver keeps them."""
    sys.path.insert(0, str(HERE.parent / "benchmarks/project-model"))
    import modal_pipeline
    volume, sent = modal_pipeline.volume, set()
    own = f"{modal_pipeline.SCRATCH}/test-{uuid.uuid4().hex[:12]}"
    bundle = f"{modal_pipeline.BUNDLES.lstrip('/')}/{Path(modal_pipeline.DOCKER[0]).name}"

    def commit():
        root = Path("/results")
        new = [rel for rel in (path.relative_to(root).as_posix() for path in sorted(root.rglob("*")) if path.is_file())
               if rel not in sent and (rel.startswith(own + "/") or rel == bundle)]
        if new:
            with volume.batch_upload(force=True) as batch:
                for rel in new:
                    batch.put_file(str(root / rel), "/" + rel)
            sent.update(new)

    try:
        with mock.patch.object(volume, "commit", commit), mock.patch.object(modal_pipeline, "SCRATCH", own):
            yield modal_pipeline
    finally:
        if any(rel.startswith(own + "/") for rel in sent):
            volume.remove_file("/" + own, recursive=True)


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
    assert result["state"] != "failed", result.get("cause")  # before the record, which a run that failed early has not
    rows = [json.loads(line) for line in (tmp_path / "out" / container.RECORD_NAME).read_text().splitlines()]
    print(json.dumps(rows, indent=1), flush=True)
    assert result["state"] == "done" and result["exit_code"] == 0, result.get("cause") or result
    [service] = [row for row in rows if row["phase"] == "service"]
    assert service["outcome"] == "ready" and "postgres@sha256:" in service["pinned"], service
    said = json.loads((tmp_path / "out" / "out" / "probe.json").read_text())
    print(said, flush=True)
    assert (said["host"], said["port"], said["ssl"], said["reply"]) == ("localhost", 5432, "N", "R")
    assert said["auth"] in (0, 3, 5, 10) and said.get("session", "ready") == "ready"  # trusted, or a password asked
    assert said["outside"] != "reached"


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_on_modal_the_ci_s_steps_run_beside_the_services_and_the_tests_find_what_they_wrote(tmp_path):
    """The driver's Sandboxes with a step before the tests, as tududi's CI migrates its database: the service
    starts in the preparation's sandbox, the step writes into it there, the service starts again from what it kept
    in the network-blocked execution, whose tests read what the step wrote, and nothing outside."""
    from indexers import typescript
    entry = {**TUDUDI, "env": {**TUDUDI["env"], "POSTGRES_HOST_AUTH_METHOD": "trust"}}  # SQL speaks no SCRAM
    planned = dynamic.services({"services": [entry]})
    project = tmp_path / "proj"
    project.mkdir()
    (project / "sql.py").write_text(SQL, encoding="utf-8")
    steps = [{"declared_in": "ci.yml#jobs.test.steps.4", "name": "Migrate", "cwd": ".",
              "run": 'python3 sql.py "CREATE TABLE made (id int); INSERT INTO made VALUES (7)"'}]
    with the_driver() as modal_pipeline, container.beside(planned["services"], planned["env"], steps) as said:
        result = modal_pipeline.sandbox_run(project, ["python3", "/work/sql.py", "SELECT id FROM made",
                                                      "/daodan/out/sql.json"], image=typescript.IMAGE,
                                            out_dir=tmp_path / "out", prepare=["true"], outputs=["/daodan/out"],
                                            env={"PATH": "/usr/local/bin:/usr/bin:/bin"}, timeout=600,
                                            prepare_timeout=900)
    assert result["state"] != "failed", result.get("cause")  # before the record, which a run that failed early has not
    rows = [json.loads(line) for line in (tmp_path / "out" / container.RECORD_NAME).read_text().splitlines()]
    print(json.dumps(rows, indent=1), flush=True)
    assert result["state"] == "done" and result["exit_code"] == 0, result.get("cause") or result
    [step] = result["ci_steps"]
    assert (step["outcome"], step["exit_code"]) == ("exited", 0) and said.ci_steps == result["ci_steps"]
    assert [row["outcome"] for row in rows if row["phase"] == "service"] == ["ready", "ready"]  # beside each phase
    found = json.loads((tmp_path / "out" / "out" / "sql.json").read_text())
    print(found, flush=True)
    assert found["rows"] == [["7"]] and found["outside"] != "reached"


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_on_modal_a_tracked_env_file_s_value_reaches_the_service_and_nothing_the_run_keeps(tmp_path):
    """The driver's Sandboxes over a project whose `.env` Git tracks: the value is read in a Sandbox of the proxy's
    image, the service starts with it (PostgreSQL makes the database it names), the tests find that database, and
    the logs, the text outputs, the record and the result name the variable where the tests printed its value."""
    from indexers import typescript
    secret = "s3cr3t" + uuid.uuid4().hex[:8]
    # `-h localhost`: the image's first server, the one that makes the database, answers on its socket only
    fact = {"name": "db", "image": "postgres:16-alpine", "declared_in": "ci.yml#jobs.t.steps.1.services.db",
            "host": "localhost", "env": {"POSTGRES_DB": "${DB_NAME}", "POSTGRES_HOST_AUTH_METHOD": "trust"},
            "dotenv": {"DB_NAME": ".env"}, "job_env": {"DATABASE_URL": f"postgres://postgres@localhost:5432/{secret}"},
            "healthcheck": {"test": ["CMD-SHELL", "pg_isready -h localhost -U postgres -d ${DB_NAME}"], "interval": "1s",
                            "retries": 60}}
    planned = dynamic.services({"services": [fact]})
    project = git_project(tmp_path / "proj", {".env": f"DB_NAME={secret}\n", "sql.py": SQL}, [".env", "sql.py"])
    with the_driver() as modal_pipeline, container.beside(planned["services"], planned["env"]) as said:
        result = modal_pipeline.sandbox_run(project, ["python3", "/work/sql.py", "SELECT current_database()",
                                                      "/daodan/out/sql.txt"], image=typescript.IMAGE,
                                            out_dir=tmp_path / "out", outputs=["/daodan/out"],
                                            env={"PATH": "/usr/local/bin:/usr/bin:/bin"}, timeout=600)
    kept = {path.name: path.read_text(encoding="utf-8") for path in (tmp_path / "out").rglob("*") if path.is_file()}
    print(json.dumps(kept, indent=1), flush=True)
    assert result["state"] == "done" and result["exit_code"] == 0, result.get("cause") or result
    assert [item["outcome"] for item in said.services] == ["ready"]
    assert json.loads(kept["sql.txt"])["rows"] == [["[.env:DB_NAME]"]]  # the database the value names, masked
    assert secret not in json.dumps([kept, result, said])


BUILD = r'''g++ -DVERSION="\"$VERSION\"" -c main.cpp -o /daodan/out/main.o && echo "built $VERSION" && python3 -c '
import json, os
json.dump([{"directory": "/work", "file": "main.cpp", "output": "main.o",
            "command": "g++ -DVERSION=\"\\\"%s\\\"\" -c main.cpp" % os.environ["VERSION"]}],
          open("/daodan/out/compile_commands.json", "w"))'
'''


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="runs in the Modal test container")
def test_on_modal_a_minus_d_build_keeps_its_database_masked_and_withholds_the_object_that_holds_the_value(tmp_path):
    """A real g++ build with `-DVERSION="<value>"` from the tracked .env, in the driver's Sandboxes: its log and its
    compilation database (JSON, which escapes the value's `é`) keep the variable's name; the object file, which
    holds the value's bytes, is not kept: a gap names it and the variable."""
    from indexers import clang
    secret = "clé-" + uuid.uuid4().hex[:8]
    project = git_project(tmp_path / "proj", {".env": f"VERSION={secret}\n", "main.cpp": (
        "const char *version = VERSION;\nint main() { return version[0]; }\n")}, [".env", "main.cpp"])
    with the_driver() as modal_pipeline:
        result = modal_pipeline.sandbox_run(project, ["sh", "-c", f"mkdir -p /daodan/out && {BUILD}"],
                                            image=clang.IMAGE, out_dir=tmp_path / "out",
                                            outputs=["/daodan/out"], timeout=300, dotenv_env=[("VERSION", ".env")],
                                            env={"PATH": "/usr/local/bin:/usr/bin:/bin"})
    kept = {path.name: path.read_bytes() for path in (tmp_path / "out").rglob("*") if path.is_file()}
    print(json.dumps({"result": result, "kept": sorted(kept)}, indent=1, default=str), flush=True)
    assert result["state"] == "done" and result["exit_code"] == 0, result.get("cause") or result
    [database] = json.loads(kept["compile_commands.json"])
    assert database["command"] == 'g++ -DVERSION="\\"[.env:VERSION]\\"" -c main.cpp'
    assert "main.o" not in kept and [Path(path).name for path in result["outputs"]] == ["compile_commands.json"]
    [gap] = [gap for gap in result["gaps"] if gap["kind"] == "output_withheld"]
    assert gap["path"].endswith("main.o") and gap["variables"] == [".env:VERSION"]
    assert b"built [.env:VERSION]" in b"".join(kept.values())
    assert not any(secret.encode() in data for data in kept.values()) and secret not in json.dumps(result)


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="runs in the Modal test container")
def test_on_modal_a_stage_s_arg_from_the_tracked_env_reaches_both_sandboxes_and_nothing_the_run_keeps(tmp_path):
    """The driver's `dotenv_env`, as `docker_build.run` asks it: the ARG is in the preparation's environment and in
    the execution's, whose RUN writes both into a file the test reads back with the variable in place of its
    value."""
    from indexers import typescript
    secret = "s3cr3t" + uuid.uuid4().hex[:8]
    project = git_project(tmp_path / "proj", {".env": f"VERSION={secret}\n", "app.js": "\n"}, [".env", "app.js"])
    run = 'mkdir -p /daodan/out && echo "prep=$(cat /work/prep) arg=$VERSION" > /daodan/out/arg.txt'
    with the_driver() as modal_pipeline:
        result = modal_pipeline.sandbox_run(project, ["sh", "-c", run], image=typescript.IMAGE,
                                            prepare=["sh", "-c", 'echo "$VERSION" > /work/prep'],
                                            out_dir=tmp_path / "out", outputs=["/daodan/out"], timeout=300,
                                            env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
                                            dotenv_env=[("VERSION", ".env")])
    kept = {path.name: path.read_text(encoding="utf-8") for path in (tmp_path / "out").rglob("*") if path.is_file()}
    assert result["state"] == "done" and result["exit_code"] == 0, result.get("cause") or result
    assert kept["arg.txt"] == "prep=[.env:VERSION] arg=[.env:VERSION]\n"
    assert secret not in json.dumps([kept, result])


POD = r'''import json, sys
from pathlib import Path
sys.path.insert(0, "/daodan/scripts")
import container
cases, engine = json.loads(sys.argv[1]), container.Engine("docker", (sys.argv[2] + "/docker",))
said = {}
for label, (specs, url) in cases.items():
    out = Path(f"/tmp/out-{label}")
    with container.beside(specs, {"DATABASE_URL": url}):
        result = container.run_in_container(Path("/tmp/project"), ["python3", "/work/probe.py"], engine=engine,
                                            image=container.PROXY_IMAGE, out_dir=out, outputs=["/daodan/out"],
                                            env={"PATH": "/usr/local/bin:/usr/bin:/bin"}, timeout=300)
    probe = out / "out" / "probe.json"
    said[label] = {"result": result, "probe": json.loads(probe.read_text()) if probe.is_file() else None,
                   "rows": [json.loads(line) for line in (out / container.RECORD_NAME).read_text().splitlines()]}
said["left"] = container.cli(engine, "ps", "-a", "--format", "{{.Names}}").stdout.decode().split()
print(json.dumps(said))
'''


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real proof on Modal (tests/modal_pytest.py)")
def test_on_a_real_docker_the_pod_gives_the_tests_the_service_at_localhost_and_by_name_and_nothing_outside():
    """`container.run_in_container` itself on a real engine: Docker (`modal_pipeline.DOCKER`) in a Modal VM
    Sandbox as the driver starts it. The service of tududi's CI starts in the pod (`--network container:<pod>`) and
    is awaited; the tests, in the pod too, reach it at localhost and, as a job in a container does, by its name
    (the pod's hosts); the pod has no network; no container stays. The same service declared in a GitLab job,
    with no health check, is awaited as GitLab's runner awaits it, until the port its image exposes answers. Compose's
    start in the order `depends_on` gives, the project's files in a service as its bind mounts name them."""
    import base64

    import modal
    gitlab = {"name": "db", "image": "postgres:16-alpine", "declared_in": ".gitlab-ci.yml#test.services.0",
              "host": "db", "aliases": ["postgres"], "env": TUDUDI["env"], "wait": "ports"}
    [planned] = dynamic.services({"services": [gitlab]})["services"]
    # Compose's: the health check as it writes it, the project's init.sql in the service before it starts, a
    # one-shot service that reads what it made once the database is healthy, one that starts once that completes
    migrate = {"name": "migrate", "image": "postgres:18", "declared_in": STEP + ".services.migrate",
               "host": "localhost", "env": {"PGPASSWORD": "changethis"}, "after": {"db": "service_healthy"},
               "command": ["psql", "-h", "localhost", "-U", "postgres", "-d", "app", "-v", "ON_ERROR_STOP=1", "-c",
                           "SELECT count(*) FROM made_by_the_project"]}
    idle = {"name": "idle", "image": "postgres:18", "declared_in": STEP + ".services.idle", "host": "localhost",
            "command": ["sleep", "900"], "after": {"migrate": "service_completed_successfully"}}
    composed = dynamic.services({"services": [COMPOSE_DB, migrate, idle]})["services"]
    cases = {"localhost": ([SPEC], DATABASE_URL),  # on the runner, from a job's container, from a GitLab job
             "postgres": ([{**SPEC, "host": "postgres"}], DATABASE_URL.replace("@localhost:", "@postgres:")),
             "gitlab": ([planned], DATABASE_URL.replace("@localhost:", "@db:")),
             "compose": (composed, "postgres://postgres:changethis@localhost:5432/app")}
    image = (modal.Image.debian_slim(python_version="3.13").apt_install("git")
             .add_local_dir(SCRIPTS, "/daodan/scripts", ignore=["**/__pycache__"])
             # `container` and its imports read data registers at import, from `data` beside its folder's parent
             .add_local_dir(SCRIPTS.parent / "data", "/daodan/data", ignore=["marks/**"]))
    with the_driver() as modal_pipeline:
        bundle = modal_pipeline._bundle()
        box = modal.Sandbox.create(image=image, app=modal.App.lookup("daodan-pipeline-sandboxes",
                                                                       create_if_missing=True),
                                   volumes={"/results": modal_pipeline.volume},
                                   experimental_options=modal_pipeline.VM, timeout=1200, cpu=2, memory=6144)
        try:
            modal_pipeline._daemon(box, bundle)
            for path, text in (("/tmp/project/probe.py", PROBE), ("/tmp/pod.py", POD),
                               ("/tmp/project/init.sql", "CREATE TABLE made_by_the_project (id int);\n")):
                assert box.exec("sh", "-c", f"mkdir -p {Path(path).parent.as_posix()} && echo "
                                f"{base64.b64encode(text.encode()).decode()} | base64 -d > {path}").wait() == 0
            process = box.exec("python3", "/tmp/pod.py", json.dumps(cases), modal_pipeline.ENGINE, timeout=900)
            out, err = process.stdout.read(), process.stderr.read()
            assert process.wait() == 0, err[-3000:]
        finally:
            box.terminate()
    said = json.loads(out)
    print(json.dumps(said, indent=1), flush=True)
    for label, (specs, url) in cases.items():
        result, probe, rows = said[label]["result"], said[label]["probe"], said[label]["rows"]
        assert result["state"] == "done" and result["exit_code"] == 0, result.get("cause") or result
        assert [s["outcome"] for s in result["services"]] == ["ready"] * len(specs), result
        *services, execute = rows
        for service in services:
            assert service["pinned"].startswith("postgres@sha256:"), service
            assert service["network"].startswith("container:daodan-pod-"), service
        assert execute["phase"] == "execute" and execute["network"] == services[0]["network"]
        assert (probe["host"], probe["port"], probe["session"]) == (specs[0]["host"], 5432, "ready")
        assert probe["outside"] != "reached"
    assert said["left"] == []
