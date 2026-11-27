"""The preparation's dependency restores: each package manager's own command, run in Daodan's container.

The answers are in `tests/fixtures/premap/restore/<manager>.json`, recorded once in a real container from the
projects beside them (`tests/fixtures/premap/restore/<manager>/`): `good` restores, `bad` names a package no
registry has.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "daodan/core"))

import preparation  # noqa: E402

ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "restore"


def recorded(manager):
    stored = json.loads((ANSWERS / f"{manager}.json").read_text(encoding="utf-8"))
    assert stored["line"] == preparation.restore(manager, ["good", "bad"]), "the recorded line is not the current one"
    return stored["result"]


def test_gradle_resolves_every_configuration_and_a_package_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("gradle")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "gradle", "bad")]
    assert "org.example.missing:nothing:9.9.9" in gaps[0]["detail"]


def test_maven_goes_offline_and_a_package_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("maven")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "maven", "bad")]
    assert "org.example.missing:nothing" in gaps[0]["detail"]


def test_a_restore_runs_where_the_build_starts_and_its_hosts_are_declared_once():
    files = ["settings.gradle", "app/build.gradle", "lib/build.gradle", "tools/x/build.gradle.kts", "pom.xml",
             "core/pom.xml", "other/pom.xml"]
    assert preparation.restores(files) == {"gradle": ["."], "maven": ["."]}
    assert preparation.restores(["a/pom.xml", "b/pom.xml", "b/c/pom.xml"]) == {"maven": ["a", "b"]}
    assert set(preparation.RESTORES["gradle"]["hosts"]) >= {"plugins.gradle.org", "services.gradle.org"}


def test_a_nested_folder_with_npm_s_own_lockfile_is_a_restore_of_its_own():
    """A root with independent apps below, each with its own manifest and lockfile (no workspaces): every one is
    restored, whichever of npm's two lockfile names it has."""
    for lock in ("package-lock.json", "npm-shrinkwrap.json"):
        files = ["package.json", "package-lock.json", "admin-app/package.json", f"admin-app/{lock}",
                 "scripts/docs/package.json", f"scripts/docs/{lock}"]
        assert preparation.restores(files) == {"npm": [".", "admin-app", "scripts/docs"]}
        assert preparation.node_restores(files) == [("npm", [".", "admin-app", "scripts/docs"], False)]


def test_a_nested_folder_with_a_pnpm_or_yarn_lockfile_is_a_restore_of_its_own_with_that_manager():
    files = ["package.json", "package-lock.json", "web/package.json", "web/pnpm-lock.yaml"]
    assert preparation.restores(files) == {"npm": ["."], "pnpm": ["web"]}
    assert preparation.restores([*files[:3], "web/yarn.lock"]) == {"npm": ["."], "yarn": ["web"]}


def test_a_workspace_member_is_restored_from_the_root_only_beside_a_nested_project_with_a_lockfile():
    manifests = {"package.json": {"name": "root", "workspaces": ["packages/*"]}, "package-lock.json": {},
                 "packages/ui/package.json": {"name": "ui", "dependencies": {"ms": "2.1.3"}},
                 "admin/package.json": {"name": "admin", "dependencies": {"ms": "2.1.3"}}, "admin/package-lock.json": {}}
    plan = preparation.node_prepare(list(manifests), lambda rel: json.dumps(manifests[rel]))
    assert plan["restores"] == {"npm": [".", "admin"]} and plan["gaps"] == []


def test_a_member_a_workspace_names_is_restored_by_the_root_only_even_with_a_lockfile_of_its_own():
    """A leftover `package-lock.json` in a member: the folder above names it, so the root installs it."""
    manifests = {"package.json": {"name": "root", "workspaces": ["packages/*"]}, "package-lock.json": {},
                 "packages/ui/package.json": {"name": "ui", "dependencies": {"ms": "2.1.3"}},
                 "packages/ui/package-lock.json": {},
                 "admin/package.json": {"name": "admin", "dependencies": {"ms": "2.1.3"}}, "admin/package-lock.json": {}}
    plan = preparation.node_prepare(list(manifests), lambda rel: json.dumps(manifests[rel]))
    assert plan["restores"] == {"npm": [".", "admin"]} and plan["gaps"] == []


def prepared(manifests: dict) -> dict:
    return preparation.node_prepare(list(manifests), lambda rel: manifests[rel] if isinstance(manifests[rel], str)
                                    else json.dumps(manifests[rel]))


UI = {"packages/ui/package.json": {"name": "ui", "dependencies": {"ms": "2.1.3"}}}
PNPM_PACKAGES = "packages:\n  - 'packages/*'\n"


