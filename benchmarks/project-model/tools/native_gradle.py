"""Gradle: the build model as Gradle configures it, read by an init script once every project is evaluated.

At each top-most settings script (or, without one, top-most build script): `gradle --no-daemon -q
--init-script pm-model.gradle pmResolve --continue`. Init scripts apply to every build of the tree (the root build, buildSrc,
included builds); in `projectsEvaluated` each writes per project the path, directory, build file, source sets
with their source directories, compile tasks, declared dependencies per configuration, what the classpath
configurations resolve to (projects of other builds included), the Java toolchain requested and the one Gradle
would launch; the resolution runs in a `pmResolve` task of each project of the main build, since Gradle 9
resolves configurations only inside a task. Configuring a Gradle build runs its scripts: project code by construction.

The Gradle version is the one the wrapper names (gradle/wrapper/gradle-wrapper.properties, official site only),
downloaded with curl into the run's Gradle home, as Daodan's container does; without a wrapper, the installed
Gradle. The wrapper script and jar are never run.
"""
from __future__ import annotations

import json
import os
import re
import zipfile
from pathlib import Path

import native_common as common

VERSION = "Gradle 9.9.1 on Temurin 17"
VERSION_COMMAND = ["gradle", "--version"]
TRIGGERS = ("settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts")
COMMAND = "gradle --no-daemon -q --init-script pm-model.gradle pmResolve --continue"
INIT = r'''
import groovy.json.JsonOutput
import org.gradle.api.artifacts.component.ProjectComponentIdentifier
gradle.projectsEvaluated { g ->
    def out = []
    def build = g.parent == null ? '' : g.rootProject.name
    g.rootProject.allprojects.each { p ->
        def entry = [path: p.path, build: build, dir: p.projectDir.absolutePath, buildFile: p.buildFile.absolutePath,
                     buildFileExists: p.buildFile.exists(), sourceSets: [:], compileTasks: [], declared: [],
                     resolved: [:], errors: [], android: p.extensions.findByName('android') != null,
                     toolchain: null, launcher: null]
        def kotlin = p.extensions.findByName('kotlin')
        try {
            def sets = p.extensions.findByName('sourceSets')
            def android = p.extensions.findByName('android')
            if (android != null) {
                android.sourceSets.each { ss ->
                    def dirs = ss.java.srcDirs + (ss.hasProperty('kotlin') ? ss.kotlin.srcDirs : [])
                    entry.sourceSets[ss.name] = dirs.collect { it.absolutePath }.unique()
                }
                entry.compileTasks = p.tasks.names.findAll { it ==~ /compile\w*(JavaWithJavac|Kotlin)/ }.sort()
            } else if (sets != null && !sets.isEmpty()) {
                sets.each { ss ->
                    def ks = null
                    try { ks = kotlin?.sourceSets?.findByName(ss.name) } catch (Throwable ignored) {}
                    def dirs = ks != null ? ks.kotlin.srcDirs : ss.java.srcDirs
                    ['groovy', 'scala'].each { lang -> def x = ss.extensions.findByName(lang); if (x != null) { dirs = dirs + x.srcDirs } }
                    entry.sourceSets[ss.name] = dirs.collect { it.absolutePath }.unique()
                    def names = []
                    if (ks != null) { names << ss.getCompileTaskName('kotlin') }
                    names << ss.compileJavaTaskName
                    ['groovy', 'scala'].each { lang -> if (ss.extensions.findByName(lang) != null) { names << ss.getCompileTaskName(lang) } }
                    entry.compileTasks.addAll(names.findAll { p.tasks.names.contains(it) })
                }
            } else if (kotlin != null && kotlin.hasProperty('targets')) {
                kotlin.sourceSets.each { ks -> entry.sourceSets[ks.name] = ks.kotlin.srcDirs.collect { it.absolutePath } }
                kotlin.targets.each { t ->
                    if (t.platformType.name() != 'common') {
                        t.compilations.each { c -> entry.compileTasks << c.compileKotlinTaskName }
                    }
                }
            }
        } catch (Throwable e) { entry.errors << ('sourceSets: ' + e.message) }
        p.configurations.each { c ->
            // what a build script declares: declarable configurations, not the plugins' own tool classpaths
            def declarable = c.hasProperty('canBeDeclared') ? c.canBeDeclared : true
            if (!declarable || c.name.startsWith('kotlin') || c.name.endsWith('Elements')) { return }
            c.dependencies.each { d ->
                def item = [configuration: c.name, group: d.group, name: d.name, version: d.version]
                if (d instanceof org.gradle.api.artifacts.ProjectDependency) {
                    item.project = d.hasProperty('path') ? d.path : d.dependencyProject.path
                }
                entry.declared << item
            }
        }
        try {
            def spec = p.extensions.findByName('java')?.toolchain
            if (spec != null && spec.languageVersion.isPresent()) {
                entry.toolchain = spec.languageVersion.get().toString()
                def launcher = p.extensions.getByName('javaToolchains').launcherFor(spec).get()
                entry.launcher = launcher.metadata.languageVersion.toString() + ' ' + launcher.metadata.installationPath
            }
        } catch (Throwable e) { entry.errors << ('toolchain: ' + e.message) }
        out << entry
    }
    def dir = new File(System.getProperty('pm.out'))
    dir.mkdirs()
    new File(dir, (build ?: '_root') + '.json').text = JsonOutput.toJson([gradle: g.gradleVersion, build: build,
        rootDir: g.rootProject.projectDir.absolutePath, projects: out])
}
// Gradle 9 resolves configurations only inside a task: one task per project, everything captured up front.
gradle.allprojects { p ->
    def key = (p.gradle.parent == null ? '' : p.gradle.rootProject.name) + p.path
    p.tasks.register('pmResolve') { t ->
        def confs = ['compileClasspath', 'runtimeClasspath', 'testCompileClasspath', 'testRuntimeClasspath']
            .collect { p.configurations.findByName(it) }.findAll { it != null && it.canBeResolved }
        def target = new File(new File(System.getProperty('pm.out')), 'resolved' + key.replace(':', '_') + '.json')
        t.doLast {
            def resolved = [:]
            def errors = []
            confs.each { c ->
                try {
                    resolved[c.name] = c.incoming.resolutionResult.root.dependencies.collect { dep ->
                        if (!dep.hasProperty('selected')) { return [requested: dep.requested.displayName, failed: true] }
                        def id = dep.selected.id
                        def mv = dep.selected.moduleVersion
                        [requested: dep.requested.displayName, group: mv?.group, name: mv?.name, version: mv?.version,
                         project: (id instanceof ProjectComponentIdentifier) ?
                             (id.hasProperty('buildTreePath') ? id.buildTreePath : id.projectPath) : null]
                    }
                } catch (Throwable e) {
                    def causes = []
                    for (def x = e.cause; x != null && causes.size() < 3; x = x.cause) { causes << x.message }
                    errors << (c.name + ': ' + e.message + (causes ? ' <- ' + causes.join(' <- ') : ''))
                }
            }
            target.parentFile.mkdirs()
            target.text = JsonOutput.toJson([key: key, resolved: resolved, errors: errors])
        }
    }
}
'''
SCOPE = {"implementation": "runtime", "api": "runtime", "compileOnly": "provided", "runtimeOnly": "runtime",
         "compileOnlyApi": "provided", "annotationProcessor": "build", "kapt": "build", "ksp": "build",
         "testImplementation": "test", "testRuntimeOnly": "test", "testCompileOnly": "test",
         "testAnnotationProcessor": "test", "developmentOnly": "dev", "classpath": "build"}


