"""The translation between the pre-map's facts and stack-analyser (declarations in, evidence out) and the measures the
benchmark `modal_stack_fork.py` takes with it: the comparison, the fast scan, the totals.

No test starts Node, reaches the network or runs Modal: `stack_analyser.run` is replaced in every one.

    python -B -m pytest -q -p no:cacheprovider benchmarks/project-model/test_fork_stack.py
"""
from __future__ import annotations

import ast
import contextlib
import json
import os
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

PAYLOAD = HERE / "fixtures-fork/py-fastapi-compose.payload.json"


def fact(ecosystem, name, declared_in=None, *sources, version=None):
    return {"ecosystem": ecosystem, "name": name, "declared_in": declared_in, "sources": list(sources),
            **({"version": version} if version else {})}


def evidence(tech, kind, value, path, source="stack-analyser", **more):
    return {"tech": tech, "kind": kind, "value": value, "path": path, "source": source, **more}


def component(*items, childs=()):
    return {"name": "main", "path": ["/"], "tech": None, "techs": [], "childs": list(childs), "evidence": list(items)}


def registry(*entries):
    return {"entries": list(entries)}


REDIS = {"id": "redis", "name": "Redis", "kind": "service", "type": "database", "site": "https://redis.io/",
         "mark": "marks/redis.svg", "signs": {}}
PYTHON = {"id": "python", "name": "Python", "kind": "project", "category": "tool", "type": "altro",
          "site": "https://www.python.org", "mark": "marks/python.svg", "signs": {}}
STRIPE = {"id": "stripe", "name": "Stripe", "kind": "service", "type": "gateway", "site": "https://stripe.com",
          "mark": None, "signs": {"hosts": ["api.stripe.com"]}}


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


# ---------------------------------------------------------------------------------------------- declarations

def test_each_source_of_a_package_fact_is_one_declaration():
    facts = {"packages": [{"ecosystem": "pypi", "name": "fastapi", "version": "0.115", "declared_in": "api/requirements.txt#L3",
                           "sources": ["requirements@2", "renovate@41"]}]}
    sent, gaps = fork_stack.declarations(facts)
    assert sent == [{"type": "python", "name": "fastapi", "version": "0.115", "path": "api/requirements.txt", "line": 3, "source": s}
                    for s in ("requirements@2", "renovate@41")] and gaps == []


def test_a_fact_without_version_or_line_sends_neither():
    sent, gaps = fork_stack.declarations({"packages": [fact("npm", "react", "web/package.json", "npm@1")]})
    assert sent == [{"type": "npm", "name": "react", "path": "web/package.json", "source": "npm@1"}] and gaps == []


def test_the_ecosystems_of_the_premap_are_the_registry_s_inverse_and_the_others_pass_as_they_are():
    ecosystems = ("pypi", "crates", "go", "rubygems", "composer", "github-actions", "terraform", "terraform-resource",
                  "npm", "deno", "maven", "nuget", "hex", "pub", "swiftpm")
    sent, gaps = fork_stack.declarations({"packages": [fact(e, "x", "m.file", "s@1") for e in ecosystems]})
    assert [d["type"] for d in sent] == ["python", "rust", "golang", "ruby", "php", "githubAction", "terraform",
                                         "terraform.resource", "npm", "deno", "maven", "nuget", "hex", "pub", "swiftpm"]
    assert gaps == [] and {d["type"] for d in sent} <= set(fork_stack.TYPES)


def test_the_types_are_the_ones_the_release_accepts():
    assert fork_stack.TYPES == ("deno", "docker", "githubAction", "golang", "hex", "maven", "npm", "nuget", "php", "pub",
                                "python", "ruby", "rust", "swiftpm", "terraform", "terraform.resource")


