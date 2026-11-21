"""The translation between the pre-map's facts and stack-analyser: declarations in, evidence out.

No test starts Node, reaches the network or runs Modal: `stack_analyser.run` is replaced in every one.

    python -B -m pytest -q -p no:cacheprovider benchmarks/project-model/test_fork_stack.py
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE / "tools"), str(ROOT / "daodan/core")]

import container  # noqa: E402
import fork_stack  # noqa: E402
import service_registry  # noqa: E402
import snapshot  # noqa: E402
import stack_analyser  # noqa: E402
import technologies  # noqa: E402

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


def test_an_image_the_packages_already_state_is_not_sent_twice():
    facts = {"packages": [fact("docker", "postgres", "docker-compose.yml", "compose@3")],
             "services": [{"name": "db", "image": "postgres:16", "declared_in": "docker-compose.yml.services.db",
                           "sources": ["renovate@41"]}]}
    sent, _ = fork_stack.declarations(facts)
    assert [(d["name"], d["source"]) for d in sent] == [("postgres", "compose@3")]


def test_a_declaration_the_fork_cannot_take_is_a_gap_not_a_failure():
    facts = {"packages": [fact("conan", "zlib", "conanfile.txt#L2", "conan@1"),
                          fact("pypi", "flask", None, "requirements@2"),
                          fact("npm", "left-pad", "vendor/web/package.json#L5", "npm@1")],
             "excluded": [{"path": "vendor/", "why": "submodule"}]}
    sent, gaps = fork_stack.declarations(facts)
    assert sent == []
    assert gaps == [
        {"kind": "declaration_not_sent", "value": "zlib", "path": "conanfile.txt", "ecosystem": "conan",
         "detail": "the release takes no declaration of type conan"},
        {"kind": "declaration_not_sent", "value": "flask", "path": None, "ecosystem": "pypi",
         "detail": "the pre-map names no file for it"},
        {"kind": "declaration_not_sent", "value": "left-pad", "path": "vendor/web/package.json", "ecosystem": "npm",
         "detail": "the pre-map leaves out its path"}]


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
