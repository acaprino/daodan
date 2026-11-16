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
from premap import compose, container_runner, renovate  # noqa: E402
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


def test_renovate_reads_gitlab_s_pipeline_where_it_names_services_or_includes_files(tmp_path):
    for case, text, read in (("a", "test:\n  services: [postgres]\n", True), ("b", "include: ci/x.yml\n", True),
                             ("c", "test:\n  script: [make]\n", False)):
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
    facet's) are not; nothing after the tests is."""
    tests = [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"},
             {"root": ".", "runner": "jest", "declared_in": "package.json#scripts.frontend:test"},
             {"root": "backend", "runner": "pytest", "declared_in": "backend/pyproject.toml"}]
    files = {"package.json": json.dumps({"scripts": TUDUDI_SCRIPTS}), **FASTAPI_SCRIPTS}
    out = read_steps(tmp_path, files, tests, {".github/workflows/ci.yml": CI,
                                              ".github/workflows/test-backend.yml": BACKEND})
    assert out["facts"]["ci_steps"] == [*TUDUDI_STEPS, {
        "declared_in": ".github/workflows/test-backend.yml#jobs.test-backend.steps.5", "tests": "backend/pyproject.toml",
        "name": "Migrate DB", "cwd": "backend", "run": "uv run bash scripts/prestart.sh"}]
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
            {"name": "Tests", "run": "npm test"}]}}}
    tests = [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"}]
    files = {"package.json": json.dumps({"scripts": {"test": "jest", "lint": "eslint .", "build": "tsc"}})}
    out = read_steps(tmp_path, files, tests, {".github/workflows/unit.yml": workflow})
    path = ".github/workflows/unit.yml#jobs.unit.steps."
    facts = {item["declared_in"].removeprefix(path): item for item in out["facts"]["ci_steps"]}
    assert sorted(facts, key=int) == ["2", "3", "4", "5", "6", "7"]
    assert facts["7"] == {"declared_in": path + "7", "tests": "package.json#scripts.test", "name": "Build", "cwd": ".",
                          "run": "npm run build", "env": {"TOKEN": "x", "MODE": "ci"}, "shell": "bash"}
    for number, said in (("2", "actions/cache@v4"), ("3", "github.event_name == 'push'"),
                         ("4", "${{ secrets.NPM_TOKEN }}"), ("5", "pwsh"), ("6", "docker compose exec")):
        assert said in facts[number]["cause"] and "run" not in facts[number], (number, facts[number])
    assert facts["3"]["name"] == "Seed"


def test_an_observer_s_runs_get_the_steps_before_their_tests_and_a_gap_for_each_that_does_not_run():
    """The steps before the tests an observer runs (`declared_in` of its runs), once each, in the job's order;
    a `ci_step_not_run` gap for one with a `cause`."""
    def fact(number: int, tests: str, **more) -> dict:
        return {"declared_in": f"ci.yml#jobs.t.steps.{number}", "tests": tests, "cwd": ".", "run": f"echo {number}",
                **more}
    record = {"ci_steps": [fact(10, "a"), fact(2, "a"), fact(2, "b"), fact(3, "c"),
                           {"declared_in": "ci.yml#jobs.t.steps.4", "tests": "b", "name": "Cache",
                            "cause": "it uses actions/cache@v4: Daodan runs no action"}]}
    planned = dynamic.ci_steps(record, [{"root": ".", "runner": "jest", "declared_in": "a"},
                                        {"root": ".", "runner": "jest", "declared_in": "b"}])
    assert [step["run"] for step in planned["steps"]] == ["echo 2", "echo 10"]
    assert planned["steps"][0] == {"declared_in": "ci.yml#jobs.t.steps.2", "cwd": ".", "run": "echo 2"}
    [gap] = planned["gaps"]
    assert (gap["kind"], gap["path"]) == ("ci_step_not_run", "ci.yml#jobs.t.steps.4")
    assert "Cache" in gap["detail"] and "actions/cache@v4" in gap["detail"]
    assert dynamic.ci_steps({}, [{"root": ".", "runner": "go"}]) == {"steps": [], "gaps": []}


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
    """Compose 5.6.1 itself (`compose.DOWNLOAD`, checked by its sha256), with no engine, on the template's files."""
    binary = tmp_path / "bin" / "docker-compose"
    binary.parent.mkdir()
    shutil.copy(container_runner.fetched(*compose.DOWNLOAD, "docker-compose"), binary)
    binary.chmod(0o755)
    project = tmp_path / "work"
    for rel, text in {"compose.yml": COMPOSE_YML, "compose.override.yml": OVERRIDE_YML, ".env": DOTENV,
                      "init.sql": "select 1;\n"}.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    context = SimpleNamespace(stated={"compose": [UP]})
    commands = compose.commands(context)
    results = []
    for command in commands:
        said = subprocess.run([str(binary), *command["argv"][1:]], cwd=project / command["cwd"], capture_output=True,
                              text=True, timeout=120, env={"PATH": "/usr/bin:/bin", **command["env"]})
        results.append({"returncode": said.returncode, "stdout": said.stdout, "stderr": said.stderr,
                        "root": str(project)})
    out = compose.read(context, commands, results)
    print(json.dumps(out, indent=1), flush=True)
    assert out["facts"]["services"] == [COMPOSE_DB, COMPOSE_MAILPIT] and not out.get("gaps")


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
    if _command[:1] == ["sh"]:  # a shell script, run by a real shell in the container's /work, with its variables
        import os as _os
        import subprocess as _subprocess
        _log()
        print("started", _args[-1], flush=True)
        _created = [_json.loads(_line) for _line in (_state / "calls.jsonl").read_text().splitlines()]
        _created = next(_c for _c in _created if _c[:1] == ["create"] and _c[_c.index("--name") + 1] == _args[-1])
        _given = dict(_created[_n + 1].split("=", 1) for _n, _a in enumerate(_created) if _a == "-e")
        _sys.exit(_subprocess.run(_command, cwd=_state / "containers" / _args[-1] / "fs" / "work",
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

def observer_of(seen: dict, runs: list[list[dict]], state: str = "ran", stepped: list[list[dict]] = ()):
    """A Python observer with a container run per item of `runs`, each starting the services with those outcomes
    and the CI's steps with those of `stepped` (as `container.run_in_container` does within `container.beside`),
    that keeps what it was planned."""
    def observe(project, planned, out_dir, engine):
        services, env, steps, said = container.BESIDE.get()
        seen.update(planned, services=services, env=env, steps=steps)
        for outcomes in runs:
            said.services.extend(outcomes)
        for outcomes in stepped:
            said.ci_steps.extend(outcomes)
        return {"state": state, "sites": [], "gaps": [], "runs": [{"root": ".", "runner": "pytest", "state": "ran"}]} \
            if state == "ran" else {"state": state, "cause": "no engine", "remedy": "start one"}
    return SimpleNamespace(ENTRY="dynamic-fake-python", VERSION="1", LANGUAGES=("python",),
                           external=lambda callee: {"manager": "python", "package": "x", "version": None},
                           plan=lambda record, files, read: {"runs": [{"root": ".", "runner": "pytest",
                                                                       "declared_in": "pyproject.toml"}], "gaps": []},
                           observe=observe)


def run_step(tmp_path, entries: list[dict], runs: list[list[dict]], state: str = "ran", ci_steps=(), stepped=()):
    _project, manifest = write_project(tmp_path, {"lib.py": SAMPLED_LIB})
    static_store(manifest)
    seen: dict = {}
    record = {"services": entries, "tests": [], "ci_steps": list(ci_steps)}
    with mock.patch.object(premap, "ensure", return_value=record), \
            mock.patch.object(dynamic, "observers", return_value=[observer_of(seen, runs, state, stepped)]):
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
    seen, events = run_step(tmp_path, [], [], ci_steps=facts, stepped=[failed, failed])
    assert seen["steps"] == [{"declared_in": "ci.yml#jobs.test.steps.2", "name": "Migrate", "cwd": ".",
                              "run": "alembic upgrade head"}]
    [said] = gaps(events, "ci_step_failed")
    assert said["path"] == "ci.yml#jobs.test.steps.2" and "Migrate" in said["detail"] and "no such table" in said["detail"]
    [skipped] = gaps(events, "ci_step_not_run")
    assert skipped["path"] == "ci.yml#jobs.test.steps.3"
    assert container.BESIDE.get() is None


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
    rows = [json.loads(line) for line in (tmp_path / "out" / container.RECORD_NAME).read_text().splitlines()]
    print(json.dumps(rows, indent=1), flush=True)
    assert result["state"] == "done" and result["exit_code"] == 0, result
    [step] = result["ci_steps"]
    assert (step["outcome"], step["exit_code"]) == ("exited", 0) and said.ci_steps == result["ci_steps"]
    assert [row["outcome"] for row in rows if row["phase"] == "service"] == ["ready", "ready"]  # beside each phase
    found = json.loads((tmp_path / "out" / "out" / "sql.json").read_text())
    print(found, flush=True)
    assert found["rows"] == [["7"]] and found["outside"] != "reached"


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
             .add_local_dir(SCRIPTS, "/daodan/scripts", ignore=["**/__pycache__"]))
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
        assert result["state"] == "done" and result["exit_code"] == 0, result
        assert [s["outcome"] for s in result["services"]] == ["ready"] * len(specs), result
        *services, execute = rows
        for service in services:
            assert service["pinned"].startswith("postgres@sha256:"), service
            assert service["network"].startswith("container:daodan-pod-"), service
        assert execute["phase"] == "execute" and execute["network"] == services[0]["network"]
        assert (probe["host"], probe["port"], probe["session"]) == (specs[0]["host"], 5432, "ready")
        assert probe["outside"] != "reached"
    assert said["left"] == []
