"""The preparation's dependency restores: each package manager's own command, run in Daodan's container.

The answers are in `tests/fixtures/premap/restore/<manager>.json`, recorded once in a real container from the
projects beside them (`tests/fixtures/premap/restore/<manager>/`): `good` restores, `bad` names a package no
registry has.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

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
        assert ran[1:] == [f"{'bundled' if refuse else 'installed'} corepack pnpm install --frozen-lockfile"]
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
    assert preparation.restores(files) == {"uv": ["."], "poetry": ["svc"]}
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


def test_a_dotnet_solution_that_does_not_restore_restores_each_of_its_projects_and_stays_a_gap(tmp_path):
    """eShop: one project of the solution needs a workload the container lacks (NETSDK1147), and the solution's
    restore restores nothing; each project the solution lists is then restored on its own, and the failure stays
    a gap with the error lines of both."""
    import os
    import subprocess
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
