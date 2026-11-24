"""The translation between the pre-map's facts and stack-analyser (declarations in, evidence out) that the `stack` step
runs, `daodan/core/stack_recognition.py`.

No test starts Node, reaches the network or runs Modal: `stack_analyser.run` is replaced in every one.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_stack_recognition.py
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import container  # noqa: E402
import service_registry  # noqa: E402
import file_inventory  # noqa: E402
import snapshot  # noqa: E402
import stack_analyser  # noqa: E402
import stack_recognition  # noqa: E402
import technologies  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

PAYLOAD = ROOT / "tests/fixtures/stack/py-fastapi-compose.payload.json"

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
         "mark": "marks/redis.svg"}
PYTHON = {"id": "python", "name": "Python", "kind": "project", "category": "tool", "type": "altro",
          "site": "https://www.python.org", "mark": "marks/python.svg"}
STRIPE = {"id": "stripe", "name": "Stripe", "kind": "service", "type": "gateway", "site": "https://stripe.com",
          "mark": None, "hosts": ["api.stripe.com"]}


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


def recognized(work: Path, files: dict[str, str] | None = None, **facts) -> dict:
    """`stack_recognition.run` with the registry shipped, over a project of `files` and the pre-map's `facts` (a test that
    uses it takes `real_stack`: what the project shows is what the release recognizes)."""
    return stack_recognition.run(snapshot_of(work, files or {"README.md": "# app\n"}), service_registry.load(), facts)


def package_signs(answer: dict) -> set[tuple]:
    """`(id, value, path, line)` of the package signs of `answer["found"]`."""
    return {(item["id"], sign["value"], sign["path"], sign["line"]) for item in answer["found"]
            for sign in item["signs"] if sign["sign"] == "package"}



# ---------------------------------------------------------------------------------------------- declarations

def test_each_source_of_a_package_fact_is_one_declaration():
    facts = {"packages": [{"ecosystem": "pypi", "name": "fastapi", "version": "0.115", "declared_in": "api/requirements.txt#L3",
                           "sources": ["requirements@2", "renovate@41"]}]}
    sent, gaps = stack_recognition.declarations(facts)
    assert sent == [{"type": "python", "name": "fastapi", "version": "0.115", "path": "api/requirements.txt", "line": 3, "source": s}
                    for s in ("requirements@2", "renovate@41")] and gaps == []


def test_a_fact_without_version_or_line_sends_neither():
    sent, gaps = stack_recognition.declarations({"packages": [fact("npm", "react", "web/package.json", "npm@1")]})
    assert sent == [{"type": "npm", "name": "react", "path": "web/package.json", "source": "npm@1"}] and gaps == []


def test_the_ecosystems_of_the_premap_are_the_registry_s_inverse_and_the_others_pass_as_they_are():
    ecosystems = ("pypi", "crates", "go", "rubygems", "composer", "github-actions", "terraform", "terraform-resource",
                  "npm", "deno", "maven", "nuget", "hex", "pub", "swiftpm")
    sent, gaps = stack_recognition.declarations({"packages": [fact(e, "x", "m.file", "s@1") for e in ecosystems]})
    assert [d["type"] for d in sent] == ["python", "rust", "golang", "ruby", "php", "githubAction", "terraform",
                                         "terraform.resource", "npm", "deno", "maven", "nuget", "hex", "pub", "swiftpm"]
    assert gaps == [] and {d["type"] for d in sent} <= set(stack_recognition.TYPES)


def test_the_types_are_the_ones_the_release_accepts():
    assert stack_recognition.TYPES == ("deno", "docker", "githubAction", "golang", "hex", "maven", "npm", "nuget", "php", "pub",
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
    sent, gaps = stack_recognition.declarations(facts)
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
    ours = [(eco, name, path, line) for eco, name, _, path, line, _ in stack_recognition._rows(facts)]
    assert ours == [(eco, name, path, line) for eco, name, path, line, _ in service_registry.step1_packages(manifest, facts)]
    assert len(ours) == 7  # the sample is not empty of what it tests


def test_an_image_the_packages_already_state_is_not_sent_twice():
    facts = {"packages": [fact("docker", "postgres", "docker-compose.yml", "compose@3")],
             "services": [{"name": "db", "image": "postgres:16", "declared_in": "docker-compose.yml.services.db",
                           "sources": ["renovate@41"]}]}
    sent, _ = stack_recognition.declarations(facts)
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
    sent, gaps = stack_recognition.declarations(facts)
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
    sent, gaps = stack_recognition.declarations({"packages": [fact("npm", f"p{i}", path, "npm@1") for i, path in enumerate(paths)]})
    assert [d["path"] for d in sent] == paths and gaps == []


def test_a_fact_no_source_states_is_a_gap():
    facts = {"packages": [{"ecosystem": "npm", "name": "x", "declared_in": "package.json"},
                          {"ecosystem": "npm", "name": "y", "declared_in": "package.json#L2", "sources": []},
                          fact("npm", "z", "package.json#L3", "npm@1")]}
    sent, gaps = stack_recognition.declarations(facts)
    assert [d["name"] for d in sent] == ["z"]
    assert gaps == [not_sent("x", "package.json", "npm", "no source states it"),
                    not_sent("y", "package.json", "npm", "no source states it")]


def test_a_fact_without_a_name_is_a_gap():
    sent, gaps = stack_recognition.declarations({"packages": [fact("npm", "", "package.json#L2", "npm@1")]})
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
    assert stack_recognition.perimeter(tmp_path, files, ("third_party",)) == ((".git", "api", "node_modules"),
                                                                              ("gen", "third_party"), [])
    assert sorted(p.relative_to(tmp_path).as_posix() for p in listed) == [".", "web", "web/gen", "web/src"]


def test_a_name_or_path_with_a_comma_is_an_entry_like_any_other(tmp_path):
    """The tool reads the perimeter from a file, not from a comma-separated option: no name is a case of its own."""
    for rel in ("a/x.py", "a/gen/k.py", "a,b/y.py", "c,d/keep.py", "c,d/gen/o.py", "node_modules/z.js"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x", encoding="utf-8")
    files = ["a/x.py", "a/gen/k.py", "c,d/keep.py"]
    # `a,b` is skipped by name, `c,d/gen` goes by path (`gen` is live under `a`), `x,y` is left out by the pre-map
    assert stack_recognition.perimeter(tmp_path, files, ("x,y",)) == (("a,b", "node_modules"), ("c,d/gen", "x,y"), [])


def test_a_folder_that_cannot_be_listed_leaves_the_perimeter_to_the_fork(tmp_path):
    assert stack_recognition.perimeter(tmp_path / "gone", ["web/a.ts"], ("third_party",)) == ((), ("third_party",), [])


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
    assert stack_recognition.perimeter(tmp_path, files, ()) == (("other",), ("junc", "sym"), [])
    assert sorted(entered) == [tmp_path, tmp_path / "real"]


# ---------------------------------------------------------------------------------------------- evidence out

def test_evidence_is_collected_from_every_component_once():
    same = evidence("redis", "package", "redis", "/pyproject.toml", line=7)
    deep = component(evidence("redis", "image", "redis", "/docker-compose.yml"))
    payload = component(same, childs=[component(dict(same), childs=[deep]), component(evidence("redis", "file", "x", "/x"))])
    out, gaps = stack_recognition.found(payload, registry(REDIS), {"pyproject.toml", "docker-compose.yml", "x"}, ())
    assert gaps == []
    assert [(s["sign"], s["value"], s["path"], s["line"]) for s in out[0]["signs"]] == [
        ("file", "x", "x", None), ("package", "redis", "docker-compose.yml", None), ("package", "redis", "pyproject.toml", 7)]


def test_the_same_evidence_from_two_sources_stays_two_signs():
    out, _ = stack_recognition.found(component(evidence("redis", "package", "redis", "/a.toml", "stack-analyser"),
                                        evidence("redis", "package", "redis", "/a.toml", "other")),
                              registry(REDIS), {"a.toml"}, ())
    assert [s["source"] for s in out[0]["signs"]] == ["stack-analyser", "other"]


def test_a_declaration_s_evidence_is_kept_whatever_its_file_and_the_tool_s_own_only_for_a_file_of_the_snapshot():
    """The registry takes a declared package at the path the pre-map names, in the snapshot or not; the tool's own reading
    is a file it was given only when the snapshot holds it. Either kind is dropped under a path the pre-map leaves out."""
    payload = component(
        evidence("redis", "package", "redis", "/pyproject.toml"),  # the tool's, in the snapshot: kept
        evidence("redis", "package", "redis", "/missing.toml"),  # the tool's, outside the snapshot: dropped, and said
        evidence("redis", "package", "aioredis", "/.github/workflows/x.yml", "renovate@41"),  # a declaration's: kept
        evidence("redis", "package", "redis", "/vendor/web/package.json"),  # the tool's, excluded: dropped
        evidence("redis", "package", "redis", "/vendor/web/Dockerfile", "buildkit@v0.34"))  # a declaration's, excluded
    out, gaps = stack_recognition.found(payload, registry(REDIS), {"pyproject.toml", "vendor/web/package.json"}, ("vendor",))
    assert [(s["path"], s["source"]) for s in out[0]["signs"]] == [
        (".github/workflows/x.yml", "renovate@41"), ("pyproject.toml", "stack-analyser")]
    assert gaps == [{"kind": "evidence_outside_snapshot", "count": 1, "paths": ["missing.toml"]}]  # not the excluded ones


def test_the_evidence_the_snapshot_lacks_is_counted_with_its_first_five_distinct_paths_sorted():
    items = [evidence("redis", "package", "redis", f"/{name}.toml", line=line)
             for name, line in (("g", 1), ("b", 1), ("b", 2), ("e", 1), ("a", 1), ("f", 1), ("c", 1), ("d", 1))]
    out, gaps = stack_recognition.found(component(*items, evidence("python", "extension", ".py", "/x/y.py")), registry(REDIS), set(), ())
    assert out == [] and gaps == [{"kind": "evidence_outside_snapshot", "count": 8,
                                   "paths": ["a.toml", "b.toml", "c.toml", "d.toml", "e.toml"]}]  # extension proves nothing


def test_evidence_without_a_technology_is_not_counted_as_outside_the_snapshot():
    gaps = stack_recognition.found(component(evidence(None, "package", "x", "/missing.toml")), registry(), set(), ())[1]
    assert gaps == [{"kind": "evidence_without_technology", "count": 1}]


def test_extension_evidence_alone_recognizes_nothing():
    payload = component(evidence("python", "extension", ".py", "/app/main.py"))
    assert stack_recognition.found(payload, registry(), {"app/main.py"}, ()) == ([], [])  # not even a gap: no entry comes out


def test_evidence_without_a_technology_is_one_gap_with_its_count():
    nameless = evidence(None, "package", "x", "/a.toml")
    payload = component(nameless, {"kind": "file", "value": "y", "path": "/a.toml", "source": "stack-analyser"},
                        childs=[component(dict(nameless))])
    assert stack_recognition.found(payload, registry(), {"a.toml"}, ()) == (
        [], [{"kind": "evidence_without_technology", "count": 2}])


def test_an_environment_variable_is_a_mention(tmp_path, monkeypatch):
    manifest = snapshot_of(tmp_path, {"api/pay.py": "import os\nKEY = os.environ['REDIS_URL']\n"})
    payload = component(evidence("redis", "env", "REDIS_URL", "/api/pay.py", line=2))
    monkeypatch.setattr(stack_analyser, "run", lambda *args, **kwargs: payload)
    record = technologies.derive(manifest, registry(REDIS), {"packages": [], "excluded": []})
    assert record["technologies"] == []
    assert [(e["id"], [(s["sign"], s["strength"]) for s in e["signs"]]) for e in record["mentioned"]] == [
        ("redis", [("env", "mentioned")])]
    assert "source" not in record["mentioned"][0]


def test_an_id_the_registry_lacks_still_comes_out_with_a_gap():
    out, gaps = stack_recognition.found(component(evidence("setuptools", "package", "setuptools", "/pyproject.toml")),
                                 registry(REDIS), {"pyproject.toml"}, ())
    assert out == [{"id": "setuptools", "name": "setuptools", "kind": "project", "category": "framework", "type": None,
                    "site": None, "mark": None, "source": "registry",
                    "signs": [{"sign": "package", "value": "setuptools", "path": "pyproject.toml", "line": None,
                               "strength": "declared", "source": "stack-analyser"}]}]
    assert gaps == [{"kind": "not_in_registry", "entry": "setuptools"}]


def test_an_entry_takes_its_fields_from_the_registry_and_comes_in_the_order_of_its_id():
    items = [evidence(t, "file", "f", "/f") for t in ("redis", "python")]
    out, gaps = stack_recognition.found(component(*items), registry(REDIS, PYTHON), {"f"}, ())
    assert [(e["id"], e["name"], e["kind"], e["category"], e["type"], e["site"], e["mark"], e["source"]) for e in out] == [
        ("python", "Python", "project", "tool", "altro", "https://www.python.org", "marks/python.svg", "registry"),
        ("redis", "Redis", "service", "service", "database", "https://redis.io/", "marks/redis.svg", "registry")]
    assert gaps == []


def test_the_signs_of_an_entry_are_ordered_as_service_registry_orders_them():
    items = [evidence("redis", "package", "redis", "/b.toml", line=2), evidence("redis", "package", "aioredis", "/b.toml", line=2),
             evidence("redis", "package", "redis", "/a.toml"), evidence("redis", "env", "REDIS_URL", "/z.py", line=1),
             evidence("redis", "package", "redis", "/b.toml", line=1)]
    out, _ = stack_recognition.found(component(*items), registry(REDIS), {"a.toml", "b.toml", "z.py"}, ())
    assert [(s["sign"], s["path"], s["line"], s["value"]) for s in out[0]["signs"]] == [
        ("env", "z.py", 1, "REDIS_URL"), ("package", "a.toml", None, "redis"), ("package", "b.toml", 1, "redis"),
        ("package", "b.toml", 2, "aioredis"), ("package", "b.toml", 2, "redis")]


def test_every_sign_carries_its_source_and_its_strength():
    items = [evidence("redis", "env", "REDIS_URL", "/a.py", "stack-analyser", line=1),
             evidence("redis", "image", "redis", "/c.yml", "daodan-compose")]
    out, _ = stack_recognition.found(component(*items), registry(REDIS), {"a.py", "c.yml"}, ())
    assert [(s["sign"], s["strength"], s["source"]) for s in out[0]["signs"]] == [
        ("env", "mentioned", "stack-analyser"), ("package", "declared", "daodan-compose")]


def test_the_recorded_payload_gives_the_expected_technologies():
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    files = {"docker-compose.yml", "Dockerfile", "pyproject.toml", "app/__init__.py", "app/main.py"}
    out, gaps = stack_recognition.found(payload, service_registry.load(), files, ())
    assert {e["id"] for e in out} == {"docker", "fastapi", "postgresql", "python", "redis", "setuptools", "sqlalchemy"}
    assert gaps == []  # every rule of the release is an entry of the registry
    by_id = {e["id"]: e for e in out}
    assert [(s["sign"], s["path"]) for s in by_id["python"]["signs"]] == [("package", "Dockerfile")]  # `.py` proves nothing
    assert [(s["sign"], s["path"]) for s in by_id["redis"]["signs"]] == [("package", "docker-compose.yml"),
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
# the tool read `node_modules/x.js` by itself, a file the snapshot lacks: said, not silent
OUTSIDE = {"kind": "evidence_outside_snapshot", "count": 1, "paths": ["api/node_modules/x.js"]}


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


def test_run_sends_declarations_and_perimeter_and_answers_in_the_shape_of_service_registry_run(manifest, started):
    answer = stack_recognition.run(manifest, REGISTRY, FACTS)
    [(project, kwargs)] = started
    assert project.resolve() == (manifest.parents[1] / "app").resolve()
    assert kwargs == {"declarations": [{"type": "python", "name": "redis", "version": "==5.0", "path": "api/requirements.txt",
                                        "line": 1, "source": "requirements@2"}],
                      "skip_dirs": (".git", "gen", "node_modules"), "ignore": ("api/gen",)}
    assert list(answer) == ["found", "checkers", "gaps", "ran"] and answer["gaps"] == [OUTSIDE]
    assert answer["ran"] == ["registry_hosts", "stack-analyser"]
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
    answer = stack_recognition.run(manifest, REGISTRY, FACTS)
    reason = "stack-analyser failed (exit 1): boom (analyze again)"
    assert answer["checkers"] == [{"checker": "stack-analyser", "state": "failed", "reason": reason},
                                  {"checker": "host", "state": "ran"}]
    assert answer["gaps"] == [{"kind": "checker_failed", "checker": "stack-analyser", "detail": reason}]
    assert [(e["id"], [s["sign"] for s in e["signs"]]) for e in answer["found"]] == [("stripe", ["host"])]


def test_an_error_the_tool_does_not_name_is_a_gap_too(manifest, monkeypatch):
    def broken(project, **kwargs):
        raise RuntimeError("the tool broke")

    monkeypatch.setattr(stack_analyser, "run", broken)
    answer = stack_recognition.run(manifest, REGISTRY, FACTS)
    assert answer["checkers"][0] == {"checker": "stack-analyser", "state": "failed", "reason": "RuntimeError: the tool broke"}
    assert "stack-analyser" not in answer["ran"] and [e["id"] for e in answer["found"]] == ["stripe"]


def test_a_host_checker_that_fails_is_a_gap_and_the_fork_s_evidence_stays(manifest, started, monkeypatch):
    def broken(entries, project):
        raise ValueError("no lines")

    monkeypatch.setattr(stack_recognition, "check_hosts", broken)
    answer = stack_recognition.run(manifest, REGISTRY, FACTS)
    assert answer["checkers"] == [{"checker": "stack-analyser", "state": "ran"},
                                  {"checker": "host", "state": "failed", "reason": "ValueError: no lines"}]
    assert answer["gaps"] == [{"kind": "checker_failed", "checker": "host", "detail": "ValueError: no lines"}, OUTSIDE]
    assert [e["id"] for e in answer["found"]] == ["python", "redis"]


def test_run_reports_the_declarations_it_could_not_send(manifest, started):
    facts = {**FACTS, "packages": [fact("conan", "zlib", "conanfile.txt#L2", "conan@1")]}
    answer = stack_recognition.run(manifest, REGISTRY, facts)
    assert started[0][1]["declarations"] == []
    assert [g["kind"] for g in answer["gaps"]] == ["declaration_not_sent", "evidence_outside_snapshot"]


PAGES, GOTENBERG = "actions/deploy-pages", "gotenberg/gotenberg"


def test_a_declared_package_or_image_of_a_file_the_snapshot_lacks_is_recognized_as_the_registry_does(manifest, monkeypatch):
    """The corpus round's `github.pages` (real-app-kotlinconf) and `gotenberg` (real-stack-documenso): the pre-map names a
    workflow in a dot folder and a Dockerfile with a suffix, the registry takes them, the snapshot holds neither."""
    facts = {"packages": [fact("github-actions", PAGES, ".github/workflows/x.yml#L5", "githubactions@1"),
                          fact("github-actions", "actions/upload-pages-artifact", ".github/workflows/x.yml#L9", "githubactions@1")],
             "docker_builds": [{"dockerfile": "docker/Dockerfile.gotenberg", "sources": ["dockerfile@1"],
                                "stages": [{"base": f"{GOTENBERG}:8", "line": 1}]}], "excluded": []}
    technology = {PAGES: "github.pages", "actions/upload-pages-artifact": "github.pages", GOTENBERG: "gotenberg"}

    def tool(project, declarations=(), **kwargs):  # it recognizes what it is sent, with the declaration's source and path
        return component(*[evidence(technology[d["name"]], "package" if d["type"] == "githubAction" else "image", d["name"],
                                    "/" + d["path"], d["source"], line=d.get("line")) for d in declarations])

    monkeypatch.setattr(stack_analyser, "run", tool)
    with open_snapshot(manifest) as store:
        assert not {".github/workflows/x.yml", "docker/Dockerfile.gotenberg"} & set(dict(store.iter_file_headers_only()))
    answer = stack_recognition.run(manifest, service_registry.load(), facts)
    by_id = {entry["id"]: entry for entry in answer["found"]}
    assert [(s["sign"], s["path"], s["line"], s["strength"], s["source"]) for s in by_id["github.pages"]["signs"]] == [
        ("package", ".github/workflows/x.yml", 5, "declared", "githubactions@1"),
        ("package", ".github/workflows/x.yml", 9, "declared", "githubactions@1")]
    assert [(s["sign"], s["path"], s["strength"]) for s in by_id["gotenberg"]["signs"]] == [
        ("package", "docker/Dockerfile.gotenberg", "declared")]
    assert [g for g in answer["gaps"] if g["kind"] in ("evidence_outside_snapshot", "not_in_registry")] == []


def test_the_first_round_s_two_paths_are_not_in_the_snapshot_and_what_a_declaration_proves_there_is_kept(tmp_path):
    """The first round lost `github.pages` and `gotenberg`: the pre-map names a workflow in a dot folder and a Dockerfile
    with a suffix, the registry takes a package at those paths, and the snapshot holds neither. A declaration's evidence
    there stays; the tool's own reading of a file the snapshot lacks is dropped and counted."""
    paths = (".github/workflows/web-deploy.yml", "docker/development/Dockerfile.gotenberg")
    manifest = snapshot_of(tmp_path, {paths[0]: "name: web\n", paths[1]: "FROM gotenberg/gotenberg:8\n",
                                      "docker/Dockerfile": "FROM alpine\n"})
    with open_snapshot(manifest) as store:
        files = set(dict(store.iter_file_headers_only()))
    assert "docker/Dockerfile" in files and not files & set(paths)
    pages = {"id": "github.pages", "name": "Github Pages", "kind": "service"}
    gotenberg = {"id": "gotenberg", "name": "Gotenberg", "kind": "service"}
    payload = component(evidence("github.pages", "action", PAGES, "/" + paths[0], "githubactions@1"),
                        evidence("gotenberg", "image", GOTENBERG, "/" + paths[1], "dockerfile@1"),
                        evidence("gotenberg", "image", GOTENBERG, "/" + paths[1]))  # the tool's own, same file
    out, gaps = stack_recognition.found(payload, registry(pages, gotenberg), files, ())
    assert [(entry["id"], [s["source"] for s in entry["signs"]]) for entry in out] == [
        ("github.pages", ["githubactions@1"]), ("gotenberg", ["dockerfile@1"])]
    assert gaps == [{"kind": "evidence_outside_snapshot", "count": 1, "paths": [paths[1]]}]