def test_a_workspace_names_its_members_where_the_manager_that_restores_the_root_reads_them():
    """pnpm reads `pnpm-workspace.yaml` and ignores the manifest's `workspaces`; npm and Yarn read `workspaces` and
    ignore the yaml: a declaration the manager does not read installs nothing, so the member is restored on its own."""
    # an npm root and a yaml naming `packages/*`: `npm ci` at the root installs no member
    plan = prepared({"package.json": {"name": "root"}, "package-lock.json": {}, "pnpm-workspace.yaml": PNPM_PACKAGES,
                     **UI, "packages/ui/package-lock.json": {}})
    assert plan["restores"] == {"npm": [".", "packages/ui"]} and plan["gaps"] == []
    # a pnpm root and `workspaces` in the manifest only
    plan = prepared({"package.json": {"name": "root", "workspaces": ["packages/*"]}, "pnpm-lock.yaml": "",
                     **UI, "packages/ui/pnpm-lock.yaml": ""})
    assert plan["restores"] == {"pnpm": [".", "packages/ui"]} and plan["gaps"] == []
    # each manager with the declaration it reads: the root installs the member
    plan = prepared({"package.json": {"name": "root"}, "pnpm-lock.yaml": "", "pnpm-workspace.yaml": PNPM_PACKAGES,
                     **UI, "packages/ui/pnpm-lock.yaml": ""})
    assert plan["restores"] == {"pnpm": ["."]} and plan["gaps"] == []
    # a member with no lockfile, which no declaration the root's manager reads names, is a gap, not an install
    plan = prepared({"package.json": {"name": "root"}, "package-lock.json": {}, "pnpm-workspace.yaml": PNPM_PACKAGES, **UI})
    assert plan["restores"] == {"npm": ["."]}
    assert [(g["kind"], g["manager"], g["path"]) for g in plan["gaps"]] == [("restore_failed", "npm", "packages/ui")]
    # `workspaces` as an object: its `packages` are the patterns
    plan = prepared({"package.json": {"name": "root", "workspaces": {"packages": ["packages/*"]}}, "package-lock.json": {},
                     **UI})
    assert plan["restores"] == {"npm": ["."]} and plan["gaps"] == []


def test_a_workspace_root_an_outer_workspace_installs_names_no_members_of_its_own():
    """`ui` is a member of the root, and `ui` itself declares `examples/*`: the root's install does not read that, so
    `demo`, with a lockfile of its own, is restored on its own, from the outermost folder inward."""
    plan = prepared({"package.json": {"name": "root", "workspaces": ["packages/*"]}, "package-lock.json": {},
                     "packages/ui/package.json": {"name": "ui", "workspaces": ["examples/*"],
                                                  "dependencies": {"ms": "2.1.3"}},
                     "packages/ui/package-lock.json": {},
                     "packages/ui/examples/demo/package.json": {"name": "demo", "dependencies": {"ms": "2.1.3"}},
                     "packages/ui/examples/demo/package-lock.json": {}})
    assert plan["restores"] == {"npm": [".", "packages/ui/examples/demo"]} and plan["gaps"] == []
    # the root's own declaration still reaches a member below a folder that is not a member itself
    plan = prepared({"package.json": {"name": "root", "workspaces": ["packages/**"]}, "package-lock.json": {},
                     "packages/ui/package.json": {"name": "ui", "workspaces": ["examples/*"],
                                                  "dependencies": {"ms": "2.1.3"}},
                     "packages/ui/package-lock.json": {},
                     "packages/ui/examples/demo/package.json": {"name": "demo", "dependencies": {"ms": "2.1.3"}},
                     "packages/ui/examples/demo/package-lock.json": {}})
    assert plan["restores"] == {"npm": ["."]} and plan["gaps"] == []


def test_a_stated_jdk_with_a_suffix_counts_at_its_number_for_the_one_a_build_asks_for():
    """`21-ea` and `21-open` are JDK 21 to both parsers of a version: the build asks for 21, the project states it."""
    from indexers import jvm
    for version in ("21-ea", "21-open", "21.0.2", "21"):
        stated = [{"tool": "java", "version": version, "declared_in": "build.gradle#x"}]
        assert preparation.jdk_named(21, "languageVersion=21", stated) == (stated[0], None), version
        assert jvm._major(version) == preparation.jdk_major(version) == 21
    assert [jvm._major(v) for v in ("1.8", "8", "1", "v21", "", None)] == [
        preparation.jdk_major(v) for v in ("1.8", "8", "1", "v21", "", None)] == [8, 8, 1, None, None, None]


JETBRAINS_21 = {"tool": "java", "version": "21", "vendor": "JETBRAINS",
                "declared_in": "gradle/gradle-daemon-jvm.properties#toolchainVersion"}
CATALOG = json.loads((ANSWERS.parent / "mise-java-vendors.json").read_text(encoding="utf-8"))["vendors"]


def test_a_jdk_of_a_vendor_is_installed_by_mise_under_the_vendor_s_name_with_the_hosts_it_reaches():
    got = preparation.toolchains([JETBRAINS_21])
    lines = "\n".join(got["lines"])
    assert got["gaps"] == []
    assert " install java@jetbrains-21 " in lines and "DAODAN-MISSING java@jetbrains-21" in lines
    assert {"mise-java.jdx.dev", "cache-redirector.jetbrains.com", "d2xrhe97vsfxuc.cloudfront.net"} <= set(got["hosts"])
    plain = "\n".join(preparation.toolchains([{k: v for k, v in JETBRAINS_21.items() if k != "vendor"}])["lines"])
    assert " install java@21 " in plain and "jetbrains" not in plain  # no vendor: mise's default, as before


def test_every_vendor_the_table_maps_is_one_mise_lists_and_every_host_its_download_reached_is_declared():
    """`tests/fixtures/premap/mise-java-vendors.json`: mise's catalog (mise-java.jdx.dev) and the hosts one JDK 21
    archive of each vendor was fetched through, redirects followed."""
    mapped = {name: row for name, row in preparation.JDK_VENDORS.items() if row["mise"]}
    assert len(mapped) == 11
    for name, row in mapped.items():
        got = preparation.toolchains([{**JETBRAINS_21, "vendor": name}])
        assert row["mise"] in CATALOG, name
        assert set(CATALOG[row["mise"]]["reached"]) <= set(got["hosts"]), name
        assert f" install java@{row['mise']}-21 " in "\n".join(got["lines"]), name


