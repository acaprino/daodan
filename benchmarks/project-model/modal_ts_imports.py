"""What the configuration of `tsc` adds to the imports Daodan resolves (spec 8.3 point 4, 8.11 step 5 piece F), on Modal.

Nothing of a project runs: its files are read, and TypeScript's own API (`ts.getParsedCommandLineOfConfigFile`, as
`tools/native_tsc_config.cjs` of F1) reads each `tsconfig*.json` and `jsconfig*.json` of the snapshot with the files it
keeps (`tools/ts_imports_config.cjs`); no package is restored, so an `extends` into a `node_modules` that is not there is a
declared error and that config does not count. The Daodan code is the clone of HEAD that `DAODAN_SCRIPTS` names, as
`modal_pipeline.py` uploads it.

Per project, `import_resolution` resolves the specifiers of every file twice:

- before: as the product does today (`ts_path_config`: the `paths` and `baseUrl` of the nearest folder with a
  `tsconfig.json` or `jsconfig.json`);
- after: the settings of the config that holds the importer (`baseUrl ?? pathsBasePath` as the base of its `paths`), and the
  hand reading for the files no config lists. The config of a file is one of the files tsc lists for it (`fileNames`), never
  the nearest folder's; of several, the one tsserver opens the file in (`src/server/editorServices.ts`, TypeScript 6.0.3:
  `forEachConfigFileLocation`, from the file's folder up, a `tsconfig.json` then a `jsconfig.json` in each; then
  `tryFindDefaultConfiguredProjectForOpenScriptInfoOrClosedFileInfo`: that config if it lists the file, else its project
  references in order and theirs, else the config of the folders above). A file several configs list that no such walk reaches is
  counted as ambiguous and goes to the deepest config, then the first by name.

The pairs (importer, specifier) are the same, unresolved in both, gained (no target before, one now), lost or changed; for each
kind the distinct file edges and the edges between modules (`module_derive.derive` on the snapshot, no pre-map) that change; a
gained pair says whether a `paths` pattern or a plain `baseUrl` made it (`hit_kind`).

    PYTHONUTF8=1 python -m modal run benchmarks/project-model/modal_ts_imports.py --cases js-angular,js-vite-react-ts,js-nx
    DAODAN_SCRIPTS=<clean clone of HEAD>/daodan/core python -m modal run benchmarks/project-model/modal_ts_imports.py

A project with no `tsconfig*.json` or `jsconfig*.json` is left out (`skipped`): the two resolutions are the same by construction.
The function has a fixed machine; each real project has a call of its own. The result lands in `results/ts-imports/ts-imports.json`:
counts, and at most five examples per project; no source.
"""
from __future__ import annotations

import collections
import json
import os
import posixpath
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import NamedTuple

import modal

import modal_pipeline as mp

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/ts-imports/ts-imports.json"
ARCHIVES = Path("/results/project-model/native-real")  # the volume: a real repository's archive, as `modal_native.py prepare` keeps it
NODE_HOME = "/opt/node"
TYPESCRIPT = f"{NODE_HOME}/lib/node_modules/typescript"  # TypeScript 6.0.3, the pin of `modal_native.py` and of F1
SCRIPT = f"{mp.REMOTE_PM}/ts_imports_config.cjs"
CPU, MEMORY, TIMEOUT = 4.0, 16384, 4 * 3600
BATCH = 100  # configs per `node` call: the length of a command line
EXAMPLES = 5
KINDS = ("same", "unresolved", "gained", "lost", "changed")
NODE_INSTALL = (  # as `modal_native.INSTALL_MAIN`: Node v22.23.4 checked by its sha256, then typescript 6.0.3 for it
    "cd /tmp && curl -fsSLO https://nodejs.org/dist/v22.23.4/node-v22.23.4-linux-x64.tar.xz"
    " && curl -fsSLO https://nodejs.org/dist/v22.23.4/SHASUMS256.txt"
    " && grep ' node-v22.23.4-linux-x64.tar.xz$' SHASUMS256.txt | sha256sum -c -"
    f" && tar -C /opt -xJf node-v22.23.4-linux-x64.tar.xz && mv /opt/node-v22.23.4-linux-x64 {NODE_HOME}"
    " && rm node-v22.23.4-linux-x64.tar.xz SHASUMS256.txt"
    f" && PATH={NODE_HOME}/bin:$PATH npm install -g --no-fund --no-audit typescript@6.0.3")

