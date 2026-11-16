"""Export declared facts for the offline UI preview; never run project tools."""

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tomllib


MOCKUP = Path(__file__).resolve().parents[1]
ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=MOCKUP, text=True).strip())


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT).decode("utf-8")


files = sorted(path for path in git("ls-files", "-z").split("\0") if path and (ROOT / path).is_file())
extensions = {".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
              ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".css": "CSS",
              ".html": "HTML", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
              ".c": "C", ".h": "C/C++", ".cpp": "C++", ".hpp": "C++", ".cs": "C#",
              ".vue": "Vue template", ".svelte": "Svelte template", ".astro": "Astro template"}
counts = Counter(extensions[Path(path).suffix] for path in files if Path(path).suffix in extensions)
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
                if root.endswith("/viewer") and name in ("react", "vite", "@xyflow/react", "elkjs"):
                    technologies.append({"name": {"react": "React", "vite": "Vite", "@xyflow/react": "React Flow", "elkjs": "ELK"}[name],
                                         "version": version, "category": "UI" if name == "react" else "Build" if name == "vite" else "Grafo",
                                         "source": path, "unit": root, "state": "declared"})
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
for unit in units:
    parents = [other for other in units if other is not unit and unit["root"].startswith(other["root"] + "/")]
    unit["parent"] = max(parents, key=lambda other: len(other["root"]))["id"] if parents else None

result = {"source": {"kind": "git-inventory-and-declared-manifests", "root": ROOT.as_posix(),
                     "commit": git("rev-parse", "--short", "HEAD").strip(),
                     "captured_at": datetime.now(timezone.utc).isoformat(), "files_count": len(files),
                     "notice": "Inventario Git tracciato e manifesti correnti. Anteprima dichiarativa: nessuna build o analisi eseguita; grafo storico separato."},
          "files": files, "languages": [{"name": name, "files": count, "source": "Estensioni dei file tracciati, comprese fixture e benchmark"}
                                         for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))],
          "units": units, "technologies": technologies,
          "gaps": ["Linguaggi da estensioni: la presenza nelle fixture non dimostra uso nel prodotto.",
                   "Framework e dipendenze dichiarati nei manifesti dei plugin; versioni installate e uso effettivo non verificati.",
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
