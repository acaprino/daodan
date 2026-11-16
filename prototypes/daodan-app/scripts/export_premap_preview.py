"""Export declared facts for the offline UI preview; never run project tools.

Languages, technologies and declared versions are Daodan's own: a snapshot of `plugins/` written to a temporary
folder, the `stack` step's record (`technologies.py`) and the pre-map's toolchains. Files, units and the versions
of their dependencies are read from Git and the manifests, which no record of Daodan holds yet.
"""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib


MOCKUP = Path(__file__).resolve().parents[1]
ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=MOCKUP, text=True).strip())


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT).decode("utf-8")


files = sorted(path for path in git("ls-files", "-z").split("\0") if path and (ROOT / path).is_file())
units = []
technologies = []

for path in files:
    if not path.startswith("plugins/") or Path(path).name not in ("plugin.toml", "package.json"):
        continue
    text = (ROOT / path).read_text(encoding="utf-8")
    data = tomllib.loads(text) if path.endswith(".toml") else json.loads(text)
    root = str(Path(path).parent).replace("\\", "/")
    unit = {"id": root, "name": data["name"], "root": root, "manifest": path,
            "kind": "plugin" if path.endswith(".toml") else "npm-package", "dependencies": []}
    if unit["kind"] == "npm-package":
        for scope in ("dependencies", "devDependencies"):
            for name, version in sorted(data.get(scope, {}).items()):
                unit["dependencies"].append({"name": name, "version": version, "scope": scope,
                                             "source": path, "state": "declared"})
    else:
        for name in data.get("dependencies", {}).get("required", []):
            unit["dependencies"].append({"name": name, "version": "", "scope": "plugin",
                                         "source": path, "state": "declared"})
    units.append(unit)

runtime = "plugins/codebase-map/skills/map/scripts/mcp_server.py"
text = (ROOT / runtime).read_text(encoding="utf-8")
block = text.split("# /// script", 1)[1].split("# ///", 1)[0]
metadata = tomllib.loads("\n".join(line.removeprefix("# ") for line in block.splitlines()))
runtime_root = str(Path(runtime).parent).replace("\\", "/")
units.append({"id": runtime, "name": "Runtime Codebase Map", "root": runtime_root,
              "manifest": runtime, "kind": "entrypoint", "dependencies": [
                  {"name": dependency, "version": "", "scope": "runtime", "source": runtime, "state": "declared"}
                  for dependency in metadata["dependencies"]]})
technologies.append({"name": "Python", "version": metadata["requires-python"], "category": "Runtime",
                     "source": runtime, "unit": runtime, "state": "declared"})
# What Daodan itself recognizes in `plugins/`, with no tool of the project run.
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))
import premap  # noqa: E402
import snapshot  # noqa: E402
import technologies as stack  # noqa: E402
from premap.suffix_table import NAMES  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

with tempfile.TemporaryDirectory(prefix="daodan-preview-") as work:
    manifest = Path(work) / "manifest.sqlite"
    snapshot.main(["write", str(ROOT / "plugins"), "--out", str(manifest), "--no-engine", "--no-index"])
    record, toolchains = stack.ensure(manifest), premap.ensure(manifest).get("toolchains", [])
    with open_snapshot(manifest) as store:
        counts = Counter(entry["language"] for _, entry in store.iter_file_headers_only() if entry.get("language"))
versions = {(unit["root"], dependency["name"]): dependency["version"] for unit in units for dependency in unit["dependencies"]}
known = {entry["id"]: entry for entry in record["technologies"]}
for found in record["units"]:
    owned = tuple(path.rstrip("/") + "/" for path in found["paths"])
    for ident in found["technologies"]:
        sign = next(s for s in known[ident]["signs"] if s["path"].startswith(owned))
        technologies.append({"name": known[ident]["name"], "category": {None: "tecnologia", "altro": "tecnologia"}.get(known[ident]["type"], known[ident]["type"]),
                             "version": versions.get((found["paths"][0], sign["value"]), ""),
                             "source": sign["path"] + (f":{sign['line']}" if sign["line"] else ""),
                             "unit": found["paths"][0], "state": "recognized"})
for item in toolchains:
    technologies.append({"name": item["tool"], "version": item["version"], "category": "Versione dichiarata",
                         "source": item["declared_in"] + (f":{item['line']}" if item.get("line") else ""),
                         "unit": str(Path(item["declared_in"].split("#")[0]).parent).replace("\\", "/"), "state": "declared"})
for unit in units:
    parents = [other for other in units if other is not unit and unit["root"].startswith(other["root"] + "/")]
    unit["parent"] = max(parents, key=lambda other: len(other["root"]))["id"] if parents else None

result = {"source": {"kind": "git-inventory-and-declared-manifests", "root": ROOT.as_posix(),
                     "commit": git("rev-parse", "--short", "HEAD").strip(),
                     "captured_at": datetime.now(timezone.utc).isoformat(), "files_count": len(files),
                     "notice": "Inventario Git tracciato e manifesti correnti. Anteprima dichiarativa: nessuna build o analisi eseguita; grafo storico separato."},
          "files": files, "languages": [{"name": NAMES.get(name, name.capitalize()), "files": count, "source": "Snapshot di Daodan sulla cartella plugins"}
                                         for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))],
          "units": units, "technologies": technologies,
          "gaps": ["Linguaggi e tecnologie dallo snapshot di plugins: benchmark, test e documenti restano fuori.",
                   "Tecnologie riconosciute dal registro di Daodan per unità di build; versioni installate e uso effettivo non verificati.",
                   "I compiler Vue/Svelte/Astro appartengono al tooling di analisi, non dichiarano il framework dell'app.",
                   "La pre-mappa canonica non contiene librerie risolte: la UI compone inventario e dichiarazioni, da aggiornare con i risultati degli analyzer.",
                   "Il grafo dimostrativo usa uno snapshot storico distinto; i conteggi non descrivono una nuova analisi."]}
output = MOCKUP / "assets/premap-preview.json"
assert result["files"] and len({unit["id"] for unit in units}) == len(units)
assert all(dependency["state"] == "declared" for unit in units for dependency in unit["dependencies"])
rendered = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
page = MOCKUP / "index.html"
html = page.read_text(encoding="utf-8")
marker = '<script id="premap-data" type="application/json">'
before, existing = html.split(marker, 1)
_, after = existing.split("</script>", 1)
output.write_text(rendered, encoding="utf-8")
page.write_text(before + marker + rendered.replace("<", "\\u003c") + "</script>" + after, encoding="utf-8")
print(json.dumps({"output": output.as_posix(), "files": len(files), "languages": len(counts),
                  "units": len(units), "technologies": len(technologies),
                  "declared_dependencies": sum(len(unit["dependencies"]) for unit in units)}))