def test_a_vendor_mise_has_no_jdk_of_is_a_gap_naming_the_vendor_and_the_version_and_installs_nothing():
    for vendor in ("APPLE", "ADOPTOPENJDK", "HEWLETT_PACKARD", "vendor matching('Acme')"):
        got = preparation.toolchains([{**JETBRAINS_21, "vendor": vendor}])
        assert (got["files"], got["lines"], got["hosts"]) == ([], [], ()), vendor
        [gap] = got["gaps"]
        assert (gap["kind"], gap["tool"], gap["version"], gap["vendor"]) == ("toolchain_unavailable", "java", "21", vendor)
        assert vendor in gap["detail"] and "21" in gap["detail"]
        assert gap["path"] == JETBRAINS_21["declared_in"]


def test_the_jdk_a_build_names_with_a_vendor_is_asked_for_with_that_vendor_through_the_one_function():
    said = "languageVersion=21, vendor=JetBrains"
    item, gap = preparation.jdk_named(21, said, [], "the build", "JetBrains")  # as Gradle prints it
    assert item == {"tool": "java", "version": "21", "vendor": "JETBRAINS", "declared_in": "the build's error"}
    assert "JetBrains" in gap["detail"] and "21" in gap["detail"]
    other = {"tool": "java", "version": "21", "declared_in": "build.gradle#x"}  # states 21, of no vendor in particular
    assert preparation.jdk_named(21, said, [other], "the build", "JetBrains")[0]["vendor"] == "JETBRAINS"
    stated = {**other, "vendor": "JETBRAINS"}
    assert preparation.jdk_named(21, said, [other, stated], "the build", "JetBrains") == (stated, None)
    for words in (None, "any vendor", "any"):  # Gradle prints `vendor=any vendor` when the build names none
        assert preparation.jdk_named(21, "languageVersion=21", [], "the build", words)[0] == {
            "tool": "java", "version": "21", "declared_in": "the build's error"}, words
    unknown = preparation.jdk_named(21, said, [], "the build", "vendor matching('Acme')")[0]
    assert unknown["vendor"] == "vendor matching('Acme')"  # what Gradle printed: `toolchains` makes it a gap


def test_a_nested_package_no_workspace_names_and_no_lockfile_of_its_own_stays_a_gap_not_an_install():
    """The owner's rule is every project at any depth, but a folder with no lockfile that no workspace names is not
    restored on its own: it may be a publish manifest (js-angular's `projects/ui-kit`) or a test fixture; a Lerna
    package is its root's `lerna bootstrap`'s (below)."""
    manifests = {"package.json": {"name": "root"}, "package-lock.json": {},
                 "landing/package.json": {"name": "landing", "dependencies": {"ms": "2.1.3"}}}
    plan = preparation.node_prepare(list(manifests), lambda rel: json.dumps(manifests[rel]))
    assert plan["restores"] == {"npm": ["."]}
    assert [(g["kind"], g["path"]) for g in plan["gaps"]] == [("restore_failed", "landing")]


def test_every_restore_line_reports_its_failure_and_the_run_goes_on():
    for manager in preparation.RESTORES:
        line = preparation.restore(manager, ["x"])
        assert "DAODAN-RESTORE-FAILED" in line and line.endswith("true"), manager


def test_npm_installs_without_scripts_and_a_package_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("npm")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "npm", "bad")]
    assert "@example-missing/nothing" in gaps[0]["detail"]


def test_pnpm_installs_from_its_lockfile_and_one_out_of_date_is_a_gap():
    gaps = preparation.restore_gaps(recorded("pnpm")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "pnpm", "bad")]
    assert "OUTDATED_LOCKFILE" in gaps[0]["detail"]


