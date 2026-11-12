"""The inputs of the phase-3 runs, derived from one `flows.py links` result: perimeter, units (B) and flows (C).

Perimeter: the home widgets, the insert sheet, the home controller and the hooks they call up to two
levels, and the writers of every store those files read. Units: `flows.units` with share 2 and a
limit of 120,000 bytes. Flows: per store read inside the perimeter, its writers and readers inside
it with their sites, under a cap of 12,000 characters.

    python benchmarks/phazly-flow/phase3/inputs.py LINKS.json [--out benchmarks/phazly-flow/phase3]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "plugins/codebase-map/skills/map/scripts"))
import flows  # noqa: E402

LIMIT, SHARE, CAP = 120_000, 2, 12_000


def is_test(path: str) -> bool:
    return ".test." in path or "/__tests__/" in path or "/test/" in path


def perimeter_of(links: dict) -> list[str]:
    sizes = links["sizes"]
    core = {f for f in sizes if f.startswith("react-app/src/components/home/") and not is_test(f)}
    core |= {"react-app/src/components/common/QuickAddSheet.tsx", "react-app/src/hooks/useHomeTabController.ts"}
    core |= {f for f in sizes if f.startswith("react-app/src/components/tabs/HomeTab") and not is_test(f)}
    readers, frontier = set(core), set(core)
    for _ in range(2):
        reached = {e["to"].split("::")[0] for e in links["edges"] if e["type"] == "chiama"
                   and e["from"].split("::")[0] in frontier and e["to"].split("::")[0].startswith("react-app/src/hooks/")
                   and not is_test(e["to"])} - readers
        readers |= reached
        frontier = reached
    writers = set()
    for store in links["stores"].values():
        if any(reader.split("::")[0] in readers for reader in store["reads"]):
            writers |= {w.split("::")[0] for w in store["writes"] if w.startswith("react-app/src/") and not is_test(w)}
    return sorted(readers | writers)


def flows_text(links: dict, perimeter: list[str]) -> str:
    site = {}
    for edge in links["edges"]:
        if edge["type"] == "scrive":
            site.setdefault((edge["from"], edge["to"]), edge["site"])
        if edge["type"] == "legge":
            site.setdefault((edge["to"], edge["from"]), edge["site"])
    inside = set(perimeter)
    lines = ["# Flussi che attraversano il perimetro", "",
             "Ricavati da `flows.py` (regole di collegamento di phazly, collegamenti con il motore). Per ogni dato letto nel "
             "perimetro: chi lo scrive e chi lo legge, con il punto del codice. Granularità e significato non sono etichettati.", ""]
    for key, store in sorted(links["stores"].items(), key=lambda item: -len(item[1]["reads"])):
        readers = [r for r in store["reads"] if r.split("::")[0] in inside]
        writers = [w for w in store["writes"] if w.split("::")[0] in inside]
        if not readers or not writers:
            continue
        lines.append(f"## `{key}`")
        lines.append("- scrivono: " + "; ".join(f"`{w.split('::')[1]}` ({site.get((w, 'store:' + key), w.split('::')[0])})" for w in writers))
        lines.append("- leggono: " + "; ".join(f"`{r.split('::')[1]}` ({site.get((r, 'store:' + key), r.split('::')[0])})" for r in readers))
        lines.append("")
    text = "\n".join(lines)
    if len(text) > CAP:
        text = text[:text.rfind("\n## ", 0, CAP)] + f"\n\n(Elenco troncato al tetto di {CAP:,} caratteri.)\n".replace(",", ".")
    return text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("links", type=Path)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args(argv)
    links = json.loads(args.links.read_text(encoding="utf-8"))
    perimeter = perimeter_of(links)
    units = flows.units(links, {f: links["sizes"][f] for f in perimeter}, perimeter, LIMIT, share=SHARE)
    (args.out / "perimeter.txt").write_text("\n".join(perimeter) + "\n", encoding="utf-8", newline="\n")
    (args.out / "units.json").write_text(json.dumps([unit["files"] for unit in units["units"]], indent=1) + "\n",
                                         encoding="utf-8", newline="\n")
    (args.out / "flows.md").write_text(flows_text(links, perimeter), encoding="utf-8", newline="\n")
    print(f"perimeter {len(perimeter)} files, {len(units['units'])} units, assigned {units['assigned']}/{units['files']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
