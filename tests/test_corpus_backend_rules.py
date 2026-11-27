"""Package declarations behind stack labels in the benchmark corpus and in Daodan itself."""

import json
import sys
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parents[1] / "daodan/core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))
import service_registry  # noqa: E402
import snapshot  # noqa: E402
import technologies  # noqa: E402
from pipeline import Context, Scan, Stack, events  # noqa: E402
from test_codebase_map_stack_recognition import fact, package_signs, recognized  # noqa: E402


@pytest.fixture(scope="module")
def entries():
    return service_registry.load()["entries"]


@pytest.mark.parametrize(("ecosystem", "package", "expected"), [
    # fixtures/jvm-spring-boot-managed/build.gradle.kts lines 21 and 25.
    ("maven", "org.springframework.boot:spring-boot-starter-web", {"spring-boot": "framework"}),
    ("maven", "org.springframework.boot:spring-boot-starter-test", {"spring-boot": "framework"}),
    ("maven", "org.springframework.boot:org.springframework.boot.gradle.plugin", {"spring-boot": "framework"}),
    # quarkusio/quarkus-super-heroes@f2404b0510d0 rest-heroes/pom.xml lines 64 and 110.
    ("maven", "io.quarkus:quarkus-hibernate-reactive-panache",
     {"quarkus": "framework", "hibernate-reactive": "library", "panache": "library"}),
    ("maven", "io.quarkus:quarkus-rest-qute",
     {"quarkus": "framework", "quarkus-rest": "framework", "qute": "library"}),
    ("maven", "tech.jhipster:jhipster-framework", {"jhipster": "tool"}),
    # wger-project/wger@d4cc7d7769e6 pyproject.toml lines 31 and 48.
    ("pypi", "celery", {"celery": "framework"}),
    ("pypi", "djangorestframework", {"django-rest-framework": "framework"}),
    # Daodan's pyproject.toml declares both the parser API and the language pack.
    ("pypi", "tree-sitter", {"tree-sitter": "library"}),
    ("pypi", "tree_sitter_language_pack", {"tree-sitter-language-pack": "library"}),
    # TheAxelander/OpenBudgeteer@48eba0855d63 OpenBudgeteer.Blazor/OpenBudgeteer.Blazor.csproj line 20.
    ("nuget", "MudBlazor", {"blazor": "framework", "mudblazor": "framework"}),
    # ardalis/CleanArchitecture@ecf2f4df8919 src/Clean.Architecture.Web/Clean.Architecture.Web.csproj line 16.
    ("nuget", "FastEndpoints.Swagger", {"fastendpoints": "framework"}),
    # jasontaylordev/CleanArchitecture@57c9d5d4a61a src/AppHost/AppHost.csproj line 12.
    ("nuget", "Aspire.Hosting.JavaScript", {"dotnet-aspire": "framework"}),
    ("nuget", "xunit.v3.mtp-v2", {"xunit": "tool"}),
    ("nuget", "Mono.Cecil", {"mono-cecil": "library"}),  # daodan/core/dynamic/dotnet_record/rewrite/Daodan.Rewrite.csproj
])
def test_declared_backend_package_carries_its_project_category_and_source(real_stack, tmp_path, entries, ecosystem, package, expected):
    found = package_signs(recognized(tmp_path, packages=[fact(ecosystem, package, "manifest#L17", "pre-map@1")]))
    categories = {e["id"]: service_registry.entry_category(e) for e in entries if e["kind"] == "project"}
    for ident, category in expected.items():
        assert (ident, package, "manifest", 17) in found
        assert categories[ident] == category