# ---------------------------------------------------------------------------------------------- the five changes

def test_a_forbidden_file_is_in_the_perimeter(tmp_path, started):
    """The tool opens `.env.example`, which `source_files.FORBIDDEN_GLOBS` forbids Daodan: the file of a live folder is
    named in `ignore`, and so is one at the root; a file Daodan may read is not."""
    manifest = snapshot_of(tmp_path, {"web/src/a.ts": "export {}\n", "web/package.json": "{}\n"})
    for rel in ("web/.env.example", "web/src/.env.sample", ".env.template", "web/server.pem", "web/src/notes.txt"):
        (tmp_path / "app" / rel).write_text("KEY=1\n", encoding="utf-8")
    stack_recognition.run(manifest, REGISTRY, {"packages": [], "excluded": []})
    [(_, kwargs)] = started
    assert kwargs["ignore"] == (".env.template", "web/.env.example", "web/server.pem", "web/src/.env.sample")


def test_an_image_an_action_and_a_terraform_resource_are_package_signs():
    items = [evidence("redis", kind, kind, "/f") for kind in ("package", "image", "action", "terraform", "file", "source")]
    out, _ = stack_recognition.found(component(*items, evidence("redis", "env", "REDIS_URL", "/f")),
                                     registry(REDIS), {"f"}, ())
    assert sorted((s["value"], s["sign"], s["strength"]) for s in out[0]["signs"]) == [
        ("REDIS_URL", "env", "mentioned"), ("action", "package", "declared"), ("file", "file", "declared"),
        ("image", "package", "declared"), ("package", "package", "declared"), ("source", "source", "declared"),
        ("terraform", "package", "declared")]