@pytest.mark.skipif(not os.environ.get("MODAL_TASK_ID"), reason="a real pnpm, on Modal (tests/modal_pytest.py)")
@pytest.mark.parametrize("pnpm", [None, "9.15.9", "10.34.9", "11.29.0", "12.23.0"])
def test_pnpm_s_restore_of_a_dependency_with_a_build_script_left_unrun_is_no_gap(tmp_path, monkeypatch, pnpm):
    """hono-open-api-starter: pnpm 11 and later end an install that leaves a dependency's build script unrun with
    ERR_PNPM_IGNORED_BUILDS (`strictDepBuilds`, pnpm.io/settings/build), the packages installed. The restore runs
    without scripts on purpose, so the line turns that setting off: each pnpm installs, none is a gap; without the
    setting, pnpm 11 and later fail (`None`: the pnpm corepack takes when the project names none)."""
    import subprocess
    monkeypatch.setattr(preparation, "LOG", str(tmp_path / "restore.log"))
    work = tmp_path / "app"
    work.mkdir()
    manifest = {"name": "app", "version": "1.0.0", "dependencies": {"core-js": "3.38.1"}}  # a postinstall script
    if pnpm:
        manifest["packageManager"] = f"pnpm@{pnpm}"
    (work / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
    node = Path(shutil.which("node")).resolve().parent  # corepack ships beside Node
    env = {**os.environ, "PATH": f"{node}:{os.environ['PATH']}", "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0",
           "COREPACK_HOME": str(tmp_path / "corepack")}

    def run(line):
        return subprocess.run(["sh", "-c", line], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300)

    locked = run("cd app && corepack pnpm install --lockfile-only --ignore-scripts")
    assert locked.returncode == 0, locked.stdout + locked.stderr
    version = run("cd app && corepack pnpm --version").stdout.strip()
    line = preparation.restore("pnpm", ["app"])
    done = run(line)
    assert preparation.restore_gaps(done.stderr) == [], (version, done.stderr)
    assert (work / "node_modules" / "core-js" / "package.json").is_file()
    if int(version.split(".")[0]) >= 11:  # the case: the line without the setting fails
        (work / "node_modules").rename(tmp_path / "installed")
        [gap] = preparation.restore_gaps(run(line.replace(" --config.strict-dep-builds=false", "")).stderr)
        assert "ERR_PNPM_IGNORED_BUILDS" in gap["detail"], (version, gap)


def test_yarn_installs_from_its_lockfile_and_one_out_of_date_is_a_gap():
    gaps = preparation.restore_gaps(recorded("yarn")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "yarn", "bad")]
    assert "lockfile" in gaps[0]["detail"].lower()


FAKE_NPM = """#!/bin/sh
echo "npm $*" >> "$CALLS"
[ -n "${REFUSE:-}" ] && { echo "npm error code EBADENGINE" >&2; exit 1; }
while [ $# -gt 0 ]; do [ "$1" = --prefix ] && prefix=$2; shift; done
mkdir -p "$prefix/bin" && printf '#!/bin/sh\\necho "installed corepack $*" >> "$CALLS"\\n' > "$prefix/bin/corepack"
chmod 755 "$prefix/bin/corepack"
"""


def test_pnpm_and_yarn_run_a_corepack_with_npms_current_key_and_none_installed_is_a_gap(tmp_path):
    """mix-infra-gha on Node 20.18.1: the corepack a Node ships may predate npm's registry key of January 2025
    ("Cannot find matching keyid"), and from Node 25 none ships. The line installs one with the Node's own npm,
    apart and first on the path, from 0.31.0, the first release with that key; npm takes the newest whose engines
    take that Node. When npm installs none, the Node's own corepack runs and the preparation names what it lacks."""
    import os
    import subprocess
    programs = tmp_path / "programs"
    programs.mkdir()
    for name, text in (("npm", FAKE_NPM), ("corepack", '#!/bin/sh\necho "bundled corepack $*" >> "$CALLS"\n')):
        (programs / name).write_text(text, encoding="utf-8", newline="\n")
        (programs / name).chmod(0o755)
    (tmp_path / "web").mkdir()
    plan = preparation.node_prepare(["web/package.json", "web/pnpm-lock.yaml"], lambda rel: "{}")
    for refuse in ("", "1"):
        tools, calls = tmp_path / f"tools{refuse}", tmp_path / f"calls{refuse}"
        done = subprocess.run(["sh", "-c", plan["lines"][0].replace(preparation.T, str(tools))], cwd=tmp_path,
                              env={**os.environ, "PATH": f"{programs}:{os.environ['PATH']}", "CALLS": str(calls),
                                   "REFUSE": refuse}, capture_output=True, text=True, timeout=60)
        ran = calls.read_text(encoding="utf-8").splitlines()
        assert ran[0] == (f"npm install -g --prefix {tools}/corepack --engine-strict --no-audit --no-fund"
                          " --loglevel=error corepack@>=0.31.0 <=0.36.0")
        assert ran[1:] == [f"{'bundled' if refuse else 'installed'} corepack pnpm install --frozen-lockfile"
                          " --config.strict-dep-builds=false"]
        assert preparation.missing(done.stderr) == ([{
            "kind": "toolchain_unavailable", "tool": "corepack", "version": ">=0.31.0",
            "detail": "corepack >=0.31.0: the preparation could not install it (its output is in the run's log)"}]
            if refuse else [])
    # npm comes with Node: its restore needs no corepack.
    assert "corepack" not in preparation.node_prepare(["package.json"], lambda rel: "{}")["lines"][0]


def test_one_node_folder_has_one_manager_its_lockfile_names():
    """A workspace's members restore with its root, whatever manager the root uses; a folder with its own
    lockfile is a project of its own."""
    assert preparation.restores(["package.json", "pnpm-lock.yaml", "packages/a/package.json"]) == {"pnpm": ["."]}
    files = ["package.json", "packages/a/package.json", "web/package.json", "web/pnpm-lock.yaml",
             "site/package.json", "site/yarn.lock"]
    assert preparation.restores(files) == {"npm": ["."], "pnpm": ["web"], "yarn": ["site"]}


def test_uv_syncs_its_lockfile_and_one_out_of_date_is_a_gap():
    gaps = preparation.restore_gaps(recorded("uv")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "uv", "bad")]
    assert "needs to be updated" in gaps[0]["detail"]


def test_poetry_installs_its_lockfile_and_one_out_of_date_is_a_gap():
    gaps = preparation.restore_gaps(recorded("poetry")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "poetry", "bad")]
    assert "poetry.lock" in gaps[0]["detail"]


