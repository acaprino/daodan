"""The dynamic step's plans for real projects at the commits the corpus pins, from their snapshot and the pre-map's
readers (no runner, no model command), as the step reads them before it runs anything: a real proof on Modal
(tests/modal_pytest.py), which clones each project. D-198 cites it."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "daodan/core"))

import dynamic  # noqa: E402
import premap  # noqa: E402
import snapshot  # noqa: E402
from dynamic import dotnet, javascript  # noqa: E402

PROJECTS = {"eshop": ("https://github.com/dotnet/eShop", "913acea66708a59595351174cee9b29f37179d29"),
            "fastapi": ("https://github.com/fastapi/full-stack-fastapi-template",
                        "aabb90126964a164e02aff39e7c385bb0598236d"),
            "tududi": ("https://github.com/chrisvel/tududi.git", "71da9d7b34dfd1600657e9c5ddf40420206fd263")}


def planned(tmp_path: Path, name: str) -> tuple[dict, list[str], object]:
    """The pre-map of the project `name` at its commit, its files and a reader of them."""
    url, commit = PROJECTS[name]
    source = tmp_path / name
    source.mkdir()
    for command in (["git", "init", "-q"], ["git", "remote", "add", "origin", url],
                    ["git", "fetch", "-q", "--depth", "1", "origin", commit],
                    ["git", "-c", "core.hooksPath=/dev/null", "checkout", "-q", "FETCH_HEAD"]):
        subprocess.run(command, cwd=source, check=True, timeout=600)
    manifest = tmp_path / "snapshot/manifest.sqlite"
    snapshot.read_project(source, manifest)
    files = sorted(path.relative_to(source).as_posix() for path in source.rglob("*")
                   if path.is_file() and ".git" not in path.relative_to(source).parts)

    def read(rel):
        try:
            return (source / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    return premap.ensure(manifest), files, read


ON_MODAL = pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"),
                              reason="a real proof on Modal (tests/modal_pytest.py)")


@ON_MODAL
def test_on_modal_eshop_s_tests_are_five_test_projects_and_the_rest_needs_a_container_engine(tmp_path):
    """eShop: the C# plan is its five MSTest projects, each `dotnet test --project` with no build (the preparation
    builds), and its four functional test projects, Aspire app hosts, are `tests_need_container_engine`; no CI
    step and no service. Its only JavaScript tests, Playwright's `test:e2e`, have the Aspire host as webServer."""
    record, files, read = planned(tmp_path, "eshop")
    csharp = dotnet.plan(record, files, read)
    names = ["Application", "Basket", "ClientApp", "Ordering", "eShop.AppHost"]
    assert [run["project"] for run in csharp["runs"]] == [f"tests/{name}.UnitTests/{name}.UnitTests.csproj"
                                                          for name in names]
    assert all(run["argv"] == ["dotnet", "test", "--project", Path(run["project"]).name, "--no-build"]
               for run in csharp["runs"])
    assert [(gap["kind"], gap["path"]) for gap in csharp["gaps"]] == [
        ("tests_need_container_engine", f"tests/{name}.FunctionalTests/{name}.FunctionalTests.csproj")
        for name in ("Basket", "Catalog", "Ordering", "Webhooks")]
    assert dynamic.ci_steps(record, csharp["runs"])["steps"] == [] and dynamic.services(record)["services"] == []
    js = javascript.plan(record, files, read)
    assert js["runs"] == []
    [gap] = js["gaps"]
    assert (gap["kind"], gap["path"]) == ("tests_need_container_engine", "package.json#scripts.test:e2e")
    assert "playwright.config.ts:87 `dotnet run --project src/eShop.AppHost/eShop.AppHost.csproj`" in gap["detail"]


@ON_MODAL
def test_on_modal_fastapi_s_playwright_tests_run_with_their_web_server(tmp_path):
    """The full-stack FastAPI template: the root `test` (`bun run --filter frontend test`) on npm, the frontend's
    `bunx playwright test`, whose webServer is `bun run dev`, on Playwright; no gap."""
    record, files, read = planned(tmp_path, "fastapi")
    js = javascript.plan(record, files, read)
    assert js["runs"] == [{"root": ".", "runner": "npm", "declared_in": "package.json#scripts.test"},
                          {"root": "frontend", "runner": "playwright",
                           "declared_in": "frontend/package.json#scripts.test"}]
    assert js["gaps"] == []


@ON_MODAL
def test_on_modal_tududi_s_jest_scripts_run(tmp_path):
    """tududi: its two Jest scripts, and no Playwright one: its end-to-end tests start from a shell script."""
    record, files, read = planned(tmp_path, "tududi")
    js = javascript.plan(record, files, read)
    assert js["runs"] == [{"root": ".", "runner": "jest", "declared_in": "package.json#scripts.test"},
                          {"root": ".", "runner": "jest", "declared_in": "package.json#scripts.frontend:test"}]
    assert js["gaps"] == []
