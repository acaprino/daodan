"""scip-java for Kotlin on Modal: the plugin's `indexers.kotlin` steps, run by `jvm_here` in the function's own
container, where no container engine runs. How the index is built and what it leaves to the reader is the
plugin's `indexers/kotlin.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import plugin_scripts  # noqa: E402,F401  (puts the plugin's scripts on the path)
from adapters import jvm_here  # noqa: E402
from indexers import jvm  # noqa: E402
from indexers import kotlin as plugin  # noqa: E402

VERSION = jvm.VERSION


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None) -> dict:
    """The plugin's contract for the checkout, built here; `refused` lists the hosts the registry proxy refused."""
    result, runs, out = jvm_here.run(project_dir, work_dir, plugin.PREPARE, plugin.EXECUTE)
    return {**plugin.finish(Path(work_dir), result, runs, out), "refused": result["refused"]}