def test_a_malformed_evidence_item_is_counted_not_raised():
    good = evidence("redis", "package", "redis", "/a.toml", line=2)
    broken = [{"tech": "redis", "value": "x", "path": "/a.toml", "source": "stack-analyser"},  # no kind
              {"tech": "redis", "kind": "package", "value": "x", "path": "/a.toml"},  # no source
              {"tech": "redis", "kind": "package", "value": ["x"], "path": "/a.toml", "source": "s"},  # not text
              {"tech": "redis", "kind": "package", "value": "x", "path": None, "source": "s"},
              {"tech": 7, "kind": "package", "value": "x", "path": "/a.toml", "source": "s"},
              {**good, "line": "2"}, "evidence", 5, None]
    payload = component(good, *broken, childs=[component(*broken[:1]), "child", {"evidence": 5}])
    out, gaps = stack_recognition.found(payload, registry(REDIS), {"a.toml"}, ())
    assert [(s["path"], s["line"]) for s in out[0]["signs"]] == [("a.toml", 2)]
    assert gaps == [{"kind": "evidence_malformed", "count": len(broken) + 3}]


def test_a_malformed_fact_is_a_gap_not_a_failure():
    facts = {"packages": [{"name": "x", "declared_in": "package.json", "sources": ["npm@1"]},  # no ecosystem
                          "text", {"ecosystem": ["npm"], "name": "y", "declared_in": "p.json", "sources": ["n@1"]},
                          {"ecosystem": "npm", "name": "v", "declared_in": "p.json", "sources": "npm@1"},
                          {"ecosystem": "npm", "name": "w", "declared_in": "p.json", "sources": ["npm@1"], "version": 3},
                          fact("npm", "z", "package.json#L3", "npm@1")],
             "services": [{"name": "db", "image": "postgres:16", "sources": ["compose@3"]}, {"name": "db2", "image": 7,
                                                                                          "declared_in": 5}],
             "docker_builds": [{"dockerfile": "Dockerfile", "sources": ["d@1"], "stages": [5]}, 3]}
    sent, gaps = stack_recognition.declarations(facts)
    assert [d["name"] for d in sent] == ["z"]
    assert {g["kind"] for g in gaps} == {"declaration_not_sent"} and len(gaps) == 9