def test_pip_requirements_install_into_a_separate_environment_and_a_missing_package_is_a_gap():
    gaps = preparation.restore_gaps(recorded("pip")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "pip", "bad")]
    assert "example-missing-nothing" in gaps[0]["detail"]


# uv's words, as uv 0.11.28 writes them: a requirement it could not get, with each cause on a line of its own, and
# an index it could not reach.
UV_GIT = ("  × Failed to download and build `mylib @\n  │ git+https://github.com/example/mylib.git@v1.4.0`\n"
          "  ├─▶ Git operation failed\n  ╰─▶ Git executable not found. Ensure that Git is installed and available.\n")
UV_INDEX = ("error: Request failed after 3 retries in 6.6s\n"
            "  Caused by: Failed to fetch: `https://pypi.example.org/simple/gunicorn/`\n")
FAKE_UV = """#!/bin/sh
echo "uv $*" >> "$CALLS"
case "$*" in
  venv*) exit 0;;
  *--overrides*|*--no-install-package*) [ -f "$AGAIN" ] || exit 0; cat "$AGAIN" >&2; exit 1;;
esac
cat "$FIRST" >&2; exit 1
"""


def test_a_python_folder_whose_install_fails_is_installed_again_without_its_vcs_requirements(tmp_path):
    """py-requirements-includes: a CI fetches a VCS requirement from the host its URL names, so the preparation
    reaches exactly those hosts, read from the URLs the Python manifests declare. One it still cannot get (git, a
    refused host, a ref) costs that requirement only: a folder whose install fails is installed again without the
    VCS requirements, and uv's words name the requirement and its cause. A folder that fails again keeps both
    installs' words; with no VCS requirement the install runs once."""
    import os
    import subprocess
    texts = {"requirements/base.txt": "click==8.1.7\nmylib @ git+https://github.com/example/mylib.git@v1.4.0\n"
                                      "-e git+https://gitlab.com/acme/tool.git@main#egg=acme-tool\n",
             "pyproject.toml": '[tool.uv.sources]\nfast = { git = "https://git.example.org/fast", tag = "v1" }\n',
             "docs/notes.txt": "x @ git+https://elsewhere.example.com/x\n"}
    assert preparation.python_vcs(sorted(texts), texts.get) == {
        "names": ["acme-tool", "fast", "mylib"], "hosts": ["git.example.org", "github.com", "gitlab.com"]}
    programs, state = tmp_path / "programs", tmp_path / "state"
    for folder in (programs, state, tmp_path / "a"):
        folder.mkdir()
    (programs / "uv").write_text(FAKE_UV, encoding="utf-8", newline="\n")
    (programs / "uv").chmod(0o755)
    (tmp_path / "first").write_text(UV_GIT, encoding="utf-8")
    (tmp_path / "again").write_text(UV_INDEX, encoding="utf-8")

    def restore(manager, names, again=False):
        calls = tmp_path / f"calls-{manager}-{len(names)}-{again}"
        script = "\n".join([*([preparation.without(names)] if names else []), preparation.restore(manager, ["a"])])
        script = script.replace(preparation.LOG, str(tmp_path / "restore.log")).replace(preparation.STATE, str(state))
        done = subprocess.run(["sh", "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=60,
                              env={**os.environ, "PATH": f"{programs}:{os.environ['PATH']}", "CALLS": str(calls),
                                   "FIRST": str(tmp_path / "first"), "AGAIN": str(tmp_path / ("again" if again
                                                                                           else "none"))})
        (state / preparation.WITHOUT.rsplit("/", 1)[1]).unlink(missing_ok=True)
        return calls.read_text(encoding="utf-8").splitlines(), preparation.restore_gaps(done.stderr)

    calls, [gap] = restore("pip", ["mylib"])
    without = f"{state}/{preparation.WITHOUT.rsplit('/', 1)[1]}"
    assert calls[-2:] == [f"uv pip install -q --python {state}/venvs/a -r pyproject.toml",
                          f"uv pip install -q --python {state}/venvs/a -r pyproject.toml --overrides {without}"]
    assert gap["kind"] == "vcs_not_installed" and gap["manager"] == "pip" and gap["path"] == "a"
    assert "mylib @ | │ git+https://github.com/example/mylib.git@v1.4.0`" in gap["detail"]
    assert "Git executable not found" in gap["detail"]
    _calls, [gap] = restore("pip", ["mylib"], again=True)
    assert gap["kind"] == "restore_failed" and "mylib @" in gap["detail"] and "pypi.example.org" in gap["detail"]
    calls, [gap] = restore("pip", [])
    assert len(calls) == 2 and gap["kind"] == "restore_failed" and "mylib @" in gap["detail"]
    calls, [gap] = restore("uv", ["acme-tool", "mylib"])
    assert calls[-1].endswith("uv sync --locked --all-packages --no-install-project"
                              " --no-install-package acme-tool --no-install-package mylib")
    assert gap["kind"] == "vcs_not_installed" and gap["manager"] == "uv" and "mylib @" in gap["detail"]


def test_vcs_requirements_are_read_by_each_manifest_s_own_reader():
    """T3.A.8a: pip's parser for requirements files and setup.py's strings, `packaging` for PEP 508 lists, `tomllib`
    for uv's and Poetry's `git` sources, `configparser` for setup.cfg: a URL in a comment or a string that is no
    requirement names nothing, an editable path with extras is no VCS requirement."""
    texts = {
        "requirements.txt": "# old @ git+https://comment.example.com/old\n-e ./libs/a[extra]\n"
                            "tool @ git+ssh://git@gitlab.com/acme/tool.git ; python_version >= '3.9'\n"
                            "git+https://hg.example.org/pkg.git#egg=pkg\n",
        "pyproject.toml": '[project]\ndependencies = ["a @ git+https://pep621.example.com/a"]\n'
                          '[project.optional-dependencies]\nx = ["b @ git+https://extra.example.com/b"]\n'
                          '[dependency-groups]\ndev = ["c @ git+https://group.example.com/c", {include-group = "x"}]\n'
                          '[tool.uv.sources]\nd = [{ git = "https://uv.example.com/d", marker = "sys_platform == \'linux\'" }]\n'
                          '[tool.poetry.dependencies]\ne = { git = "https://poetry.example.com/e.git", branch = "main" }\n'
                          '[tool.poetry.group.test.dependencies]\nf = { git = "https://group.poetry.example.com/f" }\n'
                          'description = "not @ git+https://nowhere.example.com/x"\n',
        "svc/setup.cfg": "[options]\ninstall_requires =\n    g @ git+https://cfg.example.com/g\n    requests>=2\n"
                         "[options.extras_require]\nh = h @ git+https://cfg-extra.example.com/h\n",
        "lib/setup.py": 'from setuptools import setup\n# i @ git+https://comment.example.com/i\n'
                        'setup(name="lib", install_requires=["i @ git+https://setup.example.com/i", "Programming :: x"])\n',
        "lib/broken/setup.py": "setup(\n",
    }
    assert preparation.python_vcs(sorted(texts), texts.get) == {
        "names": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "pkg", "tool"],
        "hosts": ["cfg-extra.example.com", "cfg.example.com", "extra.example.com", "gitlab.com", "group.example.com",
                  "group.poetry.example.com", "hg.example.org", "pep621.example.com", "poetry.example.com",
                  "setup.example.com", "uv.example.com"]}


