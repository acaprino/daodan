"""Daodan's pre-map (`scripts/premap/`), read as it is: the record is already in the shared shape.

`snapshot.py write <fixture> --no-engine --no-index` builds the snapshot and `modules.json` beside it, as the
plugin does; `premap.write` then joins its readers. Model commands run only in a container: this adapter leaves
them `not_run`, and `modal_premap.py --score` runs them on Modal. Only the facets the pre-map gives are present;
each file's language stays in the snapshot, so `languages.files` is not given.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import native_common as common

SCRIPTS = next((p / "plugins/codebase-map/skills/map/scripts" for p in Path(__file__).resolve().parents
                if (p / "plugins/codebase-map/skills/map/scripts").is_dir()), Path("/daodan/map/scripts"))
VERSION = "premap of the checkout (daodan/premap/v1)"
COMMAND = "snapshot.py write <fixture> --out <work>/manifest.sqlite --no-engine --no-index; premap.write(manifest)"
FACETS = ("languages", "excluded", "units", "workspace", "toolchains", "dependencies")
LAST: dict = {}


def run(fixture_dir, work_dir) -> dict:
    manifest = Path(work_dir) / "daodan" / "manifest.sqlite"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    done = common.run([sys.executable, "-I", str(SCRIPTS / "snapshot.py"), "write", str(fixture_dir), "--out",
                       str(manifest), "--no-engine", "--no-index"], SCRIPTS, name="snapshot.py write (premap)")
    if not manifest.is_file():
        raise RuntimeError(f"snapshot.py write exit {done.returncode}: {done.stderr[-600:]}")
    script = (f"import sys, json; sys.path.insert(0, {str(SCRIPTS)!r}); import premap; "
              f"premap.write({str(manifest)!r})")
    wrote = common.run([sys.executable, "-I", "-c", script], SCRIPTS, name="premap.write")
    target = manifest.with_name("premap.json")
    if not target.is_file():
        raise RuntimeError(f"premap.write exit {wrote.returncode}: {wrote.stderr[-600:]}")
    record = json.loads(target.read_text(encoding="utf-8"))
    LAST.clear()
    LAST.update(sources=record["sources"], gaps=record["gaps"][:20])
    return {facet: record[facet] for facet in FACETS if facet in record}