# the packages of `modal_pipeline.image`, with Node and TypeScript under them: its layers cannot be built on after its mounts
image = (modal.Image.debian_slim(python_version="3.13")
         .apt_install("git", "ca-certificates", "xz-utils", "curl")
         .pip_install("tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30", "PyYAML>=6")
         .run_commands(NODE_INSTALL)
         .env({"PATH": f"{NODE_HOME}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"}))
if mp.LOCAL:
    image = (image.add_local_dir(mp.UPLOADED[0][0], mp.REMOTE_SCRIPTS, ignore=["**/__pycache__/**"])
             .add_local_dir(mp.UPLOADED[1][0], mp.REMOTE_DATA)
             .add_local_dir(mp.UPLOADED[2][0], f"{mp.REMOTE_PM}/fixtures")
             .add_local_file(mp.UPLOADED[3][0], f"{mp.REMOTE_PM}/score.py")
             .add_local_file(HERE / "modal_pipeline.py", "/root/modal_pipeline.py")
             .add_local_file(HERE / "tools/ts_imports_config.cjs", SCRIPT))
app = modal.App("daodan-ts-imports")


# ------------------------------------------------------------------ the pure part: which config holds a file

class Owner(NamedTuple):
    config: str | None  # the tsconfig or jsconfig whose settings the file has
    how: str  # none (no config lists it), one, many (several list it, tsserver's walk picked), unreached (several, no walk did)
    held: list  # every config that lists it, sorted


def is_config(rel: str) -> bool:
    """A `tsconfig*.json` or `jsconfig*.json` that is not inside a `node_modules`."""
    *folders, name = rel.split("/")
    return "node_modules" not in folders and name.endswith(".json") and name.startswith(("tsconfig", "jsconfig"))


def config_chain(file: str, configs, no_ancestors=frozenset()) -> list[str]:
    """The configs tsserver tries for `file`, nearest first: from the file's folder up, a `tsconfig.json` and then a
    `jsconfig.json` where one exists (`forEachConfigFileLocation`); the climb ends after a config that disables
    solution searching (`forEachAncestorProjectLoad`)."""
    chain, folder = [], posixpath.dirname(file)
    while True:
        for name in ("tsconfig.json", "jsconfig.json"):
            config = posixpath.join(folder, name)
            if config in configs:
                chain.append(config)
                if config in no_ancestors:
                    return chain
        if not folder:
            return chain
        folder = posixpath.dirname(folder)


def _referenced(start: str, file: str, tsc: dict) -> str | None:
    """The first project reference of `start`, in order, that lists `file`, then those of the references that did not
    (`forEachResolvedProjectReferenceProjectLoad`), each config once; none when `start` disables reference loading."""
    seen = set()

    def visit(config):
        if config in tsc["no_references"]:
            return None
        children = []
        for reference in tsc["references"].get(config, ()):
            if reference in seen or reference not in tsc["files_of"]:
                continue
            if file in tsc["files_of"][reference]:
                return reference
            seen.add(reference)
            children.append(reference)
        for child in children:
            found = visit(child)
            if found:
                return found
        return None

    return visit(start)


def default_config(file: str, tsc: dict) -> str | None:
    """The config tsserver opens `file` in: the nearest one that lists it or whose references do, else the next above."""
    for config in config_chain(file, set(tsc["files_of"]), tsc["no_ancestors"]):
        if file in tsc["files_of"][config]:
            return config
        found = _referenced(config, file, tsc)
        if found:
            return found
    return None


