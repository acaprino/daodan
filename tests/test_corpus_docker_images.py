"""Docker Hub aliases and repository identity across the stack's package, Compose and build inputs."""
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "daodan/core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

import service_registry  # noqa: E402
import snapshot  # noqa: E402
from pipeline import Context, Scan, Stack, events  # noqa: E402
from test_codebase_map_stack_recognition import package_signs, recognized  # noqa: E402


def test_dockerfile_and_compose_keep_the_original_registry_and_owning_publisher(real_stack, tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "compose.yaml").write_text(
        "services:\n"
        "  db:\n"
        "    image: docker.io/library/postgres:16\n"
        "  private:\n"
        "    image: private.example:5000/library/postgres:16\n"
        "  custom:\n"
        "    image: custom/redis:7\n",
        encoding="utf-8",
    )
    (project / "Dockerfile").write_text(
        "FROM registry-1.docker.io/library/redis:${TAG} AS cache\n"
        "FROM mirror.example/redis AS base\n"
        "FROM localhost:5000/playwright AS local\n"
        "FROM mcr.microsoft.com/playwright:v1 AS verified\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    context = Context(manifest, events.Bus(), fast_scan=True)
    facts = json.loads(Path(Scan.run(context)["premap"]).read_text(encoding="utf-8"))
    stack = json.loads(Path(Stack.run(context)["path"]).read_text(encoding="utf-8"))
    packages = {d["name"] for d in facts["packages"] if d["ecosystem"] == "docker"}
    assert packages == {"postgres", "private.example:5000/library/postgres", "custom/redis",
                        "redis", "mirror.example/redis", "localhost:5000/playwright", "mcr.microsoft.com/playwright"}
    assert {s["image"] for s in facts["configured_services"]} == {
        "docker.io/library/postgres:16", "private.example:5000/library/postgres:16", "custom/redis:7"}
    # the release reads each file by itself (no line, the repository as written) and is given the pre-map's
    # declarations (the name as the pre-map keeps it): both stay, each with its source (the label up to `@`)
    signs = {e["id"]: {(s["value"], s["path"], s["line"], s["source"].partition("@")[0])
                       for s in e["signs"] if s["sign"] == "package"} for e in stack["technologies"]}
    assert signs["postgresql"] == {("postgres", "compose.yaml", 3, "modules.py"),
                                   ("docker.io/library/postgres", "compose.yaml", None, "stack-analyser")}
    assert signs["redis"] == {("redis", "Dockerfile", 1, "modules.py"),
                              ("registry-1.docker.io/library/redis", "Dockerfile", None, "stack-analyser")}
    assert signs["playwright"] == {("mcr.microsoft.com/playwright", "Dockerfile", 4, "modules.py"),
                                   ("mcr.microsoft.com/playwright", "Dockerfile", None, "stack-analyser")}


def test_saved_packages_ci_service_images_and_docker_builds_share_exact_match_semantics(real_stack, tmp_path):
    leaf = "gcr.io/distroless/nodejs24-debian13"  # real-svc-otel-demo, src/frontend/Dockerfile
    facts = {
        "packages": [{"ecosystem": "docker", "name": "index.docker.io/library/postgres", "declared_in": "compose.yaml#L8",
                      "sources": ["renovate@1"]},
                     {"ecosystem": "docker", "name": "registry-1.docker.io/bitnami/postgresql", "declared_in": "job.yaml",
                      "sources": ["renovate@1"]}],
        "services": [{"name": "db", "declared_in": "compose.yaml.services.db", "image": "postgres:16", "sources": ["compose@1"]},
                     {"name": "fake", "declared_in": "job.yaml.services.fake", "image": "private.test/bitnami/postgresql:16",
                      "sources": ["compose@1"]},
                     {"name": "fake", "declared_in": "other.yml.services.fake", "image": "redis.unrelated.com/redis:7",
                      "sources": ["compose@1"]}],
        "docker_builds": [{"dockerfile": "Dockerfile", "sources": ["buildkit@1"], "stages": [
            {"line": 1, "base": leaf + "@sha256:" + "a"*64}, {"line": 2, "base": "registry:5000/" + leaf}]}],
    }
    packages = service_registry.step1_packages(Path("unused"), facts)
    assert sum(path == "compose.yaml" for _, _, path, *_ in packages) == 1
    matches = package_signs(recognized(tmp_path, **facts))
    assert {s for s in matches if s[0] in {"postgresql", "redis", "nodejs"}} == {
        ("postgresql", "index.docker.io/library/postgres", "compose.yaml", 8),
        ("postgresql", "registry-1.docker.io/bitnami/postgresql", "job.yaml", None),
        ("nodejs", leaf, "Dockerfile", 1),
    }