def test_images_of_services_and_docker_stages_are_docker_declarations():
    facts = {"services": [
        {"name": "db", "image": "postgres:16", "declared_in": "docker-compose.yml.services.db", "sources": ["compose@3"]},
        {"name": "db2", "image": "postgres:15", "declared_in": "docker-compose.yml.services.db2", "sources": ["compose@3"]},
        {"name": "api", "build": ".", "declared_in": "docker-compose.yml.services.api", "sources": ["compose@3"]},
        {"name": "cache", "image": "redis:7-alpine", "declared_in": ".github/workflows/ci.yml#jobs.test.services.cache",
         "sources": ["renovate@41"]}],
        "docker_builds": [{"dockerfile": "api/Dockerfile", "context": "api", "sources": ["buildkit@v0.34", "dockerfile@1"],
                           "stages": [{"base": "python:3.12-slim", "line": 1}, {"base": "scratch", "line": 8},
                                      {"base": "python:3.12-slim", "line": 12}]}]}
    sent, gaps = fork_stack.declarations(facts)
    assert sent == [
        {"type": "docker", "name": "postgres", "path": "docker-compose.yml", "source": "compose@3"},
        {"type": "docker", "name": "redis", "path": ".github/workflows/ci.yml", "source": "renovate@41"},
        {"type": "docker", "name": "python", "path": "api/Dockerfile", "line": 1, "source": "buildkit@v0.34"},
        {"type": "docker", "name": "python", "path": "api/Dockerfile", "line": 1, "source": "dockerfile@1"}]
    assert gaps == []  # one image per file as in `step1_packages`; no `scratch`, no service without an image


def test_the_rows_are_those_of_step1_packages(manifest):
    """`_rows` repeats `step1_packages` to keep each fact's `sources`: the two must agree on what a fact is."""
    facts = {"packages": [fact("pypi", "flask", "api/requirements.txt#L3", "requirements@2"),
                          fact("npm", "left-pad", None, "npm@1"),
                          fact("docker", "postgres", "docker-compose.yml", "compose@3")],
             "services": [
                 {"name": "db", "image": "postgres:16", "declared_in": "docker-compose.yml.services.db", "sources": ["c@3"]},
                 {"name": "cache", "image": "redis:7", "declared_in": "docker-compose.yml.services.cache", "sources": ["c@3"]},
                 {"name": "ci", "image": "redis:7", "declared_in": ".github/workflows/ci.yml#jobs.t.services.ci", "sources": ["r@41"]},
                 {"name": "api", "build": ".", "declared_in": "docker-compose.yml.services.api", "sources": ["c@3"]}],
             "docker_builds": [{"dockerfile": "api/Dockerfile", "sources": ["buildkit@v0.34"], "stages": [
                 {"base": "node:20", "line": 1}, {"base": "scratch", "line": 5}, {"base": "node:20", "line": 9},
                 {"base": "nginx:1", "line": 12}]}]}
    ours = [(eco, name, path, line) for eco, name, _, path, line, _ in fork_stack._rows(facts)]
    assert ours == [(eco, name, path, line) for eco, name, path, line, _ in service_registry.step1_packages(manifest, facts)]
    assert len(ours) == 7  # the sample is not empty of what it tests


def test_an_image_the_packages_already_state_is_not_sent_twice():
    facts = {"packages": [fact("docker", "postgres", "docker-compose.yml", "compose@3")],
             "services": [{"name": "db", "image": "postgres:16", "declared_in": "docker-compose.yml.services.db",
                           "sources": ["renovate@41"]}]}
    sent, _ = fork_stack.declarations(facts)
    assert [(d["name"], d["source"]) for d in sent] == [("postgres", "compose@3")]


def not_sent(value, path, ecosystem, detail):
    return {"kind": "declaration_not_sent", "value": value, "path": path, "ecosystem": ecosystem, "detail": detail}