def test_a_perimeter_entry_the_fork_would_refuse_is_left_out_with_a_gap(tmp_path, started):
    """The tool exits with an error for a folder name with a separator and for a path with a drive letter or `..`: such an
    entry is left out and said, and a name with a comma is no longer a case of its own."""
    manifest = snapshot_of(tmp_path, {"a/x.py": "x\n", "a/gen/k.py": "x\n"})
    for rel in ("back\\slash/y.py", "c,d/z.py", "gen2,x/w.py", "node_modules/z.js"):  # on the disk, not in the snapshot
        (tmp_path / "app" / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / rel).write_text("x", encoding="utf-8")
    facts = {"packages": [], "excluded": [{"path": "C:/x/"}, {"path": "a/../b"}, {"path": "up\\..\\y"}, {"path": "gen/p,q"},
                                          {"path": "third_party"}]}
    answer = stack_recognition.run(manifest, REGISTRY, facts)
    [(_, kwargs)] = started
    # `back\slash` is no name for `skipDirs` but is a path for `ignore`: the tool does not enter it
    assert kwargs["skip_dirs"] == (".git", "c,d", "gen2,x", "node_modules")
    assert kwargs["ignore"] == ("back\\slash", "gen/p,q", "third_party")
    assert [g for g in answer["gaps"] if g["kind"] == "perimeter_entry_left_out"] == [
        {"kind": "perimeter_entry_left_out", "option": "ignore", "entry": "C:/x"},
        {"kind": "perimeter_entry_left_out", "option": "ignore", "entry": "a/../b"},
        {"kind": "perimeter_entry_left_out", "option": "ignore", "entry": "up\\..\\y"}]