@pytest.mark.parametrize(("ecosystem", "package", "not_declared"), [
    ("maven", "com.example:spring-boot-starter-web", {"spring-boot"}),
    ("maven", "com.example:org.springframework.boot", {"spring-boot"}),
    ("maven", "com.example:org.springframework.boot.gradle.plugin", {"spring-boot"}),
    ("maven", "com.example:com.android.application", {"android"}),
    ("maven", "org.springframework:spring-context", {"spring-boot"}),
    ("maven", "org.springframework.boot:unrelated", {"spring-boot"}),
    ("pypi", "spring-boot-starter-web", {"spring-boot"}),
    ("maven", "org.springframework.boot:spring-boot-starter-test", {"junit-jupiter", "mockito"}),
    ("maven", "org.springframework.boot:spring-boot-starter-data-jpa", {"hibernate"}),
    ("maven", "org.example:quarkus-rest-qute", {"quarkus", "quarkus-rest", "qute"}),
    ("pypi", "djangorestframework-simplejwt", {"django-rest-framework"}),
    ("pypi", "tree-sitter-language-pack", {"tree-sitter"}),
    ("nuget", "FastEndpoints.SwaggerHelper", {"fastendpoints"}),
    ("nuget", "Microsoft.WindowsAppSDK", {"winui"}),
])
def test_similar_names_and_optional_transitives_do_not_declare_a_backend(real_stack, tmp_path, ecosystem, package, not_declared):
    matches = package_signs(recognized(tmp_path, packages=[fact(ecosystem, package, "manifest#L1", "pre-map@1")]))
    assert not_declared.isdisjoint(ident for ident, *_ in matches)


def test_reader_only_scan_and_stack_identify_spring_boot_in_its_declaring_modules(real_stack, tmp_path):
    root = tmp_path / "project"
    for module, group, artifact in (
        ("api", "org.springframework.boot", "spring-boot-starter-web"),
        ("other", "org.example", "spring-boot-starter-web"),
        ("collision", "org.example", "org.springframework.boot"),
    ):
        folder = root / module
        folder.mkdir(parents=True)
        (folder / "pom.xml").write_text(
            '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
            '  <modelVersion>4.0.0</modelVersion>\n'
            f'  <groupId>example</groupId><artifactId>{module}</artifactId><version>1</version>\n'
            '  <properties><dep.version>3.4.0</dep.version></properties>\n'
            '  <dependencies><dependency>\n'
            f'    <groupId>{group}</groupId>\n'
            f'    <artifactId>{artifact}</artifactId>\n'
            '    <version>${dep.version}</version>\n'
            '  </dependency></dependencies>\n'
            '</project>\n',
            encoding="utf-8",
        )
    worker = root / "worker"
    worker.mkdir()
    (worker / "settings.gradle.kts").write_text('rootProject.name = "worker"\n', encoding="utf-8")
    (worker / "build.gradle.kts").write_text(
        'plugins {\n    id("org.springframework.boot") version "3.4.0"\n}\n', encoding="utf-8")

    manifest = tmp_path / "out" / "manifest.sqlite"
    snapshot.read_project(root, manifest)
    context = Context(manifest, events.Bus(), fast_scan=True)
    Stack.run(context)  # the stack first: its build tools choose the pre-map's sources
    facts = json.loads(Path(Scan.run(context)["premap"]).read_text(encoding="utf-8"))
    record = json.loads(technologies.path(manifest).read_text(encoding="utf-8"))

    packages = {(p["name"], p.get("version"), p["declared_in"]) for p in facts["packages"] if p["ecosystem"] == "maven"}
    assert {
        ("org.springframework.boot:spring-boot-starter-web", "3.4.0", "api/pom.xml#L7"),
        ("org.example:spring-boot-starter-web", "3.4.0", "other/pom.xml#L7"),
        ("org.example:org.springframework.boot", "3.4.0", "collision/pom.xml#L7"),
        ("org.springframework.boot", "3.4.0", "worker/build.gradle.kts#L2"),
    } <= packages
    owners = {tuple(unit["paths"]): unit["technology_evidence"]["spring-boot"]
              for unit in record["units"] if "spring-boot" in unit["frameworks"]}
    assert owners == {
        ("api",): {"path": "api/pom.xml", "line": 7},
        ("worker",): {"path": "worker/build.gradle.kts"},  # the release names the plugin by its marker artifact: no line
    }