def test_the_preparation_reaches_the_hosts_the_project_declares_and_names_one_that_does_not_answer():
    """As a CI, the preparation reaches the hosts a project declares for its dependencies (the pre-map's
    `registries`: an index, a repository, a feed, a VCS host) and no other; github.com brings the hosts GitHub serves
    its downloads from, where npm fetches a GitHub dependency. A failed restore whose words name a declared host it
    could not reach is a gap naming the host and the files that declare it."""
    record = {"units": [
        {"root": ".", "kind": "npm-package", "manifest": "package.json",
         "registries": ["ssh://github.com", "https://npm.corp.example"]},
        {"root": "svc", "kind": "python-project", "manifest": "svc/requirements.txt",
         "registries": ["https://pypi.example.org", "https://npm.corp.example:8443"]},
        {"root": "lib", "kind": "maven-module", "manifest": "lib/pom.xml"}]}
    declared = preparation.declared(record)
    assert declared["hosts"] == tuple(sorted({*preparation.GITHUB, "npm.corp.example", "pypi.example.org"}))
    assert declared["where"]["npm.corp.example"] == ["package.json", "svc/requirements.txt"]
    assert declared["where"]["codeload.github.com"] == ["package.json"]  # where GitHub serves github.com's tarballs
    assert preparation.declared({"units": [{"root": ".", "kind": "go-module"}]}) == {"hosts": (), "where": {}}
    stderr = ("DAODAN-RESTORE-FAILED pip svc\nerror: Request failed after 3 retries\n"
              "  Caused by: Failed to fetch: `https://pypi.example.org/simple/acme/`\n  Caused by: dns error\n"
              "DAODAN-RESTORE-END\nDAODAN-RESTORE-FAILED npm .\n"
              "npm error 404 Not Found - GET https://npm.corp.example/acme - Not found\nDAODAN-RESTORE-END\n")
    [gap] = preparation.unreached(preparation.restore_gaps(stderr), declared)
    assert (gap["kind"], gap["host"], gap["declared_in"], gap["path"]) == (
        "host_unreachable", "pypi.example.org", ["svc/requirements.txt"], "svc")
    assert "dns error" in gap["detail"] and "svc/requirements.txt" in gap["detail"]  # a 404 answered: no such gap


def test_one_python_folder_has_one_manager_its_lockfile_names():
    files = ["pyproject.toml", "uv.lock", "packages/a/pyproject.toml", "svc/pyproject.toml", "svc/poetry.lock",
             "tools/requirements.txt"]
    assert preparation.restores(files) == {"uv": ["."], "poetry": ["svc"], "pip": ["tools"]}  # a requirements file: its own (T1.B.9d)
    assert preparation.restores(["tools/requirements.txt", "api/pyproject.toml"]) == {"pip": ["api", "tools"]}


def test_a_restore_names_what_it_needs_from_the_preparation():
    assert preparation.RESTORES["uv"]["needs"] == ["uv"] and preparation.RESTORES["poetry"]["needs"] == ["poetry"]
    assert all(n in preparation.NEEDS for spec in preparation.RESTORES.values() for n in spec.get("needs", ()))


def test_go_downloads_each_module_and_one_no_proxy_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("go")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "go", "bad")]
    assert "example.com/missing" in gaps[0]["detail"]


