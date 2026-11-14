"""Write ANAGRAFICA.md, the registry of the corpus, from cases.json and fixtures/*/expected.json.

python catalog.py          write ANAGRAFICA.md
python catalog.py --check  exit 1 when ANAGRAFICA.md differs from what this script writes
Standard library only.
"""

from __future__ import annotations

import json
import sys
from collections import Counter

import score

OUT = score.HERE / "ANAGRAFICA.md"
RESEARCH = "../../docs/research/2026-11-14-project-model-detection.md"


def load():
    docs, sources = {}, {}
    for name in score._fixtures("all"):
        d = score.FIXTURES / name
        docs[name] = json.loads((d / "expected.json").read_text(encoding="utf-8"))
        if (d / "source.json").exists():
            sources[name] = json.loads((d / "source.json").read_text(encoding="utf-8"))
    return score.load_domain(), docs, sources


def _list(values, empty):
    return ", ".join(values) if values else empty


def _unique(values):
    return sorted({v for v in values if v}, key=str.lower)


def _origin(source):
    if not source:
        return "scritto a mano per il benchmark"
    repo = source["repo"]
    shown = repo.split("://", 1)[-1].removesuffix(".git")
    licence = f"licenza {source['licence']}" if source.get("licence") else "licenza non indicata in source.json"
    return f"[{shown}]({repo}) al commit `{source['commit']}`, {licence}"


def _units(doc):
    kinds = Counter(u.get("kind") for u in doc.get("units") or [])
    return _list([f"{k} ({n})" if n > 1 else k for k, n in sorted(kinds.items())], "nessuna")


def _workspaces(doc):
    ws = doc.get("workspace")
    ws = ws if isinstance(ws, list) else [ws] if ws else []
    return _list(_unique(w.get("tool") for w in ws), "nessuno")


def _dependency_files(doc):
    return _list(_unique(score._file(x.get("declared_in")) for x in doc.get("dependencies") or []), "nessuno")


def _versions(doc):
    per_tool = {}
    for t in doc.get("toolchains") or []:
        version = t.get("version") if t.get("version") is not None else "senza versione"
        per_tool.setdefault(t.get("tool"), []).append(f"{version} (`{t.get('declared_in')}`)")
    return [f"  - {tool}: {'; '.join(v)}" for tool, v in sorted(per_tool.items(), key=lambda x: str(x[0]).lower())]


def render(domain, docs, sources):
    by_id = {c["id"]: c for c in domain["cases"]}
    cover = score.coverage(docs, domain)
    titles = {g["id"]: g["title"] for g in domain["groups"]}
    out = ["# Anagrafica del corpus", "",
           "Scritta da `catalog.py` con [cases.json](cases.json) e i `fixtures/*/expected.json`: non si modifica a mano.",
           "Si rigenera con `python catalog.py`.", "",
           f"{len(docs)} progetti, {len(domain['cases'])} casi in {len(domain['groups'])} gruppi.", "",
           "## Dominio dei casi", "",
           "Assegnazione: \"dai dati\" se il caso segue da `expected.json`, e `python score.py --check all` fallisce "
           "quando la lista e i dati non concordano; \"letto\" se l'ha assegnato chi ha letto i file della fixture.",
           f"Incidente misurato: il caso misurato nella [ricerca]({RESEARCH}), §3.2, da cui il caso viene.", "",
           "| Gruppo | Caso | Definizione | Progetti | Assegnazione | Incidente misurato |",
           "| --- | --- | --- | --- | --- | --- |"]
    for c in domain["cases"]:
        how = "dai dati" if c["id"] in score.DERIVED else "letto"
        out.append(f"| {titles[c['group']]} | `{c['id']}` | {c['definition']} | {len(cover[c['id']])} | {how} "
                   f"| {c.get('measured', '')} |")
    out += ["", "## Progetti"]
    for family in score.FAMILIES:
        names = [n for n in docs if n.split("-", 1)[0] == family]
        out += ["", f"### {family} ({len(names)} progetti)"]
        for name in names:
            doc = docs[name]
            versions = _versions(doc)
            out += ["", f"#### {name}", "",
                    f"- Origine: {_origin(sources.get(name))}.",
                    f"- Linguaggi: {_list(_unique(x.get('language') for x in doc.get('languages') or []), 'nessuno')}.",
                    f"- Unità: {_units(doc)}.",
                    f"- Workspace: {_workspaces(doc)}.",
                    f"- File delle dipendenze: {_dependency_files(doc)}.",
                    "- Versioni dichiarate:" + ("" if versions else " nessuna.")] + versions + [
                    f"- Framework: {_list(_unique(f.get('name') for f in doc.get('frameworks') or []), 'nessuno')}.",
                    f"- Servizi: {_list(_unique(s.get('name') for s in doc.get('services') or []), 'nessuno')}.",
                    "- Casi:"]
            listed = set(doc.get("cases") or [])
            out += [f"  - `{c['id']}`: {c['definition']}" for c in domain["cases"] if c["id"] in listed]
    out += ["", "## Copertura", "", "### Progetti per caso", ""]
    out += [f"- `{cid}` ({len(names)}): {_list(names, 'nessuno')}" for cid, names in cover.items()]
    few = [(cid, names) for cid, names in cover.items() if len(names) < 2]
    out += ["", "### Casi con meno di due progetti", ""]
    out += [f"- `{cid}`: {_list(names, 'nessun progetto')}" for cid, names in few] or ["Nessuno."]
    return "\n".join(out) + "\n"


def main(argv):
    text = render(*load())
    if argv == ["--check"]:
        same = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("ANAGRAFICA.md: up to date" if same else "ANAGRAFICA.md: differs, run python catalog.py")
        return 0 if same else 1
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {OUT.name}: {len(text.splitlines())} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