def owner_of(file: str, tsc: dict) -> Owner:
    """`tsc` is `{files_of: {config: set of files it lists}, references: {config: [configs]}, no_references, no_ancestors}`."""
    held = sorted(config for config, files in tsc["files_of"].items() if file in files)
    if not held:
        return Owner(None, "none", [])
    if len(held) == 1:
        return Owner(held[0], "one", held)
    found = default_config(file, tsc)
    if found:
        return Owner(found, "many", held)
    return Owner(min(held, key=lambda config: (-config.count("/"), config)), "unreached", held)


def settings_of(entry: dict) -> dict:
    """What `import_resolution.ts_path_config` keeps of a config (`baseUrl` and `paths` with absolute targets), from what
    tsc says: its `paths` against `baseUrl`, or else against `pathsBasePath`, the folder of the file that declares them."""
    found, base = {}, entry.get("baseUrl")
    if base:
        found["baseUrl"] = base
    where = base or entry.get("pathsBasePath")
    if isinstance(entry.get("paths"), dict) and where:
        found["paths"] = {pattern: [posixpath.normpath(posixpath.join(where, target)) for target in targets
                                    if isinstance(target, str)]
                          for pattern, targets in entry["paths"].items() if isinstance(targets, list)}
    return found


# ------------------------------------------------------------------ the pure part: the comparison

def classify_pairs(before: dict, after: dict, scope=None) -> dict:
    """The (importer, specifier) pairs of two resolutions (`{importer: {specifier: [targets]}}`): how many are the `same`,
    `unresolved` in both, `gained`, `lost` or `changed`, and each of the last three as (importer, specifier, before, after)."""
    counts, pairs = dict.fromkeys(KINDS, 0), {"gained": [], "lost": [], "changed": []}
    for importer in sorted(set(before) | set(after)):
        if scope is not None and importer not in scope:
            continue
        old, new = before.get(importer, {}), after.get(importer, {})
        for specifier in sorted(set(old) | set(new)):
            x, y = old.get(specifier, []), new.get(specifier, [])
            if x == y:
                counts["same" if x else "unresolved"] += 1
                continue
            kind = "gained" if not x else "lost" if not y else "changed"
            counts[kind] += 1
            pairs[kind].append((importer, specifier, x, y))
    return {"counts": counts, "pairs": pairs}


def file_edges(resolved: dict, scope=None) -> set:
    """The distinct (importer, target) file pairs of a resolution."""
    return {(importer, target) for importer, specifiers in resolved.items() if scope is None or importer in scope
            for targets in specifiers.values() for target in targets}


def edge_changes(before: set, after: set) -> dict:
    return {"before": len(before), "after": len(after), "gained": len(after - before), "lost": len(before - after)}


def module_edges(edges, owners: dict) -> set:
    """The (module, module) pairs the file edges make, a module to itself left out; a file with no owner makes none."""
    return {(source, destination) for importer, target in edges for source in owners.get(importer, ())
            for destination in owners.get(target, ()) if source != destination}


def examples(found: dict, via: dict | None = None, limit: int = EXAMPLES, owners: dict | None = None) -> list[dict]:
    """At most `limit` of the lost, changed and gained pairs, one kind after the other, each in the order it came; with
    `owners` (`{importer: Owner}`) each says which config its importer has and which ones list it."""
    queues = [(kind, list(found[kind])) for kind in ("lost", "changed", "gained")]
    shown = []
    while len(shown) < limit and any(queue for _, queue in queues):
        for kind, queue in queues:
            if queue and len(shown) < limit:
                importer, specifier, before, after = queue.pop(0)
                shown.append({"kind": kind, "importer": importer, "specifier": specifier, "before": before,
                              "after": after, "via": (via or {}).get((importer, specifier))})
                if owners is not None:
                    shown[-1].update(config=owners[importer].config, held=owners[importer].held)
    return shown


def hit_kind(resolver, importer: str, module: str, settings: dict) -> str | None:
    """Where the first candidate that resolves comes from, in the order `_ImportResolver.script_candidates` tries them: a
    `paths` pattern, the plain `baseUrl`, or a workspace package; `relative` for a path that starts with a dot."""
    import import_resolution
    if module.startswith("."):
        return "relative"
    groups = (("paths", import_resolution._expand_alias(module, settings.get("paths"))),
              ("baseUrl", [(Path(settings["baseUrl"]) / module).as_posix()] if "baseUrl" in settings else []),
              ("packages", import_resolution._package_candidates(module, resolver.config.get("packages", {}))))
    for kind, candidates in groups:
        for candidate in candidates:
            if resolver.keeps(resolver.lookup(candidate, importer), importer):
                return kind
    return None