def test_a_declaration_the_fork_cannot_take_is_a_gap_not_a_failure():
    """The tool exits with an error for one such declaration, and so loses the whole answer for the project."""
    outside = "its path is outside the project"
    facts = {"packages": [fact("conan", "zlib", "conanfile.txt#L2", "conan@1"),
                          fact("pypi", "flask", None, "requirements@2"),
                          fact("npm", "left-pad", "vendor/web/package.json#L5", "npm@1"),
                          fact("npm", "up", "sub/../../x/package.json#L1", "npm@1"),
                          fact("npm", "drive", "C:/abs/package.json", "npm@1"),
                          fact("npm", "relative", "C:x/package.json", "npm@1"),  # on a drive, not in the project
                          fact("npm", "back", "..\\x\\package.json", "npm@1")],
             "docker_builds": [  # Compose's `build.dockerfile` normalised by the pre-map can leave the project
                 {"dockerfile": "../x/Dockerfile", "sources": ["buildkit@v0.34"], "stages": [{"base": "python:3.12", "line": 1}]},
                 {"dockerfile": "/abs/Dockerfile", "sources": ["buildkit@v0.34"], "stages": [{"base": "node:20", "line": 1}]}],
             "excluded": [{"path": "vendor/", "why": "submodule"}]}
    sent, gaps = fork_stack.declarations(facts)
    assert sent == []
    assert gaps == [
        not_sent("zlib", "conanfile.txt", "conan", "the release takes no declaration of type conan"),
        not_sent("flask", None, "pypi", "the pre-map names no file for it"),
        not_sent("left-pad", "vendor/web/package.json", "npm", "the pre-map leaves out its path"),
        not_sent("up", "sub/../../x/package.json", "npm", outside),
        not_sent("drive", "C:/abs/package.json", "npm", outside),
        not_sent("relative", "C:x/package.json", "npm", outside),
        not_sent("back", "..\\x\\package.json", "npm", outside),
        not_sent("python", "../x/Dockerfile", "docker", outside),
        not_sent("node", "/abs/Dockerfile", "docker", outside)]


def test_a_path_the_tool_reads_as_inside_the_project_is_sent():
    """`a/../b` stays in the project, and `a..b` is a name; a backslash is a separator."""
    paths = ["a/../b/package.json", "a..b/package.json", "..b/package.json", "./c/package.json", "d\\e\\package.json"]
    sent, gaps = fork_stack.declarations({"packages": [fact("npm", f"p{i}", path, "npm@1") for i, path in enumerate(paths)]})
    assert [d["path"] for d in sent] == paths and gaps == []


def test_a_fact_no_source_states_is_a_gap():
    facts = {"packages": [{"ecosystem": "npm", "name": "x", "declared_in": "package.json"},
                          {"ecosystem": "npm", "name": "y", "declared_in": "package.json#L2", "sources": []},
                          fact("npm", "z", "package.json#L3", "npm@1")]}
    sent, gaps = fork_stack.declarations(facts)
    assert [d["name"] for d in sent] == ["z"]
    assert gaps == [not_sent("x", "package.json", "npm", "no source states it"),
                    not_sent("y", "package.json", "npm", "no source states it")]


def test_a_fact_without_a_name_is_a_gap():
    sent, gaps = fork_stack.declarations({"packages": [fact("npm", "", "package.json#L2", "npm@1")]})
    assert sent == [] and gaps == [not_sent("", "package.json", "npm", "the pre-map names no package for it")]


# ---------------------------------------------------------------------------------------------- perimeter

