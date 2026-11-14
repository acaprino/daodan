"""Native group: each build tool's own project-model commands on the corpus of `fixtures/`, on Modal.

Every adapter `tools/native_<tool>.py` (and the baseline `tools/daodan_modules.py`) runs on fresh copies of each
fixture it applies to, with canary lines added to the copy's build scripts (never to the fixture), four times:

- `online`: a fresh HOME (cold caches), network on, every call under strace (execve, connect): the output,
  the network it reached, the programs it ran, the files it wrote in the copy, the canaries that fired;
- `offline_warm`: the HOME the online run filled, network blocked (`unshare -rn`): seconds, peak memory,
  and whether the output is the same;
- `offline_cold`: a fresh HOME, network blocked: what the tool answers then;
- `newer`: the copy asks for a toolchain newer than the installed one, warm HOME, network on, traced.

Each tool also runs once, traced, on a probe project written here with every hook that tool might execute.
The volume keeps one JSON per tool and fixture under `project-model/native/`; `fetch` scores the online output
with `score.py` into `results/native_<tool>.json`.

    modal deploy benchmarks/project-model/modal_native.py
    python benchmarks/project-model/modal_native.py spawn [--tools native_go,...] [--fixtures sys-go-single,...]
    python benchmarks/project-model/modal_native.py fetch [--tools ...] [--dir COPY]
    python benchmarks/project-model/modal_native.py prepare [--fixtures real-...]   clone real repositories once
    python benchmarks/project-model/modal_native.py spawn --fixtures real-... --modes online --timeout 600

`--dir` reads a local copy made with `modal volume get daodan-flow-results project-model/native COPY/..`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
ROOT = HERE if LOCAL else Path("/pm")
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
STORE = "project-model/native"
CANARY = "/tmp/pm-canary"
MODES = ("online", "offline_warm", "offline_cold", "newer")
REAL_STORE = "project-model/native-real"  # per real repository: <name>.tar.gz (the clone) and <name>.files.json
EXTRA_ENV: dict = {}
NO_NEWER = {"native_tsc", "native_gitmodules", "daodan_modules"}  # no toolchain request to raise
NOTRACE = {"native_bazel", "native_dotnet"}  # their runtimes stall under ptrace in gVisor: sockets are sampled instead
SLOW_UNDER_TRACE = {"native_gradle", "native_gradle_bsp", "native_maven", "native_swift"}  # traced online only; `newer` samples sockets
# tool -> (image, cpu, memory MB)
TOOLS = {
    "native_go": ("main", 1.0, 2048), "native_cargo": ("main", 1.0, 2048), "native_npm": ("main", 1.0, 2048),
    "native_pnpm": ("main", 1.0, 2048), "native_yarn": ("main", 1.0, 2048), "native_bun": ("main", 1.0, 2048),
    "native_uv": ("main", 1.0, 2048), "native_pip": ("main", 1.0, 2048), "native_maven": ("main", 2.0, 4096),
    "native_gradle": ("main", 2.0, 4096), "native_cmake": ("main", 1.0, 2048), "native_meson": ("main", 1.0, 2048),
    "native_bazel": ("main", 2.0, 4096), "native_composer": ("main", 1.0, 2048),
    "native_dotnet": ("dotnet", 2.0, 4096), "native_bundler": ("ruby", 1.0, 2048), "native_pub": ("dart", 1.0, 2048),
    "native_swift": ("swift", 2.0, 4096), "native_mix": ("elixir", 1.0, 2048), "daodan_modules": ("main", 1.0, 2048),
    "native_tsc": ("main", 1.0, 2048), "native_gitmodules": ("main", 1.0, 2048), "native_gradle_bsp": ("main", 2.0, 4096),
}

# ---------------------------------------------------------------- images (pinned)

TEMURIN = "eclipse-temurin:17-jdk-noble@sha256:1bedb04434bd275ef072355e9caec2a22be5240fbe82ad51a59323f2bbcab4a6"
APT = ("git", "ca-certificates", "curl", "unzip", "xz-utils", "strace", "procps", "util-linux")
PIP = ("psutil==7.1.3", "packaging==25.0")
GH = "https://github.com"
INSTALL_MAIN = [
    "curl -fsSLo /tmp/go.tgz https://go.dev/dl/go1.27.3.linux-amd64.tar.gz"
    " && echo '65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40  /tmp/go.tgz' | sha256sum -c -"
    " && tar -C /opt -xzf /tmp/go.tgz && rm /tmp/go.tgz",
    "cd /tmp && curl -fsSLO https://nodejs.org/dist/v22.23.4/node-v22.23.4-linux-x64.tar.xz"
    " && curl -fsSLO https://nodejs.org/dist/v22.23.4/SHASUMS256.txt"
    " && grep ' node-v22.23.4-linux-x64.tar.xz$' SHASUMS256.txt | sha256sum -c -"
    " && tar -C /opt -xJf node-v22.23.4-linux-x64.tar.xz && mv /opt/node-v22.23.4-linux-x64 /opt/node"
    " && rm node-v22.23.4-linux-x64.tar.xz SHASUMS256.txt"
    " && PATH=/opt/node/bin:$PATH npm install -g --no-fund --no-audit pnpm@10.33.2 @yarnpkg/cli-dist@4.9.2"
    " typescript@6.0.3",
    f"cd /tmp && curl -fsSLO {GH}/oven-sh/bun/releases/download/bun-v1.4.4/bun-linux-x64.zip"
    f" && curl -fsSLO {GH}/oven-sh/bun/releases/download/bun-v1.4.4/SHASUMS256.txt"
    " && grep ' bun-linux-x64.zip$' SHASUMS256.txt | sha256sum -c -"
    " && unzip -q bun-linux-x64.zip -d /opt && mv /opt/bun-linux-x64 /opt/bun && rm bun-linux-x64.zip SHASUMS256.txt",
    "curl -fsSLo /tmp/rustup-init https://static.rust-lang.org/rustup/archive/1.28.2/x86_64-unknown-linux-gnu/rustup-init"
    " && echo \"$(curl -fsSL https://static.rust-lang.org/rustup/archive/1.28.2/x86_64-unknown-linux-gnu/rustup-init.sha256"
    " | cut -d' ' -f1)  /tmp/rustup-init\" | sha256sum -c - && chmod +x /tmp/rustup-init"
    " && RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo /tmp/rustup-init -y --no-modify-path --profile minimal"
    " --default-toolchain 1.99.1 && rm /tmp/rustup-init",
    "curl -fsSLo /tmp/m.zip https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.10.0/apache-maven-3.10.0-bin.zip"
    " && echo '1f6d9909266510f039f59aa0e13dcd2c66da85f043e56276e41f2918f8bddaff  /tmp/m.zip' | sha256sum -c -"
    " && unzip -q /tmp/m.zip -d /opt && mv /opt/apache-maven-3.10.0 /opt/maven && rm /tmp/m.zip",
    "curl -fsSLo /tmp/g.zip https://services.gradle.org/distributions/gradle-9.9.1-bin.zip"
    " && echo 'd8a18a7a841dd5df825d35a685fad6f2d7f12ac0c280e57b67c27b4a520ba228  /tmp/g.zip' | sha256sum -c -"
    " && unzip -q /tmp/g.zip -d /opt && mv /opt/gradle-9.9.1 /opt/gradle && rm /tmp/g.zip",
    f"mkdir -p /opt/bazelisk/bin && curl -fsSLo /opt/bazelisk/bin/bazel {GH}/bazelbuild/bazelisk/releases/download/v1.26.0/bazelisk-linux-amd64"
    " && chmod +x /opt/bazelisk/bin/bazel && sha256sum /opt/bazelisk/bin/bazel"
    " && BAZELISK_HOME=/opt/bazelisk USE_BAZEL_VERSION=7.4.1 /opt/bazelisk/bin/bazel --version",
    # build-server-for-gradle has no release artifact: built from its tag, tests skipped
    f"git clone -q --depth 1 --branch 0.4.0 {GH}/microsoft/build-server-for-gradle /opt/bsg/src"
    " && cd /opt/bsg/src && git rev-parse HEAD > /opt/bsg/VERSION"
    " && GRADLE_USER_HOME=/opt/bsg/gradle-home ./gradlew --no-daemon -q :server:jar -x test"
    " && ls /opt/bsg/src/server/build/libs /opt/bsg/src/server/build/libs/plugins"
    " && printf '#!/bin/sh\\nexec java -Dplugin.dir=/opt/bsg/src/server/build/libs/plugins -DdisableServerTelemetry=true"
    " -cp \"/opt/bsg/src/server/build/libs/server.jar:/opt/bsg/src/server/build/libs/runtime/*\""
    " com.microsoft.java.bs.core.Launcher\\n' > /opt/bsg/launch.sh && chmod 755 /opt/bsg/launch.sh && cat /opt/bsg/launch.sh",
    # a second JDK for builds whose plugins need Java 21 to run (kotlinconf); used only when a run passes JAVA_HOME
    "apt-get update -q && apt-get install -y -q --no-install-recommends openjdk-21-jdk-headless && ls /usr/lib/jvm",
]
ENV_MAIN = {
    "PATH": "/opt/node/bin:/opt/go/bin:/opt/cargo/bin:/opt/bun:/opt/maven/bin:/opt/gradle/bin:/opt/bazelisk/bin:"
            "/opt/java/openjdk/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "RUSTUP_HOME": "/opt/rustup", "BAZELISK_HOME": "/opt/bazelisk", "JAVA_HOME": "/opt/java/openjdk",
}


def _mounts(image):
    if not LOCAL:
        return image
    image = image.add_local_dir(ROOT / "tools", "/pm/tools", ignore=["**/__pycache__/**"])
    image = image.add_local_dir(ROOT / "fixtures", "/pm/fixtures")
    image = image.add_local_file(ROOT / "modal_native.py", "/pm/modal_native.py")
    return image


def _main_image():
    image = (modal.Image.from_registry(TEMURIN, add_python="3.12")
             .apt_install(*APT, "build-essential", "cmake", "ninja-build", "pkg-config", "zlib1g-dev",
                          "php-cli", "php-xml", "php-mbstring", "php-curl", "php-zip", "composer")
             .pip_install(*PIP, "uv==0.11.28", "meson==1.6.1", "tree-sitter==0.26.0",
                          "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
             .run_commands(*INSTALL_MAIN)
             .env(ENV_MAIN))
    if LOCAL:
        image = image.add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
    return _mounts(image)


def _other_image(base: str, extra: list[str], env: dict | None = None):
    image = modal.Image.from_registry(base, add_python="3.12").apt_install(*APT).pip_install(*PIP)
    if extra:
        image = image.run_commands(*extra)
    if env:
        image = image.env(env)
    return _mounts(image)


IMAGES = {
    "main": _main_image,
    "dotnet": lambda: _other_image("mcr.microsoft.com/dotnet/sdk:8.0.404", [], {"DOTNET_CLI_TELEMETRY_OPTOUT": "1"}),
    # the SDK a real repository asks for (eShop global.json: 10.0.302), for a second run beside 8.0.404
    "dotnet10": lambda: _other_image("mcr.microsoft.com/dotnet/sdk:10.0.302", [], {"DOTNET_CLI_TELEMETRY_OPTOUT": "1"}),
    "ruby": lambda: _other_image("ruby:3.3.6-slim-bookworm", []),
    "dart": lambda: _other_image("dart:3.5.4", []),
    "swift": lambda: _other_image("swift:5.10.1-noble", []),
    "elixir": lambda: _other_image("elixir:1.17.3-otp-27", ["MIX_HOME=/opt/mix mix local.hex --force",
                                                             "MIX_HOME=/opt/mix mix local.rebar --force"],
                                   {"MIX_HOME": "/opt/mix"}),
}

app = modal.App("daodan-pm-native")
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)


def code_sha256() -> str:
    """One hash over this driver and the native adapters, compared with the local one before trusting a run."""
    digest = hashlib.sha256()
    files = sorted((ROOT / "tools").glob("native_*.py")) + [ROOT / "tools/daodan_modules.py", ROOT / "tools/bsp_client.py",
                                                             ROOT / "modal_native.py"]
    for path in files:
        digest.update(path.name.encode() + b"\0" + path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()[:16]


# ---------------------------------------------------------------- canaries, probes, newer toolchains

def _mark(name: str) -> str:
    return f"{CANARY}/{name}"


def inject(project: Path) -> list[str]:
    """Add a canary line to each build script of the copy; returns the files changed."""
    import re
    changed = []

    def edit(path: Path, new: str):
        path.write_text(new, encoding="utf-8")
        changed.append(path.relative_to(project).as_posix())

    for path in sorted(project.rglob("*")):
        if not path.is_file() or "node_modules" in path.parts or ".git" in path.parts:
            continue
        rel = path.relative_to(project).as_posix()
        tag = re.sub(r"[^A-Za-z0-9]+", "_", rel)
        text = path.read_text(encoding="utf-8", errors="replace") if path.stat().st_size < 2_000_000 else ""
        name = path.name
        if name == "package.json":
            try:
                data = json.loads(text)
            except ValueError:
                continue
            if not isinstance(data, dict):
                continue
            scripts = data.setdefault("scripts", {}) if isinstance(data.get("scripts", {}), dict) else {}
            for event in ("preinstall", "install", "postinstall", "prepare", "preprepare", "postprepare",
                          "prepack", "postpack", "dependencies"):
                touch = f"touch {_mark(f'npm-{event}-{tag}')}"
                scripts[event] = f"{touch} && {scripts[event]}" if event in scripts else touch
            data["scripts"] = scripts
            edit(path, json.dumps(data, indent=2) + "\n")
        elif name == "build.rs":
            edit(path, re.sub(r"fn main\(\)\s*\{", f'fn main() {{ let _ = std::fs::write("{_mark("cargo-build-rs-" + tag)}", b"");',
                              text, count=1))
        elif name == "setup.py":
            lines = text.split("\n")
            at = max((i + 1 for i, line in enumerate(lines) if line.startswith("from __future__")), default=0)
            lines.insert(at, f'open("{_mark("setup-py-" + tag)}", "w").close()')
            edit(path, "\n".join(lines))
        elif name in ("build.gradle", "settings.gradle"):
            edit(path, text + f'\nnew File("{_mark("gradle-" + tag)}").text = ""\n')
        elif name in ("build.gradle.kts", "settings.gradle.kts"):
            edit(path, text + f'\nFile("{_mark("gradle-" + tag)}").writeText("")\n')
        elif name == "CMakeLists.txt":
            edit(path, text + f'\nfile(WRITE {_mark("cmake-" + tag)} "")\n')
        elif name == "meson.build":
            edit(path, text + f"\nrun_command('touch', '{_mark('meson-' + tag)}', check: false)\n")
        elif name == "Gemfile":
            edit(path, f'File.write("{_mark("bundler-" + tag)}", "")\n' + text)
        elif name == "mix.exs":
            edit(path, f'File.write!("{_mark("mix-" + tag)}", "")\n' + text)
        elif name == "Package.swift":
            first, _, rest = text.partition("\n")
            edit(path, first + "\nimport Foundation\n" +
                 f'FileManager.default.createFile(atPath: "{_mark("swift-" + tag)}", contents: nil)\n' + rest)
        elif name.endswith((".csproj", ".fsproj", ".vbproj")) and "</Project>" in text:
            target = (f'  <Target Name="PmCanary" BeforeTargets="Restore;_GenerateRestoreGraph;'
                      f'_GenerateRestoreGraphProjectEntry;CollectPackageReferences">\n'
                      f'    <Touch Files="{_mark("dotnet-" + tag)}" AlwaysCreate="true" />\n  </Target>\n</Project>')
            edit(path, text.replace("</Project>", target, 1))
        elif name == "composer.json":
            try:
                data = json.loads(text)
            except ValueError:
                continue
            scripts = data.setdefault("scripts", {})
            for event in ("pre-install-cmd", "post-install-cmd", "pre-update-cmd", "post-update-cmd",
                          "pre-autoload-dump", "post-autoload-dump", "post-root-package-install"):
                scripts.setdefault(event, f"touch {_mark('composer-' + event)}")
            edit(path, json.dumps(data, indent=2) + "\n")
    return changed


def newer(tool: str, project: Path) -> list[str]:
    """Ask, in the copy, for a toolchain newer than the installed one; returns what was changed."""
    import re
    done = []

    def sub(path: Path, pattern: str, replacement: str, flags=re.M):
        text = path.read_text(encoding="utf-8", errors="replace")
        new, count = re.subn(pattern, replacement, text, flags=flags)
        if count:
            path.write_text(new, encoding="utf-8")
            done.append(f"{path.relative_to(project).as_posix()}: {replacement.strip()[:60]}")

    def files(*names):
        return [p for p in sorted(project.rglob("*")) if p.is_file() and (p.name in names or any(
            n.startswith("*") and p.name.endswith(n[1:]) for n in names)) and "node_modules" not in p.parts]

    def write(rel: str, text: str):
        (project / rel).write_text(text, encoding="utf-8")
        done.append(f"{rel}: written")

    if tool == "native_go":
        for p in files("go.mod", "go.work"):
            sub(p, r"^go \S+$", "go 1.99.0")
    elif tool == "native_cargo":
        write("rust-toolchain.toml", '[toolchain]\nchannel = "1.199.0"\n')
        if (project / "rust-toolchain").is_file():
            write("rust-toolchain", "1.199.0\n")
    elif tool in ("native_npm", "native_pnpm", "native_yarn", "native_bun"):
        manager = {"native_npm": "npm", "native_pnpm": "pnpm", "native_yarn": "yarn", "native_bun": "bun"}[tool]
        for p in files("package.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                continue
            data["engines"] = {**(data.get("engines") or {}), "node": ">=99", manager: ">=99"}
            data["packageManager"] = f"{manager}@99.0.0"
            p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            done.append(f"{p.relative_to(project).as_posix()}: engines >=99, packageManager {manager}@99.0.0")
        if tool == "native_bun":
            write(".bun-version", "99.0.0\n")
    elif tool in ("native_uv", "native_pip"):
        for p in files("pyproject.toml"):
            sub(p, r'^requires-python\s*=\s*"[^"]*"', 'requires-python = ">=3.99"')
        for p in files("setup.py"):
            sub(p, r"python_requires\s*=\s*['\"][^'\"]*['\"]", "python_requires='>=3.99'")
        write(".python-version", "3.99\n")
    elif tool == "native_maven":
        for p in files("pom.xml"):
            sub(p, r"<(maven\.compiler\.release|maven\.compiler\.source|maven\.compiler\.target|java\.version|release)>"
                   r"\s*\d+\s*</\1>", r"<\1>99</\1>")
    elif tool in ("native_gradle", "native_gradle_bsp"):
        for p in files("*.gradle", "*.gradle.kts"):
            sub(p, r"JavaLanguageVersion\.of\(\s*\d+\s*\)", "JavaLanguageVersion.of(99)")
            sub(p, r"jvmToolchain\(\s*\d+\s*\)", "jvmToolchain(99)")
        for p in files("gradle-wrapper.properties"):
            sub(p, r"gradle-[\w.\-]+?-(bin|all)\.zip", r"gradle-99.0-\1.zip")
    elif tool == "native_cmake":
        for p in files("CMakeLists.txt"):
            sub(p, r"cmake_minimum_required\s*\(\s*VERSION\s+[\d.]+(\.\.\.[\d.]+)?", "cmake_minimum_required(VERSION 9.99", re.M | re.I)
    elif tool == "native_meson":
        p = project / "meson.build"
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            new = re.sub(r"meson_version\s*:\s*'[^']*'", "meson_version: '>=9.99'", text)
            if new == text:
                new = re.sub(r"project\(\s*'([^']+)'", r"project('\1', meson_version: '>=9.99'", text, count=1)
            p.write_text(new, encoding="utf-8")
            done.append("meson.build: meson_version >=9.99")
    elif tool == "native_bazel":
        write(".bazelversion", "99.0.0\n")
    elif tool == "native_dotnet":
        write("global.json", '{"sdk": {"version": "99.0.100", "rollForward": "latestFeature"}}\n')
    elif tool == "native_composer":
        for p in files("composer.json"):
            data = json.loads(p.read_text(encoding="utf-8"))
            data.setdefault("require", {})["php"] = ">=99"
            p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            done.append(f"{p.relative_to(project).as_posix()}: php >=99")
    elif tool == "native_bundler":
        write(".ruby-version", "9.9.9\n")
        for p in files("Gemfile"):
            if not re.search(r"^ruby ", p.read_text(encoding="utf-8"), re.M):
                p.write_text(p.read_text(encoding="utf-8") + '\nruby "9.9.9"\n', encoding="utf-8")
                done.append(f"{p.relative_to(project).as_posix()}: ruby 9.9.9")
    elif tool == "native_pub":
        for p in files("pubspec.yaml"):
            sub(p, r"^(\s+sdk:\s*).*$", r"\1'>=99.0.0 <100.0.0'")
    elif tool == "native_swift":
        for p in files("Package.swift"):
            sub(p, r"^// swift-tools-version:\s*[\d.]+", "// swift-tools-version:99.0")
    elif tool == "native_mix":
        for p in files("mix.exs"):
            sub(p, r'elixir:\s*"[^"]*"', 'elixir: "~> 99.0"')
    return done


PACKAGE_PROBE = json.dumps({"name": "probe", "version": "0.1.0", "private": True, "scripts": {
    e: f"touch {_mark('npm-' + e)}" for e in ("preinstall", "install", "postinstall", "prepare", "dependencies")}},
    indent=2)
SETUP_PROBE = {"pyproject.toml": '[build-system]\nrequires = ["setuptools>=61"]\nbuild-backend = "setuptools.build_meta"\n\n'
                                 '[project]\nname = "probe"\ndynamic = ["version"]\nrequires-python = ">=3.9"\n',
               "setup.py": f'open("{_mark("setup-py")}", "w").close()\nfrom setuptools import setup\nsetup(version="0.1.0")\n'}
CANARY_JAVA = f'''package pmcanary;
public class Canary extends org.apache.maven.AbstractMavenLifecycleParticipant {{
    static {{ mark("maven-extension-loaded"); }}
    static void mark(String name) {{
        try {{ java.nio.file.Files.write(java.nio.file.Paths.get("{CANARY}", name), new byte[0]); }} catch (Exception e) {{ }}
    }}
    @Override public void afterProjectsRead(org.apache.maven.execution.MavenSession session) {{ mark("maven-extension-afterProjectsRead"); }}
}}
'''
CANARY_COMPONENTS = ('<component-set><components><component><role>org.apache.maven.AbstractMavenLifecycleParticipant</role>'
                     '<role-hint>pmcanary</role-hint><implementation>pmcanary.Canary</implementation></component>'
                     '</components></component-set>\n')
PROBES = {
    "native_go": {"go.mod": "module example.com/probe\n\ngo 1.22\n",
                  "main.go": 'package main\n\n//go:generate touch /tmp/pm-canary/go-generate\n\n/*\n#cgo CFLAGS: -DPROBE=1\n'
                             'int probe(void) { return 1; }\n*/\nimport "C"\n\nfunc main() { _ = C.probe() }\n'},
    "native_cargo": {"Cargo.toml": '[package]\nname = "probe"\nversion = "0.1.0"\nedition = "2021"\n',
                     "build.rs": f'fn main() {{ let _ = std::fs::write("{_mark("cargo-build-rs")}", b""); }}\n',
                     "src/lib.rs": "pub fn probe() {}\n"},
    "native_npm": {"package.json": PACKAGE_PROBE,
                   "package-lock.json": '{"name": "probe", "version": "0.1.0", "lockfileVersion": 3, "requires": true, '
                                        '"packages": {"": {"name": "probe", "version": "0.1.0"}}}\n'},
    "native_pnpm": {"package.json": PACKAGE_PROBE, "pnpm-lock.yaml": "lockfileVersion: '9.0'\n\nimporters:\n\n  .: {}\n",
                    ".pnpmfile.cjs": f"require('fs').writeFileSync('{_mark('pnpm-pnpmfile')}', '');\n"
                                     "module.exports = { hooks: {} };\n"},
    "native_yarn": {"package.json": PACKAGE_PROBE, "yarn.lock": "__metadata:\n  version: 8\n  cacheKey: 10\n",
                    ".yarnrc.yml": "yarnPath: ./canary-yarn.cjs\n",
                    "canary-yarn.cjs": f"require('fs').writeFileSync('{_mark('yarn-yarnpath')}', '');\nprocess.exit(3);\n"},
    "native_bun": {"package.json": PACKAGE_PROBE,
                   "bun.lock": '{\n  "lockfileVersion": 1,\n  "workspaces": {\n    "": {\n      "name": "probe",\n    },\n  },\n'
                               '  "packages": {},\n}\n',
                   "bunfig.toml": 'preload = ["./canary.ts"]\n',
                   "canary.ts": f"require('fs').writeFileSync('{_mark('bun-preload')}', '');\n"},
    "native_uv": SETUP_PROBE, "native_pip": SETUP_PROBE,
    "native_maven": {"pom.xml": '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>'
                                '<groupId>pm</groupId><artifactId>probe</artifactId><version>0.1.0</version>'
                                '<repositories><repository><id>pmrepo</id><url>file://${project.basedir}/repo</url>'
                                '</repository></repositories><pluginRepositories><pluginRepository><id>pmrepo</id>'
                                '<url>file://${project.basedir}/repo</url></pluginRepository></pluginRepositories>'
                                '<build><extensions><extension><groupId>pmcanary</groupId><artifactId>pmcanary</artifactId>'
                                '<version>1.0</version></extension></extensions></build></project>\n',
                     "repo/pmcanary/pmcanary/1.0/pmcanary-1.0.pom":
                         '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>'
                         '<groupId>pmcanary</groupId><artifactId>pmcanary</artifactId><version>1.0</version></project>\n'},
    "native_gradle": {"settings.gradle": f'new File("{_mark("gradle-settings")}").text = ""\nrootProject.name = "probe"\n',
                      "build.gradle": f'new File("{_mark("gradle-build")}").text = ""\n'},
    "native_cmake": {"CMakeLists.txt": f'cmake_minimum_required(VERSION 3.20)\nproject(probe C)\nfile(WRITE {_mark("cmake-lists")} "")\n'
                                       f'execute_process(COMMAND touch {_mark("cmake-execute-process")})\n'
                                       'add_library(probe STATIC probe.c)\n',
                     "probe.c": "int probe(void) { return 1; }\n",
                     "CMakePresets.json": '{"version": 3, "configurePresets": [{"name": "default"}]}\n'},
    "native_meson": {"meson.build": f"project('probe', 'c')\nrun_command('touch', '{_mark('meson-run-command')}', check: false)\n"
                                    "executable('probe', 'probe.c')\n",
                     "probe.c": "int main(void) { return 0; }\n"},
    "native_bazel": {"MODULE.bazel": 'module(name = "probe", version = "0.1.0")\n'
                                     'canary = use_extension("//:canary.bzl", "canary")\nuse_repo(canary, "canary_repo")\n',
                     "canary.bzl": "def _repo(rctx):\n"
                                   f'    rctx.execute(["touch", "{_mark("bazel-repository-rule")}"])\n'
                                   '    rctx.file("BUILD.bazel", "")\n    rctx.file("defs.bzl", "X = 1\\n")\n'
                                   "canary_repo = repository_rule(implementation = _repo)\n"
                                   'def _ext(mctx):\n    canary_repo(name = "canary_repo")\n'
                                   "canary = module_extension(implementation = _ext)\n",
                     "BUILD.bazel": 'load("@canary_repo//:defs.bzl", "X")\nfilegroup(name = "f", srcs = [])\n',
                     ".bazelversion": "7.4.1\n"},
    "native_dotnet": {"Probe.csproj": '<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup><TargetFramework>net8.0</TargetFramework>'
                                      '</PropertyGroup>\n  <Target Name="PmCanary" BeforeTargets="Restore;_GenerateRestoreGraph;'
                                      '_GenerateRestoreGraphProjectEntry;CollectPackageReferences">\n'
                                      f'    <Touch Files="{_mark("dotnet-target")}" AlwaysCreate="true" />\n  </Target>\n</Project>\n'},
    "native_composer": {"composer.json": json.dumps({"name": "pm/probe", "require": {}, "scripts": {
        e: f"touch {_mark('composer-' + e)}" for e in ("pre-install-cmd", "post-install-cmd", "pre-update-cmd",
                                                        "pre-autoload-dump", "post-root-package-install")}}, indent=2)},
    "native_bundler": {"Gemfile": f'File.write("{_mark("bundler-gemfile")}", "")\nsource "https://rubygems.org"\n'},
    "native_pub": {"pubspec.yaml": "name: probe\nenvironment:\n  sdk: ^3.5.0\n",
                   "hook/build.dart": f"import 'dart:io';\nvoid main(List<String> args) {{ File('{_mark('dart-build-hook')}').createSync(); }}\n",
                   "lib/probe.dart": "void probe() {}\n"},
    "native_swift": {"Package.swift": '// swift-tools-version:5.9\nimport PackageDescription\nimport Foundation\n'
                                      f'FileManager.default.createFile(atPath: "{_mark("swift-package")}", contents: nil)\n'
                                      'let package = Package(name: "Probe", targets: [.target(name: "Probe")])\n',
                     "Sources/Probe/Probe.swift": "public func probe() {}\n"},
    "native_mix": {"mix.exs": f'File.write!("{_mark("mix-exs")}", "")\ndefmodule Probe.MixProject do\n  use Mix.Project\n'
                              '  def project, do: [app: :probe, version: "0.1.0", deps: []]\nend\n'},
}
PREPARE = {"native_uv": [["uv", "lock"]]}  # probe-only calls before the adapter, measured like the rest


def _write_probe(tool: str, project: Path) -> None:
    import subprocess
    for rel, text in PROBES[tool].items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if tool == "native_maven":
        src = project.parent / "canary-src"
        (src / "pmcanary").mkdir(parents=True, exist_ok=True)
        (src / "pmcanary/Canary.java").write_text(CANARY_JAVA, encoding="utf-8")
        (src / "META-INF/plexus").mkdir(parents=True, exist_ok=True)
        (src / "META-INF/plexus/components.xml").write_text(CANARY_COMPONENTS, encoding="utf-8")
        subprocess.run(["javac", "-cp", "/opt/maven/lib/*", "-d", str(src), str(src / "pmcanary/Canary.java")], check=True)
        target = project / "repo/pmcanary/pmcanary/1.0/pmcanary-1.0.jar"
        subprocess.run(["jar", "cf", str(target), "-C", str(src), "pmcanary/Canary.class", "-C", str(src),
                        "META-INF/plexus/components.xml"], check=True)
        for artifact in (target, target.with_suffix(".pom")):  # checksums beside each file, as a repository has
            artifact.with_name(artifact.name + ".sha1").write_text(hashlib.sha1(artifact.read_bytes()).hexdigest(),
                                                                   encoding="utf-8")


# ---------------------------------------------------------------- measuring one run

INTERPRETERS = {"node", "python", "python3", "sh", "bash", "dash", "ruby", "perl", "php", "bun", "deno", "elixir"}


def _trace(path: str | None, project: str) -> dict:
    import re
    if not path or not Path(path).is_file():
        return {}
    execs, net, project_exec = {}, set(), []
    attempts = probes = 0
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if "execve(" in line:
            match = re.search(r'execve\("([^"]+)", \[(.*?)\]', line)
            if not match or line.rstrip().endswith("ENOENT (No such file or directory)"):
                continue
            exe, argv = match.group(1), re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(2))
            execs[Path(exe).name] = execs.get(Path(exe).name, 0) + 1
            script = next((a for a in argv[1:] if not a.startswith("-")), "")
            if exe.startswith(project) or (Path(exe).name.rstrip("0123456789.") in INTERPRETERS and script.startswith(project)):
                if len(project_exec) < 8:
                    project_exec.append(" ".join([exe] + argv[1:4])[:240])
        elif "connect(" in line and ("AF_INET" in line):
            address = re.search(r'inet_addr\("([^"]+)"\)|inet_pton\(AF_INET6, "([^"]+)"', line)
            port = re.search(r"sin6?_port=htons\((\d+)\)", line)
            host = (address.group(1) or address.group(2)) if address else "?"
            if host.startswith("127.") or host in ("::1", "::ffff:127.0.0.1", "0.0.0.0"):
                continue
            if port and port.group(1) == "0":  # getaddrinfo's address sorting: a name was resolved, no traffic
                probes += 1
                continue
            attempts += 1
            net.add(f"{host}:{port.group(1) if port else '?'}")
    return {"execs": dict(sorted(execs.items(), key=lambda kv: -kv[1])[:20]), "network": sorted(net)[:20],
            "network_attempts": attempts, "address_sorting": probes, "project_exec": project_exec}


def _summary(call: dict, project: str) -> dict:
    out = {k: call.get(k) for k in ("name", "rc", "seconds", "peak_mb", "left_running", "sockets")}
    out["stderr"] = (call.get("stderr") or "").strip()[-1500:]
    if call.get("rc") not in (0, None):
        out["stdout_head"] = (call.get("stdout_head") or "").strip()[:600]
    writes = call.get("writes") or {}
    out["writes"] = {k: v[:15] for k, v in writes.items() if v}
    out["canaries"] = call.get("canaries") or []
    out.update(_trace(call.get("trace"), project))
    return out


def _clean_canaries() -> None:
    import shutil
    shutil.rmtree(CANARY, ignore_errors=True)
    Path(CANARY).mkdir(parents=True, exist_ok=True)


def _rust_toolchains() -> set[str]:
    folder = Path("/opt/rustup/toolchains")
    return {p.name for p in folder.iterdir()} if folder.is_dir() else set()


def _one(tool: str, adapter, source: Path | None, work: Path, mode: str, home: Path, probe: bool = False) -> dict:
    """One run of `adapter` on a fresh copy of `source` (or of the probe) in `mode`."""
    import shutil
    import time
    import native_common as common
    project = work / (source.name if source is not None else "probe")
    shutil.rmtree(work, ignore_errors=True)
    if probe:
        project.mkdir(parents=True)
        _write_probe(tool, project)
        injected = sorted(PROBES[tool])
    else:
        shutil.copytree(source, project, symlinks=True, ignore=shutil.ignore_patterns("expected.json", "source.json"))
        injected = inject(project) if tool != "daodan_modules" else []
    changed = newer(tool, project) if mode == "newer" else []
    (work / "out").mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    _clean_canaries()
    rust_before = _rust_toolchains()
    common.reset()
    common.WRAP = ["unshare", "-rn"] if mode.startswith("offline") else []
    real = source is not None and str(source).startswith("/work/real/")
    slow = tool in SLOW_UNDER_TRACE  # on a real repository traced nowhere: canaries and sampled sockets instead
    traced = (mode == "online" and not (real and slow)) or (mode == "newer" and not slow)
    common.TRACE = str(work / "trace") if traced and tool not in NOTRACE else None
    if common.TRACE:
        Path(common.TRACE).mkdir(parents=True, exist_ok=True)
    common.ENV = {"HOME": str(home), "XDG_CACHE_HOME": str(home / ".cache"), "XDG_CONFIG_HOME": str(home / ".config"),
                  "XDG_DATA_HOME": str(home / ".local/share"), "CARGO_HOME": str(home / ".cargo"),
                  "HEX_HOME": str(home / ".hex"), "DOTNET_CLI_HOME": str(home), "NUGET_PACKAGES": str(home / ".nuget/packages"),
                  "GRADLE_USER_HOME": str(home / ".gradle"), "GOPATH": str(home / "go"), "TMPDIR": str(work / "tmp"),
                  # Java takes user.home from the password file, not HOME: without this Maven shares /root/.m2
                  "MAVEN_OPTS": f"-Duser.home={home}", **EXTRA_ENV}
    (work / "tmp").mkdir(exist_ok=True)
    common.WATCH = str(project)
    common.CANARY = CANARY
    started = time.time()
    output, error = None, None
    for argv in (PREPARE.get(tool, []) if probe else []):
        common.run(argv, project, name=" ".join(argv) + " (probe preparation)")
    try:
        output = adapter.run(project, work / "out")
    except Exception as exc:  # noqa: BLE001 - recorded
        import traceback
        error = f"{type(exc).__name__}: {exc} | {traceback.format_exc()[-600:]}"
    seconds = round(time.time() - started, 2)
    calls = [_summary(c, str(project)) for c in common.CALLS]
    new_rust = sorted(_rust_toolchains() - rust_before)
    fired = sorted(p.name for p in Path(CANARY).iterdir())
    notes = dict(common.NOTES)
    if tool == "daodan_modules":
        notes = {"raw": dict(adapter.LAST)}
    record = {"mode": mode, "seconds": seconds, "peak_mb": max([c.get("peak_mb") or 0 for c in calls] or [0]),
              "calls": calls, "errors": (notes.get("errors") or [])[:12], "raw": notes.get("raw"),
              "canaries_injected": injected, "canaries_fired": fired, "rust_toolchains_installed": new_rust,
              "newer_changes": changed, "output": output, "adapter_error": error}
    shutil.rmtree(project, ignore_errors=True)
    return record


def _verdict(online: dict) -> str:
    if online.get("canaries_fired") or any(c.get("project_exec") for c in online.get("calls", [])):
        return "yes"
    if any("execs" in c for c in online.get("calls", [])):
        return "no"
    return "unknown"


def _applies(paths: list[str], triggers: set) -> bool:
    """Whether a file list holds a trigger outside dot and pruned folders, as `native_common.find` walks."""
    import native_common as common
    for rel in paths:
        parts = rel.split("/")
        if any(p.startswith(".") or p in common.PRUNE for p in parts[:-1]):
            continue
        name = parts[-1]
        if name in triggers or any(t.startswith("*") and name.endswith(t[1:]) for t in triggers):
            return True
    return False


def _real_source(name: str) -> Path | None:
    """The clone of a real repository, extracted once per container from the archive `prepare_real` stored."""
    import shutil
    import tarfile
    archive = Path("/results") / REAL_STORE / f"{name}.tar.gz"
    dest = Path("/work/real") / name
    if dest.is_dir():
        return dest
    if not archive.is_file():
        print(name, "no archive", flush=True)
        return None
    part = Path("/work/real-part") / name
    shutil.rmtree(part, ignore_errors=True)
    part.mkdir(parents=True)
    with tarfile.open(archive) as tar:
        tar.extractall(part, filter="tar")
    dest.parent.mkdir(parents=True, exist_ok=True)
    (part / name).rename(dest)
    return dest


def _run_tool(tool: str, fixtures: list[str] | None, modes: list[str], probe: bool, timeout: int = 900,
              label: str = "", env: dict | None = None) -> dict:
    """`label` stores the records apart (`<tool><label>`); `env` is added to every call (a toolchain to try)."""
    EXTRA_ENV.clear()
    EXTRA_ENV.update(env or {})
    import importlib
    import os
    import shutil
    import subprocess
    import time
    sys.path.insert(0, "/pm/tools")
    sys.path.insert(0, "/pm")
    print("code", code_sha256(), flush=True)
    adapter = importlib.import_module(tool)
    version = None
    if getattr(adapter, "VERSION_COMMAND", None):
        try:
            done = subprocess.run(adapter.VERSION_COMMAND, capture_output=True, text=True, timeout=120,
                                  env={**os.environ, "HOME": "/tmp/version-home"})
            version = (done.stdout or done.stderr).strip()[:300]
        except OSError as exc:
            version = f"unavailable: {exc}"
    import native_common as common
    common.TIMEOUT = timeout  # every call of a build tool; a model not out in time is a result, not a retry
    common.TRACE_CALLS = EXTRA_ENV.get("PM_TRACE_CALLS", "execve,connect")
    names = fixtures or sorted(d.name for d in (ROOT / "fixtures").iterdir()
                               if d.is_dir() and not d.name.startswith("_") and (d / "expected.json").is_file())
    triggers = set(getattr(adapter, "TRIGGERS", ()))
    if tool == "daodan_modules":
        modes = ["online"]
    base = Path("/work") / tool
    shutil.rmtree(base, ignore_errors=True)
    store = Path("/results") / STORE / f"{tool}{label}"
    store.mkdir(parents=True, exist_ok=True)
    summary = {}
    targets = []
    for n in names:
        folder = ROOT / "fixtures" / n
        if (folder / "source.json").is_file():  # a real repository: its clone, prepared by `prepare_real`
            listing = Path("/results") / REAL_STORE / f"{n}.files.json"
            if not listing.is_file():
                print(n, "not prepared", flush=True)
                continue
            if triggers and not _applies(json.loads(listing.read_text(encoding="utf-8")), triggers):
                continue
            folder = _real_source(n)
            if folder is None:
                continue
        targets.append((n, folder))
    if probe and tool in PROBES:
        targets.append(("_probe", None))
    committed = time.time()
    for position, (name, source) in enumerate(targets):
        if source is not None and triggers and not common.find(source, triggers):
            continue
        record = {"tool": f"{tool}{label}", "env": EXTRA_ENV or None, "fixture": name, "version": getattr(adapter, "VERSION", None),
                  "version_reported": version, "command": getattr(adapter, "COMMAND", None), "code": code_sha256(),
                  "runs": {}}
        homes = {"online": base / name / "home-online", "offline_cold": base / name / "home-cold"}
        rust_before = _rust_toolchains()
        for mode in (["online"] if source is None else modes):
            if mode == "newer" and tool in NO_NEWER:
                continue
            if mode in ("offline_cold", "newer"):  # toolchains rustup installed belong to the warm state only
                for extra in _rust_toolchains() - rust_before:
                    shutil.rmtree(Path("/opt/rustup/toolchains") / extra, ignore_errors=True)
            home = homes.get(mode, homes["online"])
            record["runs"][mode] = _one(tool, adapter, source, base / name / mode, mode, home, probe=source is None)
        for extra in _rust_toolchains() - rust_before:
            shutil.rmtree(Path("/opt/rustup/toolchains") / extra, ignore_errors=True)
        online = record["runs"].get("online", {})
        for run in record["runs"].values():
            run["same_as_online"] = run.get("output") == online.get("output")
            run["code"] = record["code"]
        record["executed_project_code"] = _verdict(online)
        if "offline_warm" in record["runs"]:
            record["offline_second_run"] = record["runs"]["offline_warm"]["output"] == online.get("output")
        target = store / f"{name}.json"
        is_real = source is not None and str(source).startswith("/work/real/")
        if target.is_file() and not is_real:  # a rerun of some modes keeps the stored runs of the others
            old = json.loads(target.read_text(encoding="utf-8"))
            old_online = (old.get("runs") or {}).get("online", {})
            for mode, run in (old.get("runs") or {}).items():
                if mode not in record["runs"]:
                    run.setdefault("same_as_online", run.get("output") == old_online.get("output"))
                    run.setdefault("code", old.get("code"))
                    record["runs"][mode] = run
            if "offline_warm" not in [m for m in modes] and "offline_second_run" in old:
                record["offline_second_run"] = old["offline_second_run"]
        if EXTRA_ENV.get("PM_KEEP_TRACE"):  # a diagnostic run keeps its raw strace files beside the record
            for trace in (base / name).glob("*/trace"):
                shutil.copytree(trace, store / f"{name}-{trace.parent.name}-trace", dirs_exist_ok=True)
        shutil.rmtree(base / name, ignore_errors=True)
        target.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        if time.time() - committed > 45 or position == len(targets) - 1:
            volume.commit()
            committed = time.time()
        summary[name] = {m: (r.get("adapter_error") or len(r.get("errors") or []), r["seconds"]) for m, r in record["runs"].items()}
        print(name, json.dumps(summary[name]), flush=True)
    return {"tool": tool, "fixtures": summary}


MAIN = IMAGES["main"]()
OPTIONS = {"timeout": 3600, "volumes": {"/results": volume}}


@app.function(image=MAIN, cpu=1.0, memory=2048, **OPTIONS)
def run_main_1(tool: str, fixtures: list | None = None, modes: list | None = None, probe: bool = True,
               timeout: int = 900, label: str = "", env: dict | None = None) -> dict:
    return _run_tool(tool, fixtures, list(modes or MODES), probe, timeout, label, env)


@app.function(image=MAIN, cpu=2.0, memory=4096, **OPTIONS)
def run_main_2(tool: str, fixtures: list | None = None, modes: list | None = None, probe: bool = True,
               timeout: int = 900, label: str = "", env: dict | None = None) -> dict:
    return _run_tool(tool, fixtures, list(modes or MODES), probe, timeout, label, env)


@app.function(image=IMAGES["dotnet"](), cpu=2.0, memory=4096, **OPTIONS)
def run_dotnet_2(tool: str, fixtures: list | None = None, modes: list | None = None, probe: bool = True,
               timeout: int = 900, label: str = "", env: dict | None = None) -> dict:
    return _run_tool(tool, fixtures, list(modes or MODES), probe, timeout, label, env)


@app.function(image=IMAGES["dotnet10"](), cpu=2.0, memory=4096, **OPTIONS)
def run_dotnet10_2(tool: str, fixtures: list | None = None, modes: list | None = None, probe: bool = True,
                   timeout: int = 900, label: str = "", env: dict | None = None) -> dict:
    return _run_tool(tool, fixtures, list(modes or MODES), probe, timeout, label, env)


@app.function(image=IMAGES["ruby"](), cpu=1.0, memory=2048, **OPTIONS)
def run_ruby_1(tool: str, fixtures: list | None = None, modes: list | None = None, probe: bool = True,
               timeout: int = 900, label: str = "", env: dict | None = None) -> dict:
    return _run_tool(tool, fixtures, list(modes or MODES), probe, timeout, label, env)


@app.function(image=IMAGES["dart"](), cpu=1.0, memory=2048, **OPTIONS)
def run_dart_1(tool: str, fixtures: list | None = None, modes: list | None = None, probe: bool = True,
               timeout: int = 900, label: str = "", env: dict | None = None) -> dict:
    return _run_tool(tool, fixtures, list(modes or MODES), probe, timeout, label, env)


@app.function(image=IMAGES["swift"](), cpu=2.0, memory=4096, **OPTIONS)
def run_swift_2(tool: str, fixtures: list | None = None, modes: list | None = None, probe: bool = True,
               timeout: int = 900, label: str = "", env: dict | None = None) -> dict:
    return _run_tool(tool, fixtures, list(modes or MODES), probe, timeout, label, env)


@app.function(image=IMAGES["elixir"](), cpu=1.0, memory=2048, **OPTIONS)
def run_elixir_1(tool: str, fixtures: list | None = None, modes: list | None = None, probe: bool = True,
               timeout: int = 900, label: str = "", env: dict | None = None) -> dict:
    return _run_tool(tool, fixtures, list(modes or MODES), probe, timeout, label, env)


@app.function(image=MAIN, cpu=1.0, memory=2048, timeout=2400, volumes={"/results": volume})
def prepare_real(names: list) -> dict:
    """Clone each real repository at its pinned commit (shallow), store the archive and the file list."""
    import os
    import shutil
    import subprocess
    import tarfile
    import time
    out = {}
    store = Path("/results") / REAL_STORE
    store.mkdir(parents=True, exist_ok=True)
    for name in names:
        source = json.loads((ROOT / "fixtures" / name / "source.json").read_text(encoding="utf-8"))
        work = Path("/work/clone") / name
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        started = time.time()
        steps = [["git", "init", "-q"], ["git", "remote", "add", "origin", source["repo"]],
                 ["git", "fetch", "-q", "--depth", "1", "origin", source["commit"]],
                 ["git", "checkout", "-q", "FETCH_HEAD"]]
        error = None
        for argv in steps:
            done = subprocess.run(argv, cwd=work, capture_output=True, text=True, timeout=900,
                                  env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
            if done.returncode != 0:
                error = f"{' '.join(argv[:3])}: {done.stderr.strip()[-400:]}"
                break
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=work, capture_output=True, text=True).stdout.strip()
        files = []
        for base, dirs, items in os.walk(work):
            dirs[:] = [d for d in dirs if d != ".git"]
            files += [(Path(base) / i).relative_to(work).as_posix() for i in items]
        record = {"repo": source["repo"], "commit": source["commit"], "head": head, "error": error,
                  "files": len(files), "seconds": round(time.time() - started, 1)}
        if not error and head == source["commit"]:
            with tarfile.open(store / f"{name}.tar.gz", "w:gz") as tar:
                tar.add(work, arcname=name)
            (store / f"{name}.files.json").write_text(json.dumps(files), encoding="utf-8")
            record["archive_mb"] = round((store / f"{name}.tar.gz").stat().st_size / 2**20, 1)
        shutil.rmtree(work, ignore_errors=True)
        out[name] = record
        print(name, json.dumps(record), flush=True)
    (store / f"prepared-{int(time.time())}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    volume.commit()
    return out


# ---------------------------------------------------------------- local: spawn and fetch

def _records(tool: str, local: str | None):
    """The stored records of a tool: from a directory `modal volume get` filled, or read one by one."""
    if local:
        for path in sorted((Path(local) / tool).glob("*.json")):
            yield json.loads(path.read_text(encoding="utf-8"))
        return
    for entry in sorted(volume.listdir(f"{STORE}/{tool}"), key=lambda e: e.path):
        yield json.loads(b"".join(volume.read_file(entry.path)))


def _fetch(tools: list[str], local: str | None = None) -> None:
    sys.path.insert(0, str(HERE))
    import score
    for tool in tools:
        try:
            records = list(_records(tool, local))
        except Exception as exc:  # noqa: BLE001 - nothing stored yet
            print(tool, "nothing on the volume:", exc)
            continue
        result = {"tool": tool, "group": "native", "fixtures": {}, "probe": None}
        for record in records:
            result.setdefault("version", record.get("version"))
            result.setdefault("version_reported", record.get("version_reported"))
            result.setdefault("command", record.get("command"))
            result.setdefault("code", record.get("code"))
            runs = record["runs"]
            online = runs.get("online", {})
            facts = {}
            for mode, run in runs.items():
                calls = run.get("calls") or []
                facts[mode] = {
                    "ok": run.get("output") is not None and not run.get("adapter_error"),
                    "items": {k: len(v) for k, v in (run.get("output") or {}).items() if isinstance(v, list)},
                    "same_as_online": run.get("same_as_online", run.get("output") == online.get("output")),
                    "seconds": run["seconds"], "peak_mb": run["peak_mb"],
                    "network_attempts": sum(c.get("network_attempts") or 0 for c in calls)
                    + sum(len(c.get("sockets") or []) for c in calls if "network_attempts" not in c),
                    "network": sorted({n for c in calls for n in (c.get("network") or []) + (c.get("sockets") or [])})[:12],
                    "traced": any("execs" in c for c in calls),
                    "writes": {c["name"]: c["writes"] for c in calls if c.get("writes")},
                    "canaries_fired": run.get("canaries_fired"), "project_exec": [p for c in calls for p in c.get("project_exec") or []][:6],
                    "left_running": [p for c in calls for p in c.get("left_running") or []][:6],
                    "rust_toolchains_installed": run.get("rust_toolchains_installed"),
                    "errors": (run.get("errors") or [])[:6], "adapter_error": run.get("adapter_error"),
                    "calls": [{k: c.get(k) for k in ("name", "rc", "seconds", "peak_mb", "network_attempts", "canaries")}
                              for c in calls][:20],
                }
                if mode == "newer":
                    facts[mode]["changes"] = run.get("newer_changes")
                    facts[mode]["stderr"] = [c["stderr"][-300:] for c in calls if c.get("rc") not in (0, None)][:4]
            item = {"output": online.get("output"), "raw": online.get("raw"),
                    "seconds": (runs.get("offline_warm") or online).get("seconds"),
                    "peak_mb": max(r["peak_mb"] for r in runs.values()),
                    "network_attempts": facts.get("online", {}).get("network_attempts"),
                    "offline_second_run": record.get("offline_second_run"),
                    "executed_project_code": record.get("executed_project_code"),
                    "error": online.get("adapter_error") or ("; ".join(online.get("errors") or [])[:800] or None),
                    "facts": facts}
            name = record["fixture"]
            if name == "_probe":
                result["probe"] = item
                continue
            expected_file = HERE / "fixtures" / name / "expected.json"
            if isinstance(item["output"], dict) and expected_file.is_file():
                item["score"] = score.score(json.loads(expected_file.read_text(encoding="utf-8")), item["output"])
            result["fixtures"][name] = item
        out = HERE / "results" / f"{tool}.json"
        # one fixture per line: small, and a diff shows which fixture changed
        lines = [f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
                 for k, v in result["fixtures"].items()]
        head = {k: v for k, v in result.items() if k != "fixtures"}
        text = json.dumps(head, ensure_ascii=False, separators=(",", ":"))[:-1] + ',\n"fixtures": {\n' + ",\n".join(lines) + "\n}}\n"
        json.loads(text)
        out.write_text(text, encoding="utf-8", newline="\n")
        print(tool, len(result["fixtures"]), "fixtures", "probe" if result["probe"] else "")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "hash", "prepare"))
    parser.add_argument("--tools", default=",".join(TOOLS))
    parser.add_argument("--fixtures", default="")
    parser.add_argument("--modes", default=",".join(MODES))
    parser.add_argument("--no-probe", action="store_true")
    parser.add_argument("--timeout", type=int, default=900, help="seconds each build-tool call may take")
    parser.add_argument("--dir", help="with fetch: read the records from this copy of project-model/native")
    args = parser.parse_args()
    chosen = [t.strip() for t in args.tools.split(",") if t.strip()]
    if args.command == "hash":
        print(code_sha256())
    elif args.command == "spawn":
        print("local code", code_sha256())
        fixtures = [f.strip() for f in args.fixtures.split(",") if f.strip()] or None
        for tool in chosen:
            key = TOOLS[tool]
            function = modal.Function.from_name("daodan-pm-native", f"run_{key[0]}_{int(key[1])}")
            call = function.spawn(tool, fixtures, [m for m in args.modes.split(",") if m], not args.no_probe,
                                  args.timeout)
            print(tool, call.object_id)
    elif args.command == "prepare":
        names = [f.strip() for f in args.fixtures.split(",") if f.strip()] or sorted(
            d.name for d in (HERE / "fixtures").iterdir() if (d / "source.json").is_file())
        print("prepare", modal.Function.from_name("daodan-pm-native", "prepare_real").spawn(names).object_id)
    else:
        _fetch(chosen, args.dir)