def _add(into: dict, value: dict) -> None:
    for key, item in value.items():
        if isinstance(item, dict):
            _add(into.setdefault(key, {}), item)
        elif isinstance(item, (int, float)) and not isinstance(item, bool):
            into[key] = into.get(key, 0) + item


def totals(projects: dict) -> dict:
    """The numbers of the projects that ran, added up, and the ones that failed with their errors."""
    found = {"projects": 0, "failed": {}}
    for name, item in sorted(projects.items()):
        if "error" in item:
            found["failed"][name] = item["error"]
        else:
            found["projects"] += 1
            _add(found, {key: value for key, value in item.items() if isinstance(value, dict) or key in ('files', 'importers')})
    return found


# ------------------------------------------------------------------ on Modal

def read_configs(project: Path, rels: list[str]) -> tuple[dict, str]:
    """`{config: its answer}` from `ts_imports_config.cjs`, and the TypeScript version that gave them."""
    entries, version = {}, None
    for start in range(0, len(rels), BATCH):
        group = rels[start:start + BATCH]
        done = subprocess.run(["node", SCRIPT, TYPESCRIPT, str(project), *(str(project / rel) for rel in group)],
                              cwd=project, capture_output=True, text=True, timeout=900, check=False)
        if done.returncode != 0:
            raise RuntimeError(f"node: exit {done.returncode}: {done.stderr.strip()[-400:]}")
        answer = json.loads(done.stdout)
        version = answer["typescript"]
        entries.update(zip(group, answer["configs"]))
    return entries, version


def tsc_of(project: Path, entries: dict, files: set) -> tuple[dict, dict]:
    """The configs that read (`tsc` for `owner_of`, and their settings), with the files each lists that the snapshot holds."""
    ok = {rel: entry for rel, entry in entries.items() if not entry.get("errors")}
    tsc = {"files_of": {rel: set(entry["fileNames"]) & files for rel, entry in ok.items()}, "references": {},
           "no_references": {rel for rel, entry in ok.items() if entry["stops"]["references"]},
           "no_ancestors": {rel for rel, entry in ok.items() if entry["stops"]["ancestors"]}}
    for rel, entry in ok.items():
        tsc["references"][rel] = [target for target in (os.path.relpath(path, project).replace(os.sep, "/")
                                                       for path in entry["references"]) if target in ok]
    return tsc, {rel: settings_of(entry) for rel, entry in ok.items()}


def with_settings(base):
    """`_ImportResolver` with the settings of each importer given (`by_file`), the nearest folder's for the others."""
    class Resolver(base):
        def __init__(self, *args, by_file):
            super().__init__(*args)
            self.by_file, self.current = by_file, None

        def resolve(self, importer, entry):
            self.current = importer
            return super().resolve(importer, entry)

        def settings(self, home):
            return self.by_file[self.current] if self.current in self.by_file else super().settings(home)

    return Resolver


def resolve_all(resolver, store) -> dict:
    """`iter_resolved_imports` over a resolver already built."""
    return {importer: resolver.resolve(importer, entry) if importer in resolver.allowed else {}
            for importer, entry in store.iter_file_headers_only()}