def test_the_perimeter_skips_by_name_what_never_holds_a_snapshot_file(tmp_path, monkeypatch):
    for rel in ("web/node_modules/x.js", "api/node_modules/y.js", ".git/config", "web/src/a.ts", "gen/out.ts",
                "web/gen/keep.ts"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x", encoding="utf-8")
    files = ["web/src/a.ts", "web/gen/keep.ts"]
    listed = []
    real = os.scandir
    monkeypatch.setattr(os, "scandir", lambda path: listed.append(Path(path)) or real(path))
    # `api` holds no snapshot file and no live folder has that name: it is skipped by name, and never entered;
    # `gen` at the root holds none either but `web/gen` is live: only that path is left out
    assert fork_stack.perimeter(tmp_path, files, ("third_party",)) == ((".git", "api", "node_modules"),
                                                                       ("gen", "third_party"))
    assert sorted(p.relative_to(tmp_path).as_posix() for p in listed) == [".", "web", "web/gen", "web/src"]


def test_a_name_or_path_with_a_comma_is_left_out_of_both_lists(tmp_path):
    """The tool splits its options at commas: `a,b` would become `a` and `b`, and skip the live folder `a`."""
    for rel in ("a/x.py", "a/gen/k.py", "a,b/y.py", "c,d/keep.py", "c,d/gen/o.py", "node_modules/z.js"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x", encoding="utf-8")
    files = ["a/x.py", "a/gen/k.py", "c,d/keep.py"]
    # `a,b` is skipped by name, `c,d/gen` goes by path (`gen` is live under `a`), `x,y` is left out by the pre-map:
    # each has a comma. The tool enters them; what it finds outside the snapshot is dropped with the evidence.
    assert fork_stack.perimeter(tmp_path, files, ("x,y",)) == (("node_modules",), ())


def test_a_folder_that_cannot_be_listed_leaves_the_perimeter_to_the_fork(tmp_path):
    assert fork_stack.perimeter(tmp_path / "gone", ["web/a.ts"], ("third_party",)) == ((), ("third_party",))


class Listed:
    """What `os.scandir` gives for a folder (`is_dir`), a symbolic link or a junction."""

    def __init__(self, name, what="dir"):
        self.name, self.what = name, what

    def is_dir(self, follow_symlinks=True):
        return self.what in ("dir", "junction") or (follow_symlinks and self.what == "symlink")

    def is_symlink(self):
        return self.what == "symlink"

    def is_junction(self):
        return self.what == "junction"


def test_the_perimeter_never_follows_a_symbolic_link_or_a_junction(tmp_path, monkeypatch):
    listing, entered = {tmp_path: [Listed("real"), Listed("other"), Listed("sym", "symlink"), Listed("junc", "junction")],
                        tmp_path / "real": []}, []

    def scandir(path):
        entered.append(Path(path))
        return contextlib.nullcontext(listing[Path(path)])

    monkeypatch.setattr(os, "scandir", scandir)
    files = ["real/a.py", "sym/b.py", "junc/c.py"]  # the snapshot names a file under each, even under the links
    assert fork_stack.perimeter(tmp_path, files, ()) == (("other",), ("junc", "sym"))
    assert sorted(entered) == [tmp_path, tmp_path / "real"]


# ---------------------------------------------------------------------------------------------- evidence out

def test_evidence_is_collected_from_every_component_once():
    same = evidence("redis", "package", "redis", "/pyproject.toml", line=7)
    deep = component(evidence("redis", "image", "redis", "/docker-compose.yml"))
    payload = component(same, childs=[component(dict(same), childs=[deep]), component(evidence("redis", "file", "x", "/x"))])
    out, gaps = fork_stack.found(payload, registry(REDIS), {"pyproject.toml", "docker-compose.yml", "x"}, ())
    assert gaps == []
    assert [(s["sign"], s["value"], s["path"], s["line"]) for s in out[0]["signs"]] == [
        ("file", "x", "x", None), ("image", "redis", "docker-compose.yml", None), ("package", "redis", "pyproject.toml", 7)]


def test_the_same_evidence_from_two_sources_stays_two_signs():
    out, _ = fork_stack.found(component(evidence("redis", "package", "redis", "/a.toml", "stack-analyser"),
                                        evidence("redis", "package", "redis", "/a.toml", "other")),
                              registry(REDIS), {"a.toml"}, ())
    assert [s["source"] for s in out[0]["signs"]] == ["stack-analyser", "other"]


def test_evidence_outside_the_snapshot_or_excluded_is_dropped():
    payload = component(evidence("redis", "package", "redis", "/pyproject.toml"),
                        evidence("redis", "package", "redis", "/missing.toml"),
                        evidence("redis", "package", "redis", "/vendor/web/package.json"))
    out, gaps = fork_stack.found(payload, registry(REDIS), {"pyproject.toml", "vendor/web/package.json"}, ("vendor",))
    assert [s["path"] for s in out[0]["signs"]] == ["pyproject.toml"] and gaps == []


def test_extension_evidence_alone_recognizes_nothing():
    payload = component(evidence("python", "extension", ".py", "/app/main.py"))
    assert fork_stack.found(payload, registry(), {"app/main.py"}, ()) == ([], [])  # not even a gap: no entry comes out


def test_evidence_without_a_technology_is_one_gap_with_its_count():
    nameless = evidence(None, "package", "x", "/a.toml")
    payload = component(nameless, {"kind": "file", "value": "y", "path": "/a.toml", "source": "stack-analyser"},
                        childs=[component(dict(nameless))])
    assert fork_stack.found(payload, registry(), {"a.toml"}, ()) == (
        [], [{"kind": "evidence_without_technology", "count": 2}])


def test_an_environment_variable_is_a_mention(tmp_path, monkeypatch):
    manifest = snapshot_of(tmp_path, {"api/pay.py": "import os\nKEY = os.environ['REDIS_URL']\n"})
    payload = component(evidence("redis", "env", "REDIS_URL", "/api/pay.py", line=2))
    monkeypatch.setattr(stack_analyser, "run", lambda *args, **kwargs: payload)
    monkeypatch.setattr(service_registry, "run", fork_stack.recognize)  # the benchmark's substitution
    record = technologies.derive(manifest, registry(REDIS), {"packages": [], "excluded": []})
    assert record["technologies"] == []
    assert [(e["id"], [(s["sign"], s["strength"]) for s in e["signs"]]) for e in record["mentioned"]] == [
        ("redis", [("env", "mentioned")])]
    assert "source" not in record["mentioned"][0]


def test_an_id_the_registry_lacks_still_comes_out_with_a_gap():
    out, gaps = fork_stack.found(component(evidence("setuptools", "package", "setuptools", "/pyproject.toml")),
                                 registry(REDIS), {"pyproject.toml"}, ())
    assert out == [{"id": "setuptools", "name": "setuptools", "kind": "project", "category": "framework", "type": None,
                    "site": None, "mark": None, "source": "registry",
                    "signs": [{"sign": "package", "value": "setuptools", "path": "pyproject.toml", "line": None,
                               "strength": "declared", "source": "stack-analyser"}]}]
    assert gaps == [{"kind": "not_in_registry", "entry": "setuptools"}]


def test_an_entry_takes_its_fields_from_the_registry_and_comes_in_the_order_of_its_id():
    items = [evidence(t, "file", "f", "/f") for t in ("redis", "python")]
    out, gaps = fork_stack.found(component(*items), registry(REDIS, PYTHON), {"f"}, ())
    assert [(e["id"], e["name"], e["kind"], e["category"], e["type"], e["site"], e["mark"], e["source"]) for e in out] == [
        ("python", "Python", "project", "tool", "altro", "https://www.python.org", "marks/python.svg", "registry"),
        ("redis", "Redis", "service", "service", "database", "https://redis.io/", "marks/redis.svg", "registry")]
    assert gaps == []


def test_the_signs_of_an_entry_are_ordered_as_service_registry_orders_them():
    items = [evidence("redis", "package", "redis", "/b.toml", line=2), evidence("redis", "package", "aioredis", "/b.toml", line=2),
             evidence("redis", "package", "redis", "/a.toml"), evidence("redis", "env", "REDIS_URL", "/z.py", line=1),
             evidence("redis", "package", "redis", "/b.toml", line=1)]
    out, _ = fork_stack.found(component(*items), registry(REDIS), {"a.toml", "b.toml", "z.py"}, ())
    assert [(s["sign"], s["path"], s["line"], s["value"]) for s in out[0]["signs"]] == [
        ("env", "z.py", 1, "REDIS_URL"), ("package", "a.toml", None, "redis"), ("package", "b.toml", 1, "redis"),
        ("package", "b.toml", 2, "aioredis"), ("package", "b.toml", 2, "redis")]


def test_every_sign_carries_its_source_and_its_strength():
    items = [evidence("redis", "env", "REDIS_URL", "/a.py", "stack-analyser", line=1),
             evidence("redis", "image", "redis", "/c.yml", "daodan-compose")]
    out, _ = fork_stack.found(component(*items), registry(REDIS), {"a.py", "c.yml"}, ())
    assert [(s["sign"], s["strength"], s["source"]) for s in out[0]["signs"]] == [
        ("env", "mentioned", "stack-analyser"), ("image", "declared", "daodan-compose")]


def test_the_recorded_payload_gives_the_expected_technologies():
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    files = {"docker-compose.yml", "Dockerfile", "pyproject.toml", "app/__init__.py", "app/main.py"}
    out, gaps = fork_stack.found(payload, service_registry.load(), files, ())
    assert {e["id"] for e in out} == {"docker", "fastapi", "postgresql", "python", "redis", "setuptools", "sqlalchemy"}
    assert gaps == [{"kind": "not_in_registry", "entry": "setuptools"}]
    by_id = {e["id"]: e for e in out}
    assert [(s["sign"], s["path"]) for s in by_id["python"]["signs"]] == [("image", "Dockerfile")]  # `.py` proves nothing
    assert [(s["sign"], s["path"]) for s in by_id["redis"]["signs"]] == [("image", "docker-compose.yml"),
                                                                         ("package", "pyproject.toml")]
    assert (by_id["redis"]["kind"], by_id["fastapi"]["kind"]) == ("service", "project")


# ---------------------------------------------------------------------------------------------- recognize

FILES = {"api/pay.py": 'import requests\nURL = "https://api.stripe.com/v1/charges"\n',
         "api/requirements.txt": "redis==5.0\n", "api/gen/out.py": "X = 1\n", "Dockerfile": "FROM python:3.12-slim\n",
         ".gitignore": "node_modules/\n"}
FACTS = {"packages": [fact("pypi", "redis", "api/requirements.txt#L1", "requirements@2", version="==5.0")],
         "excluded": [{"path": "api/gen/", "why": "generated"}]}
REGISTRY = registry(REDIS, PYTHON, STRIPE)
FORK = component(evidence("redis", "package", "redis", "/api/requirements.txt", line=1),
                 evidence("python", "image", "python", "/Dockerfile"), evidence("python", "extension", ".py", "/api"),
                 evidence("redis", "package", "redis", "/api/node_modules/x.js"))


@pytest.fixture(scope="module")
def manifest(tmp_path_factory):
    """The snapshot of FILES; `node_modules` is on the disk and in the `.gitignore`, never in the snapshot."""
    work = tmp_path_factory.mktemp("fork-stack")
    (work / "app/api/node_modules").mkdir(parents=True)
    (work / "app/api/node_modules/x.js").write_text("var a = 1;\n", encoding="utf-8")
    return snapshot_of(work, FILES)


@pytest.fixture
def started(monkeypatch):
    calls = []

    def run(project, **kwargs):
        calls.append((Path(project), kwargs))
        return FORK

    monkeypatch.setattr(stack_analyser, "run", run)
    return calls


def test_recognize_sends_declarations_and_perimeter_and_answers_in_the_shape_of_service_registry_run(manifest, started):
    answer = fork_stack.recognize(manifest, REGISTRY, FACTS)
    [(project, kwargs)] = started
    assert project.resolve() == (manifest.parents[1] / "app").resolve()
    assert kwargs == {"declarations": [{"type": "python", "name": "redis", "version": "==5.0", "path": "api/requirements.txt",
                                        "line": 1, "source": "requirements@2"}],
                      "skip_dirs": (".git", "gen", "node_modules"), "ignore": ("api/gen",)}
    assert list(answer) == ["found", "checkers", "gaps"] and answer["gaps"] == []
    assert answer["checkers"] == [{"checker": "stack-analyser", "state": "ran"}, {"checker": "host", "state": "ran"}]
    assert [e["id"] for e in answer["found"]] == ["python", "redis", "stripe"]
    by_id = {e["id"]: e for e in answer["found"]}
    assert by_id["redis"]["signs"] == [{"sign": "package", "value": "redis", "path": "api/requirements.txt", "line": 1,
                                        "strength": "declared", "source": "stack-analyser"}]
    assert by_id["stripe"]["signs"] == [{"sign": "host", "value": "api.stripe.com", "path": "api/pay.py", "line": 2,
                                         "strength": "mentioned", "source": "registry_hosts"}]
    assert by_id["stripe"]["kind"] == "service"


def test_a_fork_that_fails_leaves_the_host_mentions_and_a_gap(manifest, monkeypatch):
    def broken(project, **kwargs):
        raise container.Gap("stack-analyser failed (exit 1): boom", "analyze again")

    monkeypatch.setattr(stack_analyser, "run", broken)
    answer = fork_stack.recognize(manifest, REGISTRY, FACTS)
    reason = "stack-analyser failed (exit 1): boom (analyze again)"
    assert answer["checkers"] == [{"checker": "stack-analyser", "state": "failed", "reason": reason},
                                  {"checker": "host", "state": "ran"}]
    assert answer["gaps"] == [{"kind": "checker_failed", "checker": "stack-analyser", "detail": reason}]
    assert [(e["id"], [s["sign"] for s in e["signs"]]) for e in answer["found"]] == [("stripe", ["host"])]


def test_a_host_checker_that_fails_is_a_gap_and_the_fork_s_evidence_stays(manifest, started, monkeypatch):
    def broken(entries, project):
        raise ValueError("no lines")

    monkeypatch.setattr(fork_stack, "check_hosts", broken)
    answer = fork_stack.recognize(manifest, REGISTRY, FACTS)
    assert answer["checkers"] == [{"checker": "stack-analyser", "state": "ran"},
                                  {"checker": "host", "state": "failed", "reason": "ValueError: no lines"}]
    assert answer["gaps"] == [{"kind": "checker_failed", "checker": "host", "detail": "ValueError: no lines"}]
    assert [e["id"] for e in answer["found"]] == ["python", "redis"]


def test_recognize_reports_the_declarations_it_could_not_send(manifest, started):
    facts = {**FACTS, "packages": [fact("conan", "zlib", "conanfile.txt#L2", "conan@1")]}
    answer = fork_stack.recognize(manifest, REGISTRY, facts)
    assert started[0][1]["declarations"] == []
    assert [g["kind"] for g in answer["gaps"]] == ["declaration_not_sent"]


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
                                  tuple(f"folder{i}" for i in range(40)), ("api/gen",))
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
    assert answer["after"]["gaps"] == [{"kind": "not_in_registry", "entry": "setuptools"}]
    assert modules_of(answer["after"]) == modules_of(answer["before"]) == [("app", ["."])]  # one graph under both
    # the registry reads the fast facts without the packages: docker (the Dockerfile) and python; the fork, those it was
    # sent: no declaration, and the evidence it returns whatever it was sent
    assert answer["fast"] == {"registry": ["docker", "python"], "fork": ["python", "redis", "setuptools"], "lost": ["docker"]}
    # one run for the full scan, with the declarations of its facts (the package and the Dockerfile's base), one for the
    # fast scan, with those of its own: none
    assert [sorted(d["name"] for d in sent) for sent in calls] == [["python", "redis"], []]
    assert answer["fast_gaps"] == [{"kind": "not_in_registry", "entry": "setuptools"}]  # the fork's gaps of the fast scan
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

    def broken(project, **kwargs):
        raise RuntimeError("the fork broke")

    monkeypatch.setattr(stack_analyser, "run", broken)
    with pytest.raises(RuntimeError):  # not a Gap: `recognize` leaves it to the caller
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