def test_the_store_is_closed_while_the_fork_runs(manifest, monkeypatch):
    state = {"open": 0, "opened": 0, "during": []}
    real = stack_recognition.open_snapshot

    @contextlib.contextmanager
    def tracked(path):
        state["open"] += 1
        state["opened"] += 1
        try:
            with real(path) as store:
                yield store
        finally:
            state["open"] -= 1

    def tool(project, **kwargs):
        state["during"].append(state["open"])
        return FORK

    monkeypatch.setattr(stack_recognition, "open_snapshot", tracked)
    monkeypatch.setattr(stack_analyser, "run", tool)
    answer = stack_recognition.run(manifest, REGISTRY, FACTS)
    assert state["during"] == [0] and state["open"] == 0
    assert state["opened"] == 2  # the perimeter, then the host mentions
    assert any(e["id"] == "stripe" for e in answer["found"])  # the host check read the snapshot after the fork


def test_ran_names_the_sources_of_this_run(manifest, started, monkeypatch):
    """The pre-map's sources that ran (`facts["sources"]`: `{"source": "name@version", "state": ...}`) by name, a source
    that looked and had nothing to state (`not_needed`) among them, the tool and the host check when each ran."""
    sources = [{"source": "renovate@41", "state": "ran"}, {"source": "requirements@2", "state": "ran"},
               {"source": "cargo@1", "state": "not_run"}, {"source": "go@1", "state": "not_needed"},
               {"source": "compose@3", "state": "failed"}, {"state": "ran"}, "npm@1", None]
    answer = stack_recognition.run(manifest, REGISTRY, {**FACTS, "sources": sources})
    assert answer["ran"] == ["go", "registry_hosts", "renovate", "requirements", "stack-analyser"]

    def broken(project, **kwargs):
        raise container.Gap("stack-analyser failed (exit 1): boom", "analyze again")

    monkeypatch.setattr(stack_analyser, "run", broken)
    # no sign of a pre-map source is made without the tool: only the host check ran
    assert stack_recognition.run(manifest, REGISTRY, {**FACTS, "sources": sources})["ran"] == ["registry_hosts"]
    monkeypatch.setattr(stack_analyser, "run", lambda project, **kwargs: FORK)
    monkeypatch.setattr(stack_recognition, "check_hosts", lambda entries, project: 1 / 0)
    assert stack_recognition.run(manifest, REGISTRY, FACTS)["ran"] == ["stack-analyser"]


