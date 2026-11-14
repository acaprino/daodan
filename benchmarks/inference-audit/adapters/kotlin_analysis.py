"""The Kotlin Analysis API asked only where the whole-project index is uncertain or silent.

`ask` starts one standalone session (`KotlinAsk.kt`, a copy of the map's resolver with one source module per
compile task, one library module per jar and a description of each answer) and asks each site:
- `ref`: the reference at a position, the occurrence of a name;
- `implicit`: every implicit operator call on a line (`x[k]`, `x[k] = v`, the `for` iterator, `by` delegates,
  `componentN`), with the role of each;
- `overridden`: what the declaration at a position overrides.

The modules come from the sources and classpath each KotlinCompile task dumped for scip-java
(`kotlin-configs/`): a classpath entry that is another task's output (its classes or its jar) becomes a
dependency on that task's module, so a call across tasks resolves to the source declaration, not to a jar.
An answer in a library names the jar; `external` reads group, artifact and version from its cache path.
"""
from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import subprocess
import threading
import time
from pathlib import Path

SOURCE = Path(__file__).with_name("KotlinAsk.kt")
JAVA = "/opt/jdk/bin/java"  # the JDK of adapters/kotlin.py
HEAP_MB = 3072
TIMEOUT = 120
OUTPUT = re.compile(r"build/(?:classes/[^/]+/(?P<set>[^/]+)|libs/[^/]+\.jar)$")
CACHED = re.compile(r"/files-2\.1/(?P<group>[^/]+)/(?P<artifact>[^/]+)/(?P<version>[^/]+)/[0-9a-f]+/[^/]+\.jar$"
                    r"|/repository/(?P<path>.+)/(?P<artifact2>[^/]+)/(?P<version2>[^/]+)/[^/]+\.jar$")


def _resolve_edges():
    import resolve_edges
    return resolve_edges


def build(java: str, work_dir: Path) -> Path:
    """KotlinAsk.kt compiled once against the Analysis API the map pins, cached by the source's digest."""
    edges = _resolve_edges()
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()[:12]
    jar = Path(work_dir) / f"kotlin-ask-{edges.KOTLIN_ANALYSIS.rsplit(':', 1)[1]}-{digest}.jar"
    if jar.is_file():
        return jar
    compiler = os.pathsep.join(str(edges.maven_artifact(item)) for item in edges.KOTLIN_COMPILER)
    classpath = os.pathsep.join(str(path) for path in runtime(None)[1:])
    command = [java, "-Xmx1g", "-cp", compiler, "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler", str(SOURCE),
               "-classpath", classpath, "-d", str(jar), "-jvm-target", "17", "-no-stdlib", "-no-reflect",
               "-Xskip-prerelease-check", *[f"-opt-in=org.jetbrains.kotlin.analysis.api.{name}"
                                            for name in edges.KOTLIN_OPT_INS]]
    done = subprocess.run(command, capture_output=True, text=True, timeout=900)
    if done.returncode != 0 or not jar.is_file():
        raise RuntimeError("KotlinAsk.kt did not compile: " + (done.stderr or done.stdout)[-1500:])
    return jar


def runtime(jar: Path | None) -> list:
    edges = _resolve_edges()
    return [jar, edges.maven_artifact(edges.KOTLIN_ANALYSIS), *(edges.maven_artifact(item)
                                                                for item in edges.KOTLIN_RUNTIME)]


def modules(configs: Path) -> tuple[list[dict], str]:
    """One module per compile task, in dependency order, and the source root the tasks list files under."""
    tasks, root = [], ""
    for config in sorted(Path(configs).glob("*.txt")):
        rows = [row.split(" ", 1) for row in config.read_text(encoding="utf-8").splitlines() if " " in row]
        task = {"name": config.stem, "sources": [], "classpath": []}
        for key, value in rows:
            if key == "sourceroot":
                task["root"] = value
            elif key == "source":
                task["sources"].append(value)
            elif key == "classpath":
                task["classpath"].append(value)
        if not task.get("root") or not Path(task["root"]).is_dir() or not task["sources"]:
            continue
        root = task["root"]
        first = Path(task["sources"][0]).relative_to(task["root"]).as_posix()
        project, _, rest = first.partition("src/")
        task["home"] = (project.rstrip("/"), rest.split("/", 1)[0])
        tasks.append(task)
    homes = {task["home"]: task["name"] for task in tasks}
    for task in tasks:
        task["depends"], task["libraries"] = [], []
        for entry in task["classpath"]:
            match = OUTPUT.search(entry) if entry.startswith(root + "/") else None
            if match:
                project = Path(entry).relative_to(root).as_posix().partition("build/")[0].rstrip("/")
                home = homes.get((project, match.group("set") or "main"))
                if home and home != task["name"] and home not in task["depends"]:
                    task["depends"].append(home)
            elif entry.endswith(".jar") and Path(entry).is_file() and "scip-plugin" not in entry:
                task["libraries"].append(entry)
    ordered, done = [], set()
    while len(ordered) < len(tasks):
        ready = [task for task in tasks if task["name"] not in done and set(task["depends"]) <= done]
        if not ready:
            raise RuntimeError("compile tasks depend on each other in a cycle")
        for task in ready:
            ordered.append(task)
            done.add(task["name"])
    return ordered, root


