"""Source: Gradle's own model of a build, read by an init script while Gradle configures it.

`commands` describes, for Daodan's container, `gradle help` with the init script `gradle_model.gradle` in each top
folder holding a settings script (or, without one, a build script), with the Gradle Daodan carries. The init script
applies to every build Gradle loads (the root build, included builds, buildSrc) and prints, once a build's settings
are evaluated, its root folder and the tree of projects its settings made (each project's path, folder and build
file); once its projects are configured, per project with a build file, the projects it depends on and only the
Java and Kotlin targets the build sets, never a default or a convention (that would be Gradle's own JVM, or a
toolchain lookup): the Java toolchain's `languageVersion`, `sourceCompatibility` and `targetCompatibility` of the
`java` extension or of a Java compile task, a compile task's `options.release`, Kotlin's `compilerOptions.jvmTarget`
of the extension or of a compile task; with the Android plugin, the SDK platform it compiles against (`compileSdk`)
and the build tools it runs (`buildToolsVersion`, the plugin's own default when the build sets none), which the
build needs installed. Configuring runs the project's settings and build scripts; the command
reaches the registries (plugins, a toolchain resolver).

`read` turns each project into a `gradle-project` unit named by its path (`:app:shared`; in an included build, its
identity path, `:tooling:core`), rooted at its folder, with its build file as manifest (none for a project without
one, which Gradle still makes) and the projects of its build it depends on as edges; each build is a `gradle`
workspace with its projects' folders as members; each target is a `java` toolchain declared in the project's build
file with the field (Gradle's model says which project a value applies to, not which script set it), the Android
values the toolchains `android-sdk` and `android-build-tools` (`ANDROID`), one the model gives none of (an add-on's
target) a `toolchain_undeclared` gap naming its package. A project's registries are the origins of the
repositories it and its buildscript resolve from and of those its build's settings declare (plugin management,
dependency resolution management). A build whose
settings did not evaluate is a `model_failed` gap; one that failed while configuring keeps its projects and is
`model_partial`: their edges and targets are unknown.
"""
from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path, PurePosixPath

import preparation
from premap.origins import origin

NAME, VERSION, RANK = "gradle", "9.9.1", "model"  # the Gradle of `indexers/jvm.py` GRADLE
DOWNLOAD = (("https://services.gradle.org/distributions/gradle-9.9.1-bin.zip",
             "d8a18a7a841dd5df825d35a685fad6f2d7f12ac0c280e57b67c27b4a520ba228"),)  # what the runner carries
SETTINGS = ("settings.gradle", "settings.gradle.kts")
BUILDS = ("build.gradle", "build.gradle.kts")
SEPARATOR = "\x1e"  # starts each record the init script prints
# Gradle's words for a dependency of the build (a plugin) that needs a newer JVM than the one Gradle runs on.
ASKS = re.compile(r"requires at least JVM runtime version (\d+)\. This build uses a Java (\d+) JVM")
# The Android plugin's facts: the toolchain each states and the SDK package it names (`preparation.ANDROID`).
ANDROID = {"android.compileSdk": ("android-sdk", "platforms;android-"),
           "android.buildToolsVersion": ("android-build-tools", "build-tools;")}
INIT = Path(__file__).with_name("gradle_model.gradle").read_text(encoding="utf-8")
SCRIPT = 'i=$(mktemp) && printf %s "$1" > "$i" && exec gradle --no-daemon --console=plain -q --init-script "$i" help'