# ---------------------------------------------------------------------------------------------- the review of B2

def inventory_of(work: Path, files: dict[str, str]) -> Path:
    """The manifest the inventory step alone writes (`stack` runs before `parse`): the `files` table is empty."""
    app = work / "app"
    for rel, text in files.items():
        (app / rel).parent.mkdir(parents=True, exist_ok=True)
        (app / rel).write_text(text, encoding="utf-8", newline="\n")
    for command in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
        subprocess.run(command, cwd=app, check=True, capture_output=True)
    manifest = work / "snapshot/manifest.sqlite"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    file_inventory.write(app, manifest)
    return manifest


def test_the_files_come_from_the_inventory_not_from_the_parse_table(tmp_path, started):
    manifest = inventory_of(tmp_path, FILES)
    with open_snapshot(manifest) as store:
        assert dict(store.iter_file_headers_only()) == {}  # the `parse` step has not run
    (tmp_path / "app/api/node_modules").mkdir()
    (tmp_path / "app/api/node_modules/x.js").write_text("var a = 1;\n", encoding="utf-8")
    answer = stack_recognition.run(manifest, REGISTRY, FACTS)
    [(_, kwargs)] = started
    assert kwargs["skip_dirs"] == (".git", "gen", "node_modules") and kwargs["ignore"] == ("api/gen",)  # `api` is live
    assert answer["gaps"] == [OUTSIDE]  # the evidence in an inventoried file is kept, the other is dropped
    by_id = {e["id"]: e for e in answer["found"]}
    assert [s["path"] for s in by_id["redis"]["signs"]] == ["api/requirements.txt"]
    assert [s["value"] for s in by_id["stripe"]["signs"]] == ["api.stripe.com"]  # the host mention is read


