"""The Kotlin Analysis API asked only where the whole-project index is uncertain or silent.

`ask` starts one standalone session of the plugin's `indexers/KotlinAsk.kt` (one source module per compile task,
read from the `kotlin-configs/` scip-java dumped, one library module per jar, a description of each answer) and
asks each site:
- `ref`: the reference at a position, the occurrence of a name;
- `implicit`: every implicit operator call on a line (`x[k]`, `x[k] = v`, the `for` iterator, `by` delegates,
  `componentN`), with the role of each;
- `overridden`: what the declaration at a position overrides.

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

JAVA = "/opt/jdk/bin/java"  # the JDK of adapters/kotlin.py
HEAP_MB = 3072
TIMEOUT = 120
CACHED = re.compile(r"/files-2\.1/(?P<group>[^/]+)/(?P<artifact>[^/]+)/(?P<version>[^/]+)/[0-9a-f]+/[^/]+\.jar$"
                    r"|/repository/(?P<path>.+)/(?P<artifact2>[^/]+)/(?P<version2>[^/]+)/[^/]+\.jar$")


def _resolve_edges():
    import resolve_edges
    return resolve_edges


def _source() -> Path:
    from indexers import kotlin
    return kotlin.SOURCE


def build(java: str, work_dir: Path) -> Path:
    """KotlinAsk.kt compiled once against the Analysis API the map pins, cached by the source's digest."""
    edges = _resolve_edges()
    source = _source()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
    jar = Path(work_dir) / f"kotlin-ask-{edges.KOTLIN_ANALYSIS[0].rsplit(':', 1)[1]}-{digest}.jar"
    if jar.is_file():
        return jar
    compiler = os.pathsep.join(str(edges.maven_artifact(*item)) for item in edges.KOTLIN_COMPILER)
    classpath = os.pathsep.join(str(path) for path in runtime(None)[1:])
    command = [java, "-Xmx1g", "-cp", compiler, "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler", str(source),
               "-classpath", classpath, "-d", str(jar), "-jvm-target", "17", "-no-stdlib", "-no-reflect",
               "-Xskip-prerelease-check", *[f"-opt-in=org.jetbrains.kotlin.analysis.api.{name}"
                                            for name in edges.KOTLIN_OPT_INS]]
    done = subprocess.run(command, capture_output=True, text=True, timeout=900)
    if done.returncode != 0 or not jar.is_file():
        raise RuntimeError("KotlinAsk.kt did not compile: " + (done.stderr or done.stdout)[-1500:])
    return jar


def runtime(jar: Path | None) -> list:
    edges = _resolve_edges()
    return [jar, *(edges.maven_artifact(*item) for item in (edges.KOTLIN_ANALYSIS, *edges.KOTLIN_RUNTIME))]


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
    """One KotlinAsk process over a `kotlin-configs/` folder: its start time and memory, one question at a time."""

    def __init__(self, java: str, jar: Path, configs: Path, heap_mb: int = HEAP_MB):
        command = [java, f"-Xmx{heap_mb}m", "-Djava.awt.headless=true", "-cp",
                   os.pathsep.join(str(path) for path in runtime(jar)), "daodan.KotlinAskKt", str(configs)]
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
        _ready, files, modules, self.root = ready.split("\t", 3)
        self.files, self.modules = int(files), int(modules)
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
    session = Session(java, jar, configs or work_dir / "kotlin-configs")
    base = Path(session.root) if session.root else Path(project_dir)
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
    engine = {"name": "kotlin-analysis-api", "version": _resolve_edges().KOTLIN_ANALYSIS[0].rsplit(":", 1)[1],
              "compile_seconds": compiled, "start_seconds": session.start_seconds,
              "question_seconds": round(time.time() - asked, 1), "questions": len(sites), "files": session.files,
              "modules": session.modules, "peak_mb": peak, "heap_mb": HEAP_MB, "stderr_tail": session.errors[-5:]}
    (work_dir / "kotlin-analysis.json").write_text(json.dumps(engine, indent=1), encoding="utf-8")
    return answers
