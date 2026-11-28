"""Le sorgenti dei framework che lo stack sceglie contro quelle che girano oggi (T1.C.5).

Oggi una sorgente di `entry_points.SOURCES` che `registry_build.READERS` nomina lavora dove un `package.json` dichiara uno dei suoi
`PACKAGES` (`frameworks.folders`). Con lo stack gira solo se `results/daodan_stack.json` ha trovato un id di READERS che la nomina
(`entry_points._chosen` sugli `ids` della fixture). Una perdita è una sorgente che lavora oggi e che lo stack non sceglie.

Le fixture con i file nel repository si leggono con l'inventario di Daodan (`file_inventory.write`, poi `premap.Context`, come la
sorgente li legge); quelle clonate (`source.json`) solo dove `results/daodan_premap_corpus.json` ha le loro dipendenze npm, dal
`package.json` che le dichiara. Ogni perdita ammessa sta in ACCEPTED con la causa; oggi nessuna.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "daodan" / "core"))

import entry_points  # noqa: E402
import file_inventory  # noqa: E402
import premap  # noqa: E402
from entry_points import frameworks  # noqa: E402
from registry_build import READERS  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

FIXTURES, RESULTS = HERE / "fixtures", HERE / "results"
NAMED = tuple(s for s in entry_points.SOURCES if entry_points._reader(s) in READERS.values())
ACCEPTED: dict[tuple[str, str], str] = {}  # (fixture, sorgente): causa


def _committed(name: str, out: Path) -> set[str]:
    """Le sorgenti che lavorano oggi su una fixture con i file nel repository."""
    manifest = out / name / "inventory.sqlite"
    manifest.parent.mkdir(parents=True)
    file_inventory.write(FIXTURES / name, manifest)
    with open_snapshot(manifest) as store:
        context = premap.Context(manifest, store)
        return {s.NAME for s in NAMED if frameworks.folders(context, s.PACKAGES)}


def _cloned(output: dict) -> set[str]:
    """Le sorgenti che lavorano oggi su una fixture clonata, dalle dipendenze della pre-mappa misurata."""
    declared = {d["name"] for d in output.get("dependencies") or ()
                if PurePosixPath(d.get("declared_in") or "").name == "package.json"}
    return {s.NAME for s in NAMED if declared & set(s.PACKAGES)}


def measure(out: Path) -> dict:
    """Per fixture: le sorgenti di oggi, quelle dello stack, e le perdite."""
    stack = json.loads((RESULTS / "daodan_stack.json").read_text(encoding="utf-8"))["fixtures"]
    premapped = json.loads((RESULTS / "daodan_premap_corpus.json").read_text(encoding="utf-8"))
    found = {}
    for name, run in sorted(stack.items()):
        folder = FIXTURES / name
        if (folder / "source.json").is_file():
            if "output" not in premapped.get(name, {}):
                continue  # clonata e senza pre-mappa misurata: non misurata
            today = _cloned(premapped[name]["output"])
        elif any(folder.rglob("package.json")):
            today = _committed(name, out)
        else:
            today = set()
        chosen = {s.NAME for s in entry_points._chosen(NAMED, run.get("ids"))}
        found[name] = {"today": sorted(today), "stack": sorted(chosen), "lost": sorted(today - chosen)}
    return found


def test_the_stack_loses_no_framework_source(tmp_path):
    found = measure(tmp_path)
    lost = [(name, source) for name, row in found.items() for source in row["lost"] if (name, source) not in ACCEPTED]
    print(json.dumps({name: row for name, row in found.items() if row["today"] or row["stack"]}, indent=1))
    print(f"fixture misurate: {len(found)}; con una sorgente oggi: {sum(bool(r['today']) for r in found.values())}")
    assert not lost, f"sorgenti perse: {lost}"