def one(name: str, work: Path) -> dict:
    """The comparison on one project of the corpus."""
    import import_resolution
    import module_derive
    import snapshot
    from module_inventory import _Inventory
    from snapshot_store import open_snapshot
    started = time.perf_counter()
    fixture = Path(mp.REMOTE_PM) / "fixtures" / name
    real = (fixture / "source.json").is_file()
    out = {"corpus": "real" if real else "miniature"}
    if real:
        listing = ARCHIVES / f"{name}.files.json"
        if not (ARCHIVES / f"{name}.tar.gz").is_file() or not listing.is_file():
            return {"error": f"no archive of {name} on the volume"}
        names = json.loads(listing.read_text(encoding="utf-8"))
    else:
        names = [p.relative_to(fixture).as_posix() for p in fixture.rglob("*") if p.is_file()]
    if not any(is_config(rel) for rel in names):
        return {**out, "skipped": "no tsconfig or jsconfig"}
    project = mp._project(name)
    manifest = work / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    with open_snapshot(manifest) as store:
        headers = dict(store.iter_file_headers_only())
        files = set(headers)
        entries, version = read_configs(project, sorted(rel for rel in files if is_config(rel)))
        tsc, settings = tsc_of(project, entries, files)
        importers = {rel for rel in files if Path(rel).suffix.lower() in import_resolution._SCRIPT_SUFFIXES}
        owners = {rel: owner_of(rel, tsc) for rel in importers}
        by_file = {rel: settings[owner.config] for rel, owner in owners.items() if owner.config is not None}
        root = Path(store.get("root") or ".").resolve()
        config = import_resolution.ts_path_config((root / (store.get("target") or ".")).resolve())
        plain = import_resolution._ImportResolver(store, config, False, None)
        fitted = with_settings(import_resolution._ImportResolver)(store, config, False, None, by_file=by_file)
        before, after = resolve_all(plain, store), resolve_all(fitted, store)
        found = classify_pairs(before, after, importers)
        via, by = {}, {kind: collections.Counter() for kind in ("gained", "lost", "changed")}
        for kind, resolver in (("gained", fitted), ("lost", plain), ("changed", fitted)):
            for importer, specifier, _, _ in found["pairs"][kind]:
                resolver.current = importer
                used = hit_kind(resolver, importer, specifier, resolver.settings((resolver.root / importer).parent))
                via[(importer, specifier)] = used
                by[kind][used or "none"] += 1
        edges_before, edges_after = file_edges(before, importers), file_edges(after, importers)
        out["edges"] = {"files": edge_changes(edges_before, edges_after)}
        try:
            graph = module_derive.derive(store, edges=False)
            owners_of_files, _ = module_derive._ownership(_Inventory(store), graph["modules"],
                                                          {m["id"]: m for m in graph["modules"]}, [])
            out["edges"]["modules"] = edge_changes(module_edges(edges_before, owners_of_files),
                                                   module_edges(edges_after, owners_of_files))
            out["modules"] = len(graph["modules"])
        except Exception as error:  # noqa: BLE001 - the modules are a part of the answer, not the answer
            out["modules_error"] = f"{type(error).__name__}: {error}"
    held = collections.Counter(owner.how for owner in owners.values())
    differ = sum(1 for owner in owners.values() if owner.how in ("many", "unreached")
                 and len({json.dumps(settings[config], sort_keys=True) for config in owner.held}) > 1)
    failed = {rel: entry["errors"] for rel, entry in entries.items() if entry.get("errors")}
    out.update(files=len(files), importers=len(importers), typescript=version,
               configs={"found": len(entries), "read": len(tsc["files_of"]), "failed": len(failed),
                        "with_paths": sum(1 for s in settings.values() if "paths" in s),
                        "with_base_url": sum(1 for s in settings.values() if "baseUrl" in s)},
               held={**{how: held.get(how, 0) for how in ("none", "one", "many", "unreached")},
                     # of the `none`, the files whose nearest tsconfig.json or jsconfig.json is one tsc refused: what a restored `node_modules` could change
                     "none_behind_failed": sum(1 for rel, owner in owners.items() if owner.config is None
                                               and config_chain(rel, set(entries))[:1] and config_chain(rel, set(entries))[0] in failed)},
               ambiguous={"settings_differ": differ},
               unheld_by_suffix=dict(collections.Counter(Path(rel).suffix.lower() for rel, owner in owners.items()
                                                         if owner.config is None)),
               # the name of the config each importer has, and of the one the importers of the lost pairs have
               owner_names=dict(collections.Counter(posixpath.basename(owner.config) for owner in owners.values()
                                                    if owner.config is not None)),
               lost_owner_names=dict(collections.Counter(posixpath.basename(owners[importer].config or "-")
                                                         for importer in {pair[0] for pair in found["pairs"]["lost"]})),
               pairs=found["counts"], gained_by=dict(by["gained"]), lost_by=dict(by["lost"]),
               changed_by=dict(by["changed"]),
               tsc_error_codes=dict(collections.Counter(f"TS{code}" for entry in entries.values() for code in entry.get("codes", ()))),
               tsc_errors=[{"config": rel, "error": " | ".join(errors)[:300]} for rel, errors in sorted(failed.items())[:10]],
               examples=examples(found["pairs"], via, owners=owners), seconds=round(time.perf_counter() - started, 1))
    return out


