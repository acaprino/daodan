"""Web dependencies and configuration files whose names distinguish different technologies."""
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "daodan/core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))
import snapshot  # noqa: E402
import stack_recognition  # noqa: E402
from test_codebase_map_stack_recognition import fact, package_signs, recognized  # noqa: E402


def test_registry_attributes_the_actual_dependency_to_its_manifest(real_stack, tmp_path):
    # Names taken from the Daodan/Imago manifests, explorer probes and labelled real-project corpus.
    npm = {
        "angular": "angularjs", "@angular/core": "angular", "turbo": "turborepo",
        "@hotwired/turbo": "hotwire-turbo", "@tabler/core": "tabler", "@tabler/icons-react": "tablericons",
        "vite": "vite", "vite-plus": "vite-plus", "@astrojs/compiler": "astro-compiler",
        "@vue/compiler-sfc": "vue-sfc-compiler", "d3-zoom": "d3js", "@acaprino/imago": "imago",
        "@rneui/base": "react-native-elements", "@ts-rest/open-api": "ts-rest", "hyperscript.org": "hyperscript",
        "@xyflow/react": "react-flow", "@likec4/core": "likec4",
        "@types/d3-zoom": None, "hyperscriptXorg": None, "@acaprino/imago-extra": None,
    }
    composer = {"symfony/framework-bundle": "symfony", "symfony/twig-bundle": "twigphp",
                "symfony/stimulus-bundle": "stimulus", "twbs/bootstrap": "bootstrap", "jms/serializer": "jms-serializer"}
    gems = {"capybara": "capybara", "turbo-rails": "hotwire-turbo", "solid_queue": "solid-queue", "rspec-rails": "rspec"}
    manifests = {"client/package.json": npm, "php/composer.json": composer, "ruby/Gemfile": gems}
    project = tmp_path / "project"
    for path, content in {
        "client/package.json": json.dumps({"name": "client", "dependencies": dict.fromkeys(npm, "1.0.0")}),
        "php/composer.json": json.dumps({"name": "sample/app", "require": dict.fromkeys(composer, "^1.0")}),
        "ruby/Gemfile": "\n".join(f'gem "{name}", "~> 1.0"' for name in gems),
    }.items():
        file = project / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")

    manifest = tmp_path / "snapshot/manifest.sqlite"
    snapshot.read_project(project, manifest)
    findings = stack_recognition.run(manifest)["found"]
    actual = {(s["path"], s["value"], item["id"]) for item in findings for s in item["signs"] if s["sign"] == "package"}
    assert actual == {(path, name, entry) for path, names in manifests.items() for name, entry in names.items() if entry}


def test_web_configuration_variants_require_the_exact_basename(real_stack, tmp_path):
    names = {"jest.config.cts": "jest", "nuxt.config.mjs": "nuxtjs", "vite.config.mts": "vite",
             "vitest.config.mts": "vitest", "playwright.config.cts": "playwright", "tailwind.config.cjs": "tailwind",
             "Tauri.toml": "tauri"}
    paths = [f"app/{name}" for name in names] + ["app/jest.config.mjs.txt", "app/my-vite.config.ts"]
    found = recognized(tmp_path, {path: "// configuration\n" for path in paths})["found"]
    assert {(sign["value"], item["id"]) for item in found for sign in item["signs"] if sign["sign"] == "file"} \
        == set(names.items())


def test_webjars_keep_the_maven_group_of_the_frontend_distribution(real_stack, tmp_path):
    names = {"org.webjars:bootstrap": "bootstrap", "org.webjars.npm:bootstrap": "bootstrap",
             "org.webjars.npm:vue": "vue", "org.webjars.npm:vue-router": "vue-router",
             "org.webjars.npm:font-awesome": "fontawesome", "org.webjars.npm:dompurify": "dompurify",
             "org.webjars.npm:marked": "marked"}
    packages = [fact("maven", name, "pom.xml#L1", "pre-map@1") for name in (*names, "com.example:bootstrap", "com.example:vue")]
    found = package_signs(recognized(tmp_path, packages=packages))
    assert {(name, entry) for entry, name, _, _ in found} == set(names.items())