def external(target: dict) -> dict | None:
    """Group, artifact and version of the jar an answer lies in, from its cache path; the JDK by name."""
    module = target.get("module") or ""
    if module.startswith("library:"):
        jar = module.split(":", 1)[1].split(",")[0]
        match = CACHED.search(jar.replace("\\", "/"))
        if match and match.group("group"):
            return {"jar": Path(jar).name, "group": match.group("group"), "artifact": match.group("artifact"),
                    "version": match.group("version")}
        if match:
            return {"jar": Path(jar).name, "group": match.group("path").replace("/", "."),
                    "artifact": match.group("artifact2"), "version": match.group("version2")}
        return {"jar": Path(jar).name, "version": None}
    if module.startswith("sdk:"):
        return {"jdk": True, "version": None}
    return None


class Session:
    """One KotlinAsk process: its configuration, start time and memory, and one question at a time."""

    def __init__(self, java: str, jar: Path, config: Path, heap_mb: int = HEAP_MB):
        command = [java, f"-Xmx{heap_mb}m", "-Djava.awt.headless=true", "-cp",
                   os.pathsep.join(str(path) for path in runtime(jar)), "daodan.KotlinAskKt", str(config)]
        begun = time.time()
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
        self.answers = queue.Queue()
        self.errors: list[str] = []
        self.peak = 0
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._sample, daemon=True).start()
        threading.Thread(target=self._stderr, daemon=True).start()
        ready = self.answers.get(timeout=600)
        if not ready or not ready.startswith("READY"):
            raise RuntimeError(f"KotlinAsk did not start: {ready} {' '.join(self.errors[-20:])[-2000:]}")
        self.files = int(ready.split("\t")[1])
        self.start_seconds = round(time.time() - begun, 1)

    def _read(self):
        for row in self.process.stdout:
            self.answers.put(row.rstrip("\n"))
        self.answers.put(None)

    def _stderr(self):
        for row in self.process.stderr:
            self.errors.append(row.rstrip("\n")[:300])
            del self.errors[:-200]

    def ask(self, number: int, mode: str, path: Path, line: int, column: int) -> dict:
        self.process.stdin.write(f"{number}\t{mode}\t{path}\t{line}\t{column}\n")
        self.process.stdin.flush()
        answer = self.answers.get(timeout=TIMEOUT)
        if answer is None:
            raise RuntimeError("KotlinAsk exited: " + " ".join(self.errors[-10:])[-1500:])
        return json.loads(answer)

    def _sample(self):
        """The process's resident memory, sampled twice a second (gVisor's /proc has no VmHWM)."""
        while self.process.poll() is None:
            try:
                self.peak = max(self.peak, int(Path(f"/proc/{self.process.pid}/statm").read_text().split()[1])
                                * os.sysconf("SC_PAGE_SIZE"))
            except (OSError, ValueError, IndexError, AttributeError):
                return
            time.sleep(0.5)

    def peak_mb(self) -> int | None:
        return round(self.peak / 2 ** 20) if self.peak else None

    def close(self):
        try:
            self.process.stdin.close()
            self.process.wait(timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            self.process.kill()


def ask(project_dir: Path, work_dir: Path, sites: list[dict], configs: Path | None = None, java: str = JAVA) -> dict:
    """`{site: {"target", "external", "detail"}}` for each `{"site", "mode", "file", "line", "column"}`.

    `file` is checkout-relative; `column` counts UTF-16 units (0 for `implicit`). `target` lists the answers
    of every element found, `external` the jar of the first answer in a library, `detail` the raw elements or
    the error. The run's times and memory are written to `work_dir/kotlin-analysis.json`.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    begun = time.time()
    jar = build(java, work_dir)
    compiled = round(time.time() - begun, 1)
    tasks, root = modules(configs or work_dir / "kotlin-configs")
    base = Path(root) if root else Path(project_dir)
    config = work_dir / "kotlin-ask.txt"
    config.write_text("".join(f"module {task['name']}\n" + "".join(f"source {path}\n" for path in task["sources"])
                              + "".join(f"library {path}\n" for path in task["libraries"])
                              + "".join(f"depends {name}\n" for name in task["depends"]) for task in tasks),
                      encoding="utf-8")
    session = Session(java, jar, config)
    answers, asked = {}, time.time()
    try:
        for number, site in enumerate(sites):
            raw = session.ask(number, site["mode"], base / site["file"], site["line"], site.get("column", 0))
            targets = [target for element in raw["elements"] for target in element["targets"]]
            answers[site["site"]] = {"target": targets,
                                     "external": next((found for found in map(external, targets) if found), None),
                                     "detail": {"elements": raw["elements"], "error": raw["error"]}}
        peak = session.peak_mb()
    finally:
        session.close()
    engine = {"name": "kotlin-analysis-api", "version": _resolve_edges().KOTLIN_ANALYSIS.rsplit(":", 1)[1],
              "compile_seconds": compiled, "start_seconds": session.start_seconds,
              "question_seconds": round(time.time() - asked, 1), "questions": len(sites), "files": session.files,
              "peak_mb": peak, "heap_mb": HEAP_MB,
              "modules": [{"name": task["name"], "sources": len(task["sources"]), "libraries": len(task["libraries"]),
                           "depends": task["depends"]} for task in tasks],
              "stderr_tail": session.errors[-5:]}
    (work_dir / "kotlin-analysis.json").write_text(json.dumps(engine, indent=1), encoding="utf-8")
    return answers