def _folder(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def commands(context):
    marks = [rel for rel in context.inventory.files if PurePosixPath(rel).name in SETTINGS + BUILDS]
    folders = sorted({_folder(rel) for rel in marks}, key=lambda f: (f.count("/"), f))
    tops = [f for f in folders if not any(o != f and _inside(f, o) for o in folders)]
    return [{"tool": "gradle", "argv": ["sh", "-c", SCRIPT, "gradle", INIT], "cwd": top,
             "env": {"GRADLE_OPTS": "-Xmx512m", "LC_ALL": "C.UTF-8"}, "network": "registries"}
            for top in tops] or None


def retry(answer: dict) -> list[str]:
    """The hosts of the repositories a failed answer's builds declare in their settings (a plugin of
    `pluginManagement`), the hosts a preventive request names (`egress`); the runner no longer opens them by itself."""
    from urllib.parse import urlsplit
    found = set()
    for line in (answer.get("stdout") or "").split("\n"):
        try:
            record = json.loads(line[1:]) if line.startswith(SEPARATOR) else {}
        except ValueError:
            continue
        if record.get("kind") == "build":
            found |= {urlsplit(url).hostname for url in record.get("repositories") or ()}
    return sorted(found - {None})


def asked_jdk(said: str, stated=()) -> tuple[dict, dict | None] | None:
    """The JDK a build Gradle could not run on a JVM older than one of its dependencies needs (`ASKS` in `said`):
    the newest the project states at or above that version, else the version Gradle names, with a
    `jdk_from_build_error` gap; None when Gradle asked for nothing."""
    found = ASKS.search(said or "")
    return preparation.jdk_named(int(found.group(1)), found.group(), stated, "Gradle") if found else None


def _name(build: str | None, path: str) -> str:
    """A project's identity path: in an included build, prefixed by the build's name."""
    return path if build is None else f":{build}{'' if path == ':' else path}"


def read(context, commands, results):
    units, workspaces, toolchains, gaps, seen, version, registries = {}, [], [], [], set(), None, {}
    for command, result in zip(commands, results):
        root = result.get("root") or "/"

        def rel(path: str) -> str | None:
            value = posixpath.relpath(posixpath.normpath(path), root)
            return None if value.startswith("..") else value

        records = [json.loads(line[1:]) for line in (result["stdout"] or "").split("\n") if line.startswith(SEPARATOR)]
        builds = [r for r in records if r["kind"] == "build"]
        detail = (result["stderr"] or "").strip()[-400:]
        if not builds:
            gaps.append({"kind": "model_failed", "path": command["cwd"], "detail": f"gradle settings: {detail}"})
            continue
        if result["returncode"] != 0:
            gaps.append({"kind": "model_partial", "path": command["cwd"],
                         "detail": f"gradle configure failed: the edges and Java targets are unknown: {detail}"})
        for build in builds:
            version = version or build["gradle"]
            build_root = rel(build["root"])
            if build_root is None or build_root in seen:
                continue
            seen.add(build_root)
            members = []
            for project in build["projects"]:
                folder = rel(project["dir"])
                if folder is None:
                    continue
                members.append(folder)
                name = _name(build["name"] if build["nested"] else None, project["path"])
                units[name] = {"name": name, "kind": "gradle-project", "root": folder,
                               "manifest": rel(project["buildFile"]) if project["buildFileExists"] else None}
                registries[name] = {origin(url) for url in build.get("repositories") or ()}
            workspaces.append({"tool": "gradle", "root": build_root, "members": members})
        for project in (r for r in records if r["kind"] == "project"):
            unit, build_file = units.get(_name(project["build"], project["path"])), rel(project["buildFile"])
            if unit is not None and result["returncode"] == 0:
                unit["depends_on"] = [_name(project["build"], path) for path in project["uses"]]
            if unit is not None:
                registries[unit["name"]] |= {origin(url) for url in project.get("repositories") or ()}
            for field, value in project["facts"].items():
                where = f"{build_file}#{field}"
                if not build_file or result["returncode"] != 0:
                    continue
                if value == "" and field in ANDROID:  # the Android plugin applies and its model gives no value
                    gaps.append({"kind": "toolchain_undeclared", "path": build_file, "detail": f"{where}: Gradle's"
                                 f" model of the Android plugin gives none: no {ANDROID[field][1]}* SDK package is"
                                 " installed for this project"})
                    continue
                item = {"tool": ANDROID.get(field, ("java",))[0], "version": str(value), "declared_in": where}
                if item not in toolchains:
                    toolchains.append(item)
    for name, found in registries.items():
        if found - {None}:
            units[name]["registries"] = sorted(found - {None})
    facts = {key: value for key, value in (("units", list(units.values())), ("workspace", workspaces),
                                           ("toolchains", toolchains)) if value}
    return {"facts": facts, "gaps": gaps, **({"version": version} if version else {})}