def test_cargo_fetches_the_crates_and_one_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("cargo")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "cargo", "bad")]
    assert "example-missing-nothing" in gaps[0]["detail"]


def test_every_go_module_restores_on_its_own_and_a_cargo_workspace_from_its_root():
    files = ["go.mod", "tools/go.mod", "Cargo.toml", "crates/a/Cargo.toml"]
    assert preparation.restores(files) == {"go": [".", "tools"], "cargo": ["."]}


def test_dotnet_restores_the_solution_or_the_project_and_a_package_no_feed_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("dotnet")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "dotnet", "bad")]
    assert "Example.Missing.Nothing" in gaps[0]["detail"]


def test_a_dotnet_solution_restores_the_projects_below_it():
    files = ["App.sln", "src/App/App.csproj", "tests/T/T.fsproj", "tools/x/x.csproj"]
    assert preparation.restores(files) == {"dotnet": ["."]}
    assert preparation.restores(["a/A.csproj", "b/B.vbproj"]) == {"dotnet": ["a", "b"]}


# What `dotnet` does in a folder whose solution lists a project that needs a workload the container lacks: the
# solution's restore fails whole and restores nothing; each project restores on its own, but that one.
FAKE_DOTNET = r"""#!/bin/sh
echo "dotnet $*" >> "$CALLS"
case "$*" in
  "restore App.slnx") echo "Maui.csproj : error NETSDK1147: the following workloads must be installed: maui-tizen"
                      exit 1;;
  "sln App.slnx list") printf '%s\n' 'Project(s)' '----------' 'src\App\App.csproj' 'src\Maui\Maui.csproj';;
  "restore src/App/App.csproj") echo "Restored src/App/App.csproj";;
  *) echo "$2 : error NETSDK1147: the following workloads must be installed: maui-android"; exit 1;;
esac
"""


def test_a_dotnet_solution_that_does_not_restore_restores_each_of_its_projects_and_stays_a_gap(tmp_path, monkeypatch):
    """eShop: one project of the solution needs a workload the container lacks (NETSDK1147), and the solution's
    restore restores nothing; each project the solution lists is then restored on its own, and the failure stays
    a gap with the error lines of both."""
    import os
    import subprocess
    # A log of its own: `preparation.LOG` is one file of the host's /tmp, which pytest's workers share. Another
    # test's line truncating it while this one writes left NUL bytes in it, and grep said only "binary file matches".
    monkeypatch.setattr(preparation, "LOG", str(tmp_path / "restore.log"))
    tools, work, calls = tmp_path / "bin", tmp_path / "work", tmp_path / "calls.txt"
    for folder in (tools, work):
        folder.mkdir()
    (tools / "dotnet").write_text(FAKE_DOTNET, encoding="utf-8", newline="\n")
    (tools / "dotnet").chmod(0o755)
    (work / "App.slnx").write_text("<Solution />\n", encoding="utf-8")
    done = subprocess.run(["bash", "-c", preparation.restore("dotnet", ["."])], cwd=work, capture_output=True,
                          text=True, env={**os.environ, "PATH": f"{tools}:{os.environ['PATH']}", "CALLS": str(calls)})
    assert calls.read_text(encoding="utf-8").splitlines() == [
        "dotnet restore App.slnx", "dotnet sln App.slnx list", "dotnet restore src/App/App.csproj",
        "dotnet restore src/Maui/Maui.csproj"]
    [gap] = preparation.restore_gaps(done.stderr)
    assert (gap["kind"], gap["manager"], gap["path"]) == ("restore_failed", "dotnet", ".")
    assert "maui-tizen" in gap["detail"] and "src/Maui/Maui.csproj : error NETSDK1147" in gap["detail"]


# What Google's sdkmanager does here: it accepts the licences it is answered `y` to, and installs a package only
# then, into its folder under the SDK (two folders above its own `bin`), its progress redrawn on one line.
FAKE_SDKMANAGER = """#!/bin/sh
sdk=$(cd "$(dirname "$0")/../../.." && pwd)
echo "sdkmanager $*" >> "$CALLS"
if [ "$1" = --licenses ]; then read answer && [ "$answer" = y ] && mkdir -p "$sdk/licenses"; exit $?; fi
[ -d "$sdk/licenses" ] || { echo "Warning: License for package $1 not accepted."; exit 1; }
printf 'Loading package information...\\r[=   ] 3%% Fetch remote repository...\\r'
case "$1" in *android-99*) echo "Warning: Failed to find package '$1'"; exit 1;; esac
mkdir -p "$sdk/$(printf %s "$1" | tr ';' /)"
"""