@app.function(image=image, cpu=(CPU, CPU), memory=(MEMORY, MEMORY), timeout=TIMEOUT, volumes={"/results": mp.volume})
def measure(names: list) -> dict:
    sys.path[:0] = [mp.REMOTE_SCRIPTS, mp.REMOTE_PM]
    answer = {}
    for name in names:
        work = Path(tempfile.mkdtemp(prefix=f"ts-imports-{name}-"))
        try:
            answer[name] = one(name, work)
        except Exception as error:  # noqa: BLE001 - a project's failure is its result
            answer[name] = {"error": f"{type(error).__name__}: {error}", "trace": traceback.format_exc()[-1500:]}
        finally:
            shutil.rmtree(work, ignore_errors=True)
    return answer


def save(target: Path, runs: list, projects: dict) -> None:
    ran = {name: item for name, item in projects.items() if "skipped" not in item}
    document = {"code": runs[0]["code"], "runs": runs, "totals": totals(ran),
                "skipped": sorted(name for name, item in projects.items() if "skipped" in item),
                "projects": dict(sorted(ran.items()))}
    target.write_text(json.dumps(document, indent=1), encoding="utf-8")


@app.local_entrypoint()
def main(cases: str = "mini,real", out: str = str(OUT), chunk: int = 8):
    fixtures = HERE / "fixtures"
    names = sorted(p.name for p in fixtures.iterdir() if (p / "expected.json").is_file())
    real = [name for name in names if (fixtures / name / "source.json").is_file()]
    small = [name for name in names if name not in real
             and any(is_config(f.relative_to(fixtures / name).as_posix()) for f in (fixtures / name).rglob("*") if f.is_file())]
    batches = []
    for spec in filter(None, cases.split(",")):
        if spec == "mini":
            batches += [small[i:i + chunk] for i in range(0, len(small), chunk)]
        elif spec == "real":
            batches += [[name] for name in real]
        else:
            batches.append([spec])
    target = Path(out)
    target.parent.mkdir(parents=True, exist_ok=True)
    ran = mp.code(mp.REPO, mp.UPLOADED)  # as uploaded when the app started, just before
    scripts = Path(os.environ.get("DAODAN_SCRIPTS") or mp.REPO / "daodan/core")
    ran["scripts_commit"] = subprocess.run(["git", "-C", str(scripts), "rev-parse", "HEAD"], capture_output=True, text=True,
                                           check=False).stdout.strip()
    projects, runs = {}, []
    if target.is_file():  # a call after another adds its projects to the file, and replaces the ones it runs again
        before = json.loads(target.read_text(encoding="utf-8"))
        projects, runs = before["projects"], before["runs"]
        projects.update({name: {"skipped": "no tsconfig or jsconfig"} for name in before["skipped"]})
    runs.append({"code": ran, "cases": sorted({name for batch in batches for name in batch})})
    for answer in measure.map(batches, order_outputs=False, return_exceptions=True):
        if isinstance(answer, Exception):
            print("a container failed:", answer, flush=True)
            continue
        projects.update(answer)
        save(target, runs, projects)
        for name, item in answer.items():
            print(name, item.get("error") or item.get("skipped") or {"pairs": item["pairs"], "seconds": item["seconds"]}, flush=True)
    print("ran", len(projects), "->", target, flush=True)