def _scope(configuration: str) -> str:
    if configuration in SCOPE:
        return SCOPE[configuration]
    return "test" if configuration.lower().startswith("test") or "Test" in configuration else "runtime"


def _name(project: dict) -> str:
    """The project path; a project of an included build or buildSrc is prefixed with that build's name."""
    if not project["build"]:
        return project["path"]
    return f":{project['build']}" + ("" if project["path"] == ":" else project["path"])


def _gradle(directory: Path, raw: dict) -> str:
    """The gradle executable for the build at `directory`: the wrapper's distribution, else the installed one."""
    props = directory / "gradle/wrapper/gradle-wrapper.properties"
    text = props.read_text(encoding="utf-8", errors="replace") if props.is_file() else ""
    match = re.search(r"^distributionUrl=(\S+)", text, re.M)
    url = match.group(1).replace("\\:", ":") if match else ""
    version = re.match(r"https://services\.gradle\.org/distributions/gradle-([\w.\-]+?)-(?:bin|all)\.zip$", url)
    if not version:
        return "gradle"
    home = Path(common.ENV.get("HOME") or os.environ.get("HOME", "/root")) / ".gradle/pm-dists" / version.group(1)
    executable = home / f"gradle-{version.group(1)}" / "bin" / "gradle"
    raw.setdefault("wrapper", []).append(version.group(1))
    if not executable.is_file():
        home.mkdir(parents=True, exist_ok=True)
        archive = home / "dist.zip"
        done = common.run(["curl", "-fsSL", "-o", str(archive), url], directory, name="curl wrapper distribution")
        if done.returncode != 0 or not archive.is_file():
            raw.setdefault("wrapper download", []).append(common.error_of(done))
            return "gradle-unavailable"
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(home)
        archive.unlink()
        executable.chmod(0o755)
    return str(executable)


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir), Path(work_dir)
    scripts = common.find(root, set(TRIGGERS))
    settings = [s for s in scripts if Path(s).name.startswith("settings.")]
    pool = settings or scripts
    tops = sorted({common.parent(s) for s in pool
                   if not any(common.parent(q) != common.parent(s) and
                              (common.parent(q) == "." or common.parent(s).startswith(common.parent(q) + "/"))
                              for q in pool)})
    init = work / "pm-model.gradle"
    init.write_text(INIT, encoding="utf-8")
    units, workspaces, toolchains, dependencies, errors, raw = [], [], [], [], [], {}
    for n, directory in enumerate(tops):
        out = work / f"gradle-model-{n}"
        gradle = _gradle(root / directory, raw)
        if gradle == "gradle-unavailable":
            errors.append(f"{directory}: the wrapper's Gradle could not be downloaded")
            continue
        done = common.run([gradle, "--no-daemon", "-q", "--console=plain", "--init-script", str(init),
                           f"-Dpm.out={out}", "pmResolve", "--continue"], root / directory, name=COMMAND)
        files = sorted(out.glob("*.json")) if out.is_dir() else []
        models = [m for m in (common.json_or_none(f.read_text(encoding="utf-8")) for f in files
                              if not f.name.startswith("resolved")) if m]
        resolutions = {r["key"]: r for r in (common.json_or_none(f.read_text(encoding="utf-8")) for f in files
                                             if f.name.startswith("resolved")) if r}
        if done.returncode != 0:
            errors.append(f"{directory}: {common.error_of(done)}")
        if not models:
            continue
        projects = [p for m in models for p in m["projects"]]
        for project in projects:
            resolution = resolutions.get(project["build"] + project["path"]) or {}
            project["resolved"] = resolution.get("resolved") or {}
            project["errors"] += resolution.get("errors") or []
        raw.setdefault("gradle", models[0].get("gradle"))
        raw.setdefault("project errors", {}).update({_name(p): p["errors"][:8] for p in projects if p["errors"]})
        raw.setdefault("android", []).extend(_name(p) for p in projects if p["android"])
        for project in projects:
            unit_root = common.rel(project["dir"], root)
            manifest = common.rel(project["buildFile"], root) if project["buildFileExists"] else None
            source_sets = {name: [common.rel(d, root) for d in dirs] for name, dirs in project["sourceSets"].items()}
            sources = sorted({d for dirs in source_sets.values() for d in dirs if (root / d).is_dir()})
            resolved, depends = {}, []
            for entries in project["resolved"].values():
                for entry in entries:
                    if entry.get("project"):
                        depends.append(entry["project"])
                    elif entry.get("group") and not entry.get("failed"):
                        resolved.setdefault(f"{entry['group']}:{entry['name']}", entry["version"])
            substituted = {e["requested"].rsplit(":", 1)[0] if e["requested"].count(":") > 1 else e["requested"]
                           for entries in project["resolved"].values() for e in entries if e.get("project")}
            for dep in project["declared"]:
                if dep.get("group") and f"{dep['group']}:{dep['name']}" in substituted:
                    continue  # a module coordinate an included build substitutes: a unit, already in depends_on
                if dep.get("project"):
                    depends.append(dep["project"] if not project["build"] else f":{project['build']}{dep['project']}")
                    continue
                if not dep.get("group"):
                    continue
                name = f"{dep['group']}:{dep['name']}"
                item = {"unit": _name(project), "name": name, "declared": dep.get("version"),
                        "scope": _scope(dep["configuration"]), "declared_in": manifest}
                if project["resolved"]:
                    item["resolved"] = resolved.get(name)
                dependencies.append(item)
            unit = {"name": _name(project), "kind": "gradle-project", "root": unit_root, "source_roots": sources,
                    "depends_on": sorted(set(depends) - {_name(project)}),
                    "config": {"source_sets": source_sets, "compile_tasks": project["compileTasks"]}}
            if manifest:
                unit["manifest"] = manifest
            units.append(unit)
            if project.get("toolchain"):
                toolchains.append({"tool": "java", "version": project["toolchain"], "declared_in": manifest})
                raw.setdefault("launcher", {})[_name(project)] = project.get("launcher")
        main = [m for m in models if not m["build"]] or models
        workspaces.append({"tool": "gradle", "root": common.rel(main[0]["rootDir"], root),
                           "members": [u["root"] for u in units if u["kind"] == "gradle-project"
                                       and not u["root"].startswith("buildSrc")]})
    common.NOTES.update(errors=errors, raw=raw)
    return {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "toolchains": toolchains, "dependencies": dependencies}


if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1], sys.argv[2]), indent=1))