def test_a_failed_tool_makes_no_sign_of_the_pre_map_sources(manifest, monkeypatch):
    def broken(project, **kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(stack_analyser, "run", broken)
    sources = [{"source": "renovate@41", "state": "ran"}]
    assert stack_recognition.run(manifest, REGISTRY, {**FACTS, "sources": sources})["ran"] == ["registry_hosts"]


def test_every_link_is_in_the_perimeter_by_its_path_even_to_a_file(tmp_path, started):
    manifest = snapshot_of(tmp_path, {"web/a.ts": "export {}\n", "private/.env": "KEY=1\n"})
    os.symlink("private/.env", tmp_path / "app/package.json")  # a link to a file, its name is no live folder's
    os.symlink("private", tmp_path / "app/web/shortcut")
    stack_recognition.run(manifest, REGISTRY, {"packages": [], "excluded": []})
    [(_, kwargs)] = started
    assert "package.json" in kwargs["ignore"] and "web/shortcut" in kwargs["ignore"]
    assert "package.json" not in kwargs["skip_dirs"] and "shortcut" not in kwargs["skip_dirs"]


def test_a_secret_named_file_is_ignored_by_its_name_and_never_opened(tmp_path, monkeypatch):
    for rel in ("web/a.ts", "web/my-secret.txt", "web/Aws_Credentials.json", "web/notes.txt"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x\n", encoding="utf-8")
    real_stat, real_open = Path.stat, Path.open

    def refused(path, *args, **kwargs):
        if Path(path).name in ("my-secret.txt", "Aws_Credentials.json"):
            raise AssertionError(f"opened {path}")

    monkeypatch.setattr(Path, "stat", lambda self, *a, **k: refused(self) or real_stat(self, *a, **k))
    monkeypatch.setattr(Path, "open", lambda self, *a, **k: refused(self) or real_open(self, *a, **k))
    monkeypatch.setattr("builtins.open", lambda file, *a, **k: refused(file) or open_real(file, *a, **k))
    skip, ignore, gaps = stack_recognition.perimeter(tmp_path, ["web/a.ts"], ())
    assert ignore == ("web/Aws_Credentials.json", "web/my-secret.txt") and gaps == []


open_real = open


def test_a_line_that_is_not_a_positive_integer_is_a_gap_not_a_failure():
    for line in (True, 0, -3, "2", 1.5):
        with pytest.raises(TypeError):
            stack_recognition._row("npm", "x", None, "package.json", line, ["npm@1"])
    assert [stack_recognition._row("npm", "x", None, "package.json", line, ["npm@1"])[4] for line in (None, 4)] == [None, 4]
    builds = [{"dockerfile": "Dockerfile", "sources": ["d@1"], "stages": [{"base": base, "line": line}]}
              for base, line in (("node:20", True), ("python:3", 0), ("nginx:1", 2))]
    sent, gaps = stack_recognition.declarations({"docker_builds": builds})
    assert [d["name"] for d in sent] == ["nginx"] and [g["detail"] for g in gaps] == ["the pre-map's fact is malformed"] * 2


def test_an_excluded_item_whose_path_is_not_text_is_ignored(tmp_path):
    facts = {"packages": [fact("npm", "z", "package.json#L3", "npm@1")],
             "excluded": [{"path": 5}, {"path": ["a"]}, {"path": None}, "x", {"path": "gen/"}]}
    assert stack_recognition._left_out(facts) == ("gen/",)
    assert [d["name"] for d in stack_recognition.declarations(facts)[0]] == ["z"]