def test_android_installs_exactly_the_packages_the_build_states_and_one_it_cannot_is_a_gap(tmp_path):
    """jvm-android-app-lib: the Android plugin needs the platform of its `compileSdk` and its build tools. Google's
    command-line tools, verified, are unpacked where Google's layout puts them; their licences are accepted as a CI
    accepts them, then sdkmanager installs each package the pre-map states, once; one it cannot install names
    the package and sdkmanager's own words, and the preparation goes on."""
    import os
    import subprocess
    import zipfile
    programs, tools, carried = tmp_path / "programs", tmp_path / "tools", tmp_path / "in"
    for folder in (programs, carried):
        folder.mkdir()
    with zipfile.ZipFile(carried / "cmdline-tools.zip", "w") as archive:  # as Google's zip: no file modes kept
        archive.writestr("cmdline-tools/bin/sdkmanager", FAKE_SDKMANAGER)
    (programs / "jar").write_text('#!/bin/sh\n[ "$1" = xf ] && exec python3 -c "import sys, zipfile;'
                                  ' zipfile.ZipFile(sys.argv[1]).extractall()" "$2"\n', encoding="utf-8", newline="\n")
    (programs / "jar").chmod(0o755)
    stated = [{"tool": "android-sdk", "version": "35", "declared_in": "app/build.gradle.kts#android.compileSdk"},
              {"tool": "android-sdk", "version": "35", "declared_in": "core/build.gradle.kts#android.compileSdk"},
              {"tool": "android-build-tools", "version": "34.0.0",
               "declared_in": "app/build.gradle.kts#android.buildToolsVersion"},
              {"tool": "android-sdk", "version": "99", "declared_in": "lib/build.gradle.kts#android.compileSdk"},
              {"tool": "android-sdk", "version": "35'; touch x",
               "declared_in": "bad/build.gradle.kts#android.compileSdk"},
              {"tool": "java", "version": "17", "declared_in": "app/build.gradle.kts#java.toolchain.languageVersion"}]
    plan = preparation.android(stated)
    assert plan["files"] == preparation.NEEDS["cmdline-tools"]["files"] and plan["hosts"] == ("dl.google.com",)
    assert [(g["kind"], g["path"]) for g in plan["gaps"]] == [
        ("toolchain_unavailable", "bad/build.gradle.kts#android.compileSdk")]
    script = "\n".join(plan["lines"]).replace(preparation.IN, str(carried)).replace(preparation.T, str(tools))
    done = subprocess.run(["sh", "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "PATH": f"{programs}:{os.environ['PATH']}",
                               "CALLS": str(tmp_path / "calls")})
    assert (tmp_path / "calls").read_text(encoding="utf-8").splitlines() == [
        "sdkmanager --licenses", "sdkmanager platforms;android-35", "sdkmanager build-tools;34.0.0",
        "sdkmanager platforms;android-99"]
    sdk = tools / "android"
    assert (sdk / "platforms/android-35").is_dir() and (sdk / "build-tools/34.0.0").is_dir()
    assert preparation.missing(done.stderr) == [{
        "kind": "toolchain_unavailable", "tool": "android-sdk", "version": "99",
        "detail": "android-sdk 99: platforms;android-99: Warning: Failed to find package 'platforms;android-99'"}]
    assert not (tmp_path / "x").exists()
    assert preparation.android(stated[-1:]) == {"files": [], "lines": [], "hosts": (), "gaps": []}


def test_a_nested_cargo_crate_with_its_own_lockfile_restores_on_its_own():
    """Cargo writes `Cargo.lock` at a workspace's root: a crate below the root with one is a workspace of its own, one
    without is a member."""
    files = ["Cargo.toml", "Cargo.lock", "crates/a/Cargo.toml", "tools/gen/Cargo.toml", "tools/gen/Cargo.lock"]
    assert preparation.restores(files) == {"cargo": [".", "tools/gen"]}
    assert preparation.restores(["shell/Cargo.toml", "shell/Cargo.lock"]) == {"cargo": ["shell"]}


def test_a_package_lerna_json_names_is_installed_by_lerna_s_bootstrap_after_the_root_s_restore():
    """js-lerna: `lerna.json` names `packages/*` (none: Lerna's default, the same), the root declares no workspaces and
    `packages/b` depends on its sibling `@lrn/a`: Lerna's own `bootstrap` links and installs them, at the root, after
    the root's install; a package Lerna does not name stays a gap."""
    for lerna in ({"version": "1.0.0", "packages": ["packages/*"]}, {"version": "1.0.0"}):
        manifests = {"package.json": {"name": "root", "devDependencies": {"lerna": "^6.6.2"}}, "lerna.json": lerna,
                     "packages/a/package.json": {"name": "@lrn/a", "dependencies": {"ms": "2.1.3"}},
                     "packages/b/package.json": {"name": "@lrn/b", "dependencies": {"@lrn/a": "^1.0.0"}},
                     "landing/package.json": {"name": "landing", "dependencies": {"ms": "2.1.3"}}}
        plan = prepared(manifests)
        assert plan["restores"] == {"npm": ["."], "lerna": ["."]}
        assert [(g["kind"], g["path"]) for g in plan["gaps"]] == [("restore_failed", "landing")]
        assert plan["lines"][-1] == preparation.restore("lerna", ["."])
        assert "node_modules/.bin/lerna bootstrap --ignore-scripts" in plan["lines"][-1]


def test_a_nested_requirements_file_is_an_environment_of_its_own():
    """pip installs a requirements file where it is, and no workspace names one: `docs/requirements.txt` under a uv
    project is restored on its own; a pyproject member below the root stays the root's."""
    files = ["pyproject.toml", "uv.lock", "libs/core/pyproject.toml", "docs/requirements.txt", "tools/x/requirements.txt"]
    assert preparation.restores(files) == {"uv": ["."], "pip": ["docs", "tools/x"]}
    assert preparation.python_environments(files) == {".": "uv", "docs": "pip", "tools/x": "pip"}
    both = ["requirements.txt", "svc/pyproject.toml", "svc/requirements.txt"]  # a pyproject beside it: the root's
    assert preparation.restores(both) == {"pip": ["."]}
