"""SCIP versus engines on Modal: for every reference of a snapshot, what a whole-project SCIP index answers
at the referenced name's position, beside the engine pass's answer for the same call. No model.

Road A is the product's engine pass (`resolve_edges.py --pass`); road B is the index of an existing SCIP
indexer joined by position with the snapshot's references. One container per case: snapshot as
`modal_audit.py` builds it, road A (rerun, or the per-call answers a labelled audit run left on the volume),
then each indexer of the case's languages in a copy of the checkout, then the join.

    modal deploy benchmarks/inference-audit/modal_scip.py
    python benchmarks/inference-audit/modal_scip.py spawn --cases chi,semver,tududi
    python benchmarks/inference-audit/modal_scip.py fetch --cases chi,semver,tududi

`python modal_scip.py join --manifest M --index I [--answers A] --out O` runs the join alone, locally.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
PLUGIN = HERE.parents[1] / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map")
SCRIPTS = str(PLUGIN / "scripts")
RESULTS = HERE / "results"
TAG = "inference-audit"
sys.path.insert(0, str(HERE) if LOCAL else "/audit")
sys.path.insert(0, SCRIPTS)
from modal_audit import CASES, _run, _source  # noqa: E402

# Road A's per-call answers kept by a labelled audit run at the same commit and plugin: reused, never rerun.
REUSE = {"tududi": "r1"}
SCIP_GO = "v0.2.9"  # github.com/scip-code/scip-go, built with the Go release the engine pass pins
SCIP_TYPESCRIPT = "0.5.2"  # @sourcegraph/scip-typescript; needs Node >= 22.13
NODE = ("v22.23.4", "1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce")
SUFFIXES = {"scip-typescript": (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"), "scip-go": (".go",),
            "rust-analyzer": (".rs",)}
INDEXERS = {"go": "scip-go", "rust": "rust-analyzer", "javascript": "scip-typescript", "typescript": "scip-typescript"}
EXAMPLES = 20


def _image():
    import resolve_edges as rx
    go_asset, go_sha = rx.GO_ASSETS["linux-x64"]
    ra_asset, ra_sha = rx.RUST_ANALYZER_ASSETS["linux-x64"]
    node_version, node_sha = NODE
    node = f"node-{node_version}-linux-x64.tar.xz"
    return (
        modal.Image.debian_slim(python_version="3.13")
        .apt_install("git", "curl", "ca-certificates", "nodejs", "npm", "unzip", "xz-utils")
        .pip_install("uv", "tree-sitter==0.26.0", "tree-sitter-language-pack==1.13.5", "sqlglot>=30")
        .run_commands(
            f"curl -fsSL https://nodejs.org/dist/{node_version}/{node} -o /tmp/{node}",
            f"echo '{node_sha}  /tmp/{node}' | sha256sum -c -",
            f"mkdir -p /opt/node && tar -xJf /tmp/{node} -C /opt/node --strip-components=1 && rm /tmp/{node}",
            f"PATH=/opt/node/bin:$PATH npm install -g --ignore-scripts --no-audit --no-fund "
            f"@sourcegraph/scip-typescript@{SCIP_TYPESCRIPT}",
            f"curl -fsSL https://go.dev/dl/{go_asset} -o /tmp/{go_asset}",
            f"echo '{go_sha}  /tmp/{go_asset}' | sha256sum -c -",
            f"tar -xzf /tmp/{go_asset} -C /opt && rm /tmp/{go_asset}",
            f"GOBIN=/opt/scip/bin GOPATH=/tmp/gopath GOFLAGS= GOTOOLCHAIN=local /opt/go/bin/go install "
            f"github.com/scip-code/scip-go/cmd/scip-go@{SCIP_GO} && rm -rf /tmp/gopath",
            f"curl -fsSL https://github.com/rust-lang/rust-analyzer/releases/download/{rx.RUST_ANALYZER_RELEASE}/"
            f"rust-analyzer-{ra_asset} -o /tmp/ra.gz",
            f"echo '{ra_sha}  /tmp/ra.gz' | sha256sum -c -",
            "gunzip -c /tmp/ra.gz > /opt/scip/bin/rust-analyzer && chmod 755 /opt/scip/bin/rust-analyzer && rm /tmp/ra.gz",
        )
        .add_local_dir(PLUGIN, "/daodan/map", ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_file(HERE / "modal_audit.py" if LOCAL else Path("/audit/modal_audit.py"), "/audit/modal_audit.py")
        .add_local_file(HERE / "probe.py" if LOCAL else Path("/audit/probe.py"), "/audit/probe.py")
    )


app = modal.App("daodan-scip-audit", image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)

MEASURE = ("import resource,subprocess,sys;r=subprocess.run(sys.argv[1:]);"
           "print('DAODAN_MAXRSS_KB=%d' % resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss, file=sys.stderr);"
           "sys.exit(r.returncode)")


def _measured(command: list[str], cwd: str, env: dict, timeout: int) -> dict:
    """Wall time and the peak resident memory of the largest process the command started."""
    import re
    import subprocess
    import time
    begun = time.time()
    try:
        done = subprocess.run([sys.executable, "-c", MEASURE, *command], cwd=cwd, env=env, capture_output=True,
                              text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        code, out, err = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as error:
        code, out, err = "timeout", str(error.stdout or "")[-2000:], str(error.stderr or "")[-2000:]
    peak = re.findall(r"DAODAN_MAXRSS_KB=(\d+)", err or "")
    return {"command": command, "returncode": code, "seconds": round(time.time() - begun, 1),
            "peak_rss_mb": round(int(peak[-1]) / 1024) if peak else None,
            "stdout_tail": (out or "")[-1500:], "stderr_tail": (err or "")[-2500:]}


def _tsconfig(mirror: Path, files: list[str]) -> dict:
    """Every JS/TS file of the snapshot in one program with `allowJs`; the project's own options kept."""
    options = {"allowJs": True, "checkJs": False, "noEmit": True, "incremental": False, "skipLibCheck": True}
    config = {"compilerOptions": options, "include": files, "exclude": []}
    own = mirror / "tsconfig.json"
    if own.is_file():
        own.rename(mirror / "tsconfig.project.json")
        config["extends"] = "./tsconfig.project.json"
    else:
        options.update({"target": "es2022", "module": "esnext", "moduleResolution": "bundler", "jsx": "preserve",
                        "esModuleInterop": True, "allowSyntheticDefaultImports": True, "resolveJsonModule": True})
    own.write_text(json.dumps(config, indent=1), encoding="utf-8")
    return config


MANIFESTS = {"scip-go": "go.mod", "rust-analyzer": "Cargo.toml"}
# The engine pass's own rust-analyzer options: all features, no build script, no procedural macro.
RUST_CONFIG = {"cargo": {"buildScripts": {"enable": False}, "features": "all"}, "procMacro": {"enable": False}}


def _owner(rel: str, roots: set[str]) -> str | None:
    """The nearest directory holding a manifest above a file, '' for the checkout's root."""
    parts = rel.split("/")[:-1]
    for size in range(len(parts), -1, -1):
        if "/".join(parts[:size]) in roots:
            return "/".join(parts[:size])
    return None


def _documents(index: Path, mirror: Path, prefix: str) -> set[str]:
    """The checkout-relative files an index holds a document for."""
    import resolve_edges as rx
    base = mirror.resolve()
    reader = rx.ScipEngine(base / prefix if prefix else base, [index])
    reader.probe()
    return {path.relative_to(base).as_posix() for path in reader._units if path.is_relative_to(base)}


def _index(language: str, target: Path, work: Path, files: list[str]) -> dict:
    """The SCIP indexes of the case's checkout, written from a copy of it.

    One run at the root; for Go and Rust, one more run in each other module or crate directory that holds
    snapshot files the root run left out, and Go's ignored directories (`_x`, `.x`, `testdata`) named as
    explicit packages, so the index covers the files the snapshot covers.
    """
    import os
    import shutil
    import resolve_edges as rx
    tool = INDEXERS[language]
    mirror = work / f"mirror-{tool}"
    if not mirror.exists():
        shutil.copytree(target, mirror, symlinks=True, ignore=shutil.ignore_patterns("node_modules"))
    env = dict(os.environ)
    info = {"indexer": tool, "runs": []}
    roots = set()
    if tool in MANIFESTS:
        for path in mirror.rglob(MANIFESTS[tool]):
            relative = path.parent.relative_to(mirror)
            if not {".git", "target"} & set(relative.parts):
                roots.add("" if relative == Path(".") else relative.as_posix())
    if tool == "scip-go":
        cache = rx.shared_cache_dir() / "go"
        env.update({"GOROOT": "/opt/go", "GOPATH": str(cache / "path"), "GOCACHE": str(cache / "build"),
                    "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=readonly", "GOTELEMETRY": "off",
                    "PATH": "/opt/go/bin:/opt/scip/bin:" + env["PATH"]})
        info["version"] = SCIP_GO

        def command(prefix, output):
            _run(["/opt/go/bin/go", "mod", "download"], str(mirror / prefix), ok=(0, 1), env=env, timeout=1800)
            skip = len(prefix) + 1 if prefix else 0
            ignored = sorted({rel.rsplit("/", 1)[0][skip:] for rel in files
                              if "/" in rel and _owner(rel, roots) == prefix and any(
                                  part.startswith(("_", ".")) or part == "testdata"
                                  for part in rel.split("/")[:-1])})
            return ["/opt/scip/bin/scip-go", f"--output={output}", "./...", *[f"./{d}" for d in ignored]]
    elif tool == "rust-analyzer":
        toolchain = rx.rust_toolchain()
        env.update({"PATH": f"{toolchain}/bin:" + env["PATH"], "CARGO_HOME": str(rx.shared_cache_dir() / "cargo"),
                    "CARGO_TARGET_DIR": str(work / "rust-target")})
        info["version"] = _run(["/opt/scip/bin/rust-analyzer", "--version"], env=env).stdout.strip()
        info["toolchain"] = rx.RUST_VERSION
        config = work / "rust-analyzer.json"
        config.write_text(json.dumps(RUST_CONFIG), encoding="utf-8")
        info["config"] = RUST_CONFIG

        def command(prefix, output):
            return ["/opt/scip/bin/rust-analyzer", "scip", ".", "--output", str(output), "--config-path", str(config)]
    else:
        modules = rx.npm_modules(target)  # the engine pass's own install: npm ci --ignore-scripts
        info["node_modules"] = str(modules)
        if modules is not None:
            for found in sorted(modules.parent.rglob("node_modules")):
                relative = found.relative_to(modules.parent)
                if "node_modules" in relative.parts[:-1]:
                    continue
                link = mirror / relative
                if not link.exists():
                    link.parent.mkdir(parents=True, exist_ok=True)
                    link.symlink_to(found, target_is_directory=True)
        info["tsconfig_extends"] = _tsconfig(mirror, files).get("extends")
        env["PATH"] = "/opt/node/bin:" + env["PATH"]
        env["NODE_OPTIONS"] = "--max-old-space-size=12288"
        info["version"] = SCIP_TYPESCRIPT

        def command(prefix, output):
            return ["/opt/node/bin/scip-typescript", "index", "--cwd", str(mirror), "--output", str(output),
                    "--no-progress-bar"]
    pending, covered = [""], set()
    while pending:
        prefix = pending.pop(0)
        output = work / f"{tool}-{len(info['runs'])}.scip"
        run = {"prefix": prefix, **_measured(command(prefix, output), str(mirror / prefix), env, timeout=3 * 3600)}
        if tool == "rust-analyzer" and run["returncode"] != 0:
            # An option the release does not take: the indexer's defaults rather than no index.
            run = {"prefix": prefix, "config": "rejected",
                   **_measured(command(prefix, output)[:-2], str(mirror / prefix), env, timeout=3 * 3600)}
        run["index"] = str(output) if output.is_file() else None
        run["index_bytes"] = output.stat().st_size if output.is_file() else 0
        info["runs"].append(run)
        if run["index"]:
            covered |= _documents(output, mirror, prefix)
        if prefix == "" and roots:
            missing = [rel for rel in files if rel not in covered]
            pending += sorted({_owner(rel, roots) for rel in missing} - {None, ""})
    info["seconds"] = round(sum(run["seconds"] for run in info["runs"]), 1)
    info["peak_rss_mb"] = max((run["peak_rss_mb"] or 0 for run in info["runs"]), default=None)
    info["indexes"] = [[run["index"], run["prefix"]] for run in info["runs"] if run["index"]]
    return info


def _package(symbol: str) -> str:
    """`manager package@version` of a SCIP symbol (`scheme manager package version descriptors`)."""
    parts = symbol.replace("  ", "\0").split(" ")
    if len(parts) < 5:
        return symbol[:80]
    return f"{parts[1]} {parts[2]}@{parts[3]}".replace("\0", " ")


def _descriptors(symbol: str) -> str:
    """A SCIP symbol without its scheme, manager, package and version."""
    return " ".join(symbol.replace("  ", "\0").split(" ")[4:])


def _sample(items: list, size: int = EXAMPLES) -> list:
    if len(items) <= size:
        return items
    step = len(items) / size
    return [items[int(i * step)] for i in range(size)]


def join(manifest: Path, indexes: list[tuple[Path, str]], answers_path: Path | None,
         trace: bool = False) -> dict:
    """Road B (the index at each reference's name) beside road A (the engine's and the lexical answer)."""
    import collections
    import sqlite3
    import resolve_edges as rx
    from snapshot_store import _unpack, open_snapshot

    class Index(rx.ScipEngine):
        """The pass's SCIP reader, keeping every occurrence by position with its raw symbol."""

        def __init__(self, root, paths):
            super().__init__(root, paths)
            self.at: dict = {}
            self.prefix = ""

        def load(self, indexes):
            for path, prefix in indexes:
                self.prefix = prefix
                self._parse_scip_bytes(Path(path).read_bytes())
                self.loaded_indexes.append(str(path))
            return True, ""

        def _document(self, rel, occurrences, encoding):
            # A run in a module directory may name its documents from that directory or from the checkout.
            if rel and self.prefix and not (self.project_root / rel).is_file():
                rel = f"{self.prefix}/{rel}"
            super()._document(rel, occurrences, encoding)
            if not rel:
                return
            path = (self.project_root / rel).resolve()
            for rng, symbol, roles in occurrences:
                if len(rng) < 3 or not symbol:
                    continue
                key = f"{path.as_posix()}#{symbol}" if symbol.startswith("local ") else symbol
                self.at.setdefault((path, int(rng[0]) + 1, int(rng[1])), []).append((symbol, key, bool(roles & 1)))

    with open_snapshot(manifest) as store:
        connection = store.connection
        project_root = (Path(store["root"]) / store["target"]).resolve()
        if project_root.is_file():
            project_root = project_root.parent
        store_root, source_paths, _ = rx.verify_sources(store)
        index = Index(project_root, [])
        ready, reason = index.load(indexes)
        if not ready:
            return {"error": reason}
        documents = {path for path in index._units}
        inventory = rx.inventory_files(connection)
        languages = dict(connection.execute("SELECT file, language FROM sem_coverage"))
        tables: dict = {}
        lines: dict = {}

        def lines_for(rel):
            if rel not in lines:
                lines[rel] = source_paths[rel].read_text(encoding="utf-8").split("\n")
            return lines[rel]

        def table_for(rel):
            return rx.symbol_table(connection, rel, "\n".join(lines_for(rel)))

        own: set = set()

        def own_packages():
            """`manager package` of the symbols the index defines: the project's own packages."""
            if not own:
                own.add(None)
                for key in index._defs_by_symbol:
                    if not key.split("#", 1)[-1].startswith("local "):
                        parts = key.split(" ")
                        if len(parts) >= 5:
                            own.add(f"{parts[1]} {parts[2]}")
            return own

        twin_table: dict = {}

        def twins():
            """A defined project symbol by its descriptors, for an external symbol that differs only in its package."""
            if not twin_table:
                twin_table[None] = None
                for key in index._defs_by_symbol:
                    if not key.split("#", 1)[-1].startswith("local ") and "/" in key:
                        twin_table.setdefault(_descriptors(key), key)
            return twin_table

        def follow(location):
            # The product's own rule (`grade_all`): a value binding is followed by asking the source again at its
            # position; for an index, the other symbols that occur there (a shorthand property, a destructuring).
            return index.definitions(Path(location.module_path), location.line, location.column)

        def road_b(rel, payload, span):
            """(class, project declaration or None, detail, followed) of the index at the referenced name.

            The definitions of every symbol at the position are graded as the engine pass grades an engine's
            answer (`grade_all`, with its bounded follow of value bindings), so A and B differ only by source.
            """
            parts = payload.get("parts") or []
            if not parts or not span or rel not in source_paths:
                return "none", None, "no-position", False
            l0, c0, l1, c1 = span
            try:
                text = lines_for(rel)
            except (OSError, UnicodeError):
                return "none", None, "no-position", False
            if not 1 <= l0 <= l1 <= len(text):
                return "none", None, "no-position", False
            column = rx.callee_column(text[l1 - 1], [l0, c0, l1, c1], parts[-1])
            if column is None:
                return "none", None, "no-position", False
            path = source_paths[rel].resolve()
            native = index._convert(path, l1, column, to_bytes=False)
            entries = index.at.get((path, l1, native), [])
            if not entries:
                return "none", None, ("no-document" if path not in documents else "no-occurrence"), False
            locations = index.definitions(path, l1, column)
            verdict, target = rx.grade_all(locations, inventory, tables, store_root, table_for)
            followed = False
            if not verdict.startswith("edge-"):
                verdict, target = rx.grade_all(locations, inventory, tables, store_root, table_for, follow=follow)
                followed = verdict.startswith("edge-")
            symbols = [symbol for symbol, _key, definition in entries if not definition] or \
                [symbol for symbol, _key, _definition in entries]
            local = any(symbol.startswith("local ") for symbol in symbols)
            if verdict.startswith("edge-") and target:
                return "project-declaration", target["id"], ("local " if local else "") + symbols[0][-120:], followed
            if local:
                return "local", None, symbols[0], False
            if verdict == "external-definition":
                symbol = next((s for s in symbols if not s.startswith("local ")), symbols[0])
                package = _package(symbol)
                flags = []
                if " ".join(package.split("@")[0].split(" ")[:2]) in own_packages():
                    flags.append("own package")
                if twins().get(_descriptors(symbol)):
                    flags.append("project twin")
                return "external", None, f"{package}{' [' + ', '.join(flags) + ']' if flags else ''} :: " \
                                         f"{symbol[-110:]}", False
            if verdict == "unresolved":
                return "none", None, "no-definition", False
            return "project-other", None, f"{verdict} {symbols[0][-110:]}", False

        answers = {}
        if answers_path is not None and Path(answers_path).is_file():
            db = sqlite3.connect(answers_path)
            for row in db.execute("SELECT reference_id, verdict, target_id, file, line, column FROM answers"):
                answers[row[0]] = row[1:]
            db.close()

        def road_a(reference_id, lexical_target, rel, l1, column_hint):
            """The graph the product keeps: the engine's answer wins, the lexical target stays otherwise."""
            answer = answers.get(reference_id)
            if answer is not None:
                verdict, target_id = answer[0], answer[1]
                if verdict.startswith("edge-") and target_id:
                    return "project-declaration", target_id, "engine"
                if verdict == "external-definition":
                    return "external", None, "engine"
            if lexical_target:
                return "project-declaration", lexical_target, "lexical"
            if answer is None:
                return "not-asked", None, "-"
            if answer[0] in ("project-not-a-symbol", "ambiguous-target", "binding"):
                return "project-other", None, answer[0]
            return "none", None, answer[0]

        out: dict = {}
        examples: dict = collections.defaultdict(lambda: collections.defaultdict(list))
        mismatched = 0
        rows = connection.execute(
            "SELECT id, file, kind, resolution, target_id, l0, c0, l1, c1, payload FROM sem_references "
            "WHERE kind IN ('call','read') ORDER BY file, l0, c0, id")
        for reference_id, rel, kind, resolution, lexical_target, l0, c0, l1, c1, blob in rows:
            language = languages.get(rel) or "?"
            if language not in INDEXERS:
                continue
            payload = _unpack(blob) or {}
            name = ".".join(payload.get("parts") or [])
            entry = out.setdefault(language, {
                "references": collections.Counter(), "b": {"call": collections.Counter(), "read": collections.Counter()},
                "b_none_detail": {"call": collections.Counter(), "read": collections.Counter()},
                "b_local_on_declaration": collections.Counter(), "b_external_packages": collections.Counter(),
                "b_followed": collections.Counter(), "b_external_flags": collections.Counter(),
                "b_other_verdict": {"call": collections.Counter(), "read": collections.Counter()},
                "a": collections.Counter(), "a_target_source": collections.Counter(), "matrix": collections.Counter(),
                "a_not_asked": collections.Counter(),
                "cells": collections.Counter(), "reads_vs_lexical": collections.Counter()})
            entry["references"][kind] += 1
            b_cls, b_target, b_detail, b_followed = road_b(rel, payload, [l0, c0, l1, c1])
            b_targets = {b_target} if b_target else set()
            entry["b"][kind][b_cls] += 1
            if b_followed:
                entry["b_followed"][kind] += 1
            if b_cls == "none":
                entry["b_none_detail"][kind][b_detail] += 1
            if b_cls == "project-declaration" and b_detail.startswith("local "):
                entry["b_local_on_declaration"][kind] += 1
            if b_cls == "project-other":
                entry["b_other_verdict"][kind][b_detail.split(" ")[0]] += 1
            if b_cls == "external":
                entry["b_external_packages"][b_detail.split(" :: ")[0]] += 1
                for flag in ("own package", "project twin"):
                    if flag in b_detail.split(" :: ")[0]:
                        entry["b_external_flags"][f"{kind} {flag}"] += 1
                        examples[language][f"B external, {flag}"].append(f"{rel}:{l1} {name} | {b_detail}")
            site = f"{rel}:{l1} {name}"
            if trace:
                entry.setdefault("trace", []).append(f"{kind} {site} | lexical {lexical_target} | B {b_cls} {b_target or b_detail}")
            if kind == "read":
                lexical = lexical_target if resolution == "resolved" else None
                if lexical and b_targets:
                    entry["reads_vs_lexical"]["same" if lexical in b_targets else "different"] += 1
                elif lexical:
                    entry["reads_vs_lexical"]["only-lexical"] += 1
                elif b_target:
                    entry["reads_vs_lexical"]["only-B"] += 1
                    examples[language]["read-only-B"].append(f"{site} -> {b_target}")
                else:
                    entry["reads_vs_lexical"]["neither"] += 1
                continue
            answer = answers.get(reference_id)
            if answer is not None and (answer[2] != rel or answer[3] != l1):
                mismatched += 1
            a_cls, a_target, a_source = road_a(reference_id, lexical_target if resolution == "resolved" else None,
                                               rel, l1, None)
            entry["a"][a_cls] += 1
            if a_cls == "not-asked":
                entry["a_not_asked"][f"{resolution} {payload.get('reason') or '-'}"] += 1
            if a_target:
                entry["a_target_source"][a_source] += 1
            entry["matrix"][f"A {a_cls} | B {b_cls}{' (declaration)' if b_cls == 'local' and b_target else ''}"] += 1
            detail = f"{site} | A {a_cls} {a_target or a_source} | B {b_cls} {b_target or b_detail}"
            if a_target and b_targets:
                cell = "same project target" if a_target in b_targets else "different project target"
            elif a_target:
                cell = "only A has a project target"
            elif b_target:
                cell = "only B has a project target"
            elif a_cls == "external" and b_cls == "external":
                cell = "both external"
            elif a_cls in ("none", "not-asked") and b_cls == "none":
                cell = "both none"
            else:
                cell = f"mixed: A {a_cls}, B {b_cls}"
            entry["cells"][cell] += 1
            if cell == "only A has a project target":
                examples[language][f"{cell} (B {b_cls})"].append(detail)
            elif cell in ("different project target", "only B has a project target"):
                examples[language][cell].append(detail)
            if b_cls == "none":
                examples[language][f"B none on calls ({b_detail})"].append(detail)
            elif b_cls == "local":
                examples[language]["B local on calls"].append(detail)
        for language, entry in out.items():
            for key, value in list(entry.items()):
                if key == "trace":
                    continue
                if isinstance(value, collections.Counter):
                    entry[key] = dict(value.most_common(25) if key == "b_external_packages" else sorted(value.items()))
                elif isinstance(value, dict):
                    entry[key] = {k: dict(sorted(v.items())) for k, v in value.items()}
            entry["examples"] = {k: _sample(v) for k, v in sorted(examples[language].items())}
        files = {language: sum(1 for rel, lang in languages.items() if lang == language and rel in inventory)
                 for language in out}
        indexed = collections.Counter(languages.get(path.relative_to(project_root).as_posix())
                                      for path in documents if path.is_relative_to(project_root))
        missing = {language: sorted(rel for rel, lang in languages.items() if lang == language and rel in inventory
                                    and rel in source_paths and source_paths[rel].resolve() not in documents)[:40]
                   for language in out}
        return {"languages": out, "files": files, "files_indexed": {k: indexed.get(k, 0) for k in out},
                "files_not_indexed": missing,
                "index_tool": index.identity(), "answers": len(answers), "answer_line_mismatches": mismatched}


@app.function(cpu=4, memory=16384, timeout=4 * 3600, volumes={"/results": volume})
def scip_case(name: str, case: dict, label: str = "") -> dict:
    import shutil
    import time
    started = time.time()
    work = Path("/work") / name
    target = _source(work / "src", case, None)
    manifest = work / "snapshot/manifest.sqlite"
    _run([sys.executable, f"{SCRIPTS}/snapshot.py", "write", str(target), "--out", str(manifest),
          "--no-engine", "--no-index"])
    result = {"case": name, "commit": case["commit"], "snapshot_seconds": round(time.time() - started, 1)}
    import resolve_edges as rx
    import sqlite3
    reuse = REUSE.get(name)
    if reuse:
        answers = work / "answers.sqlite"
        shutil.copyfile(Path("/results") / TAG / f"answers-{name}-{reuse}.sqlite", answers)
        audit = json.loads((Path("/results") / TAG / f"audit-{name}-{reuse}.json").read_text(encoding="utf-8"))
        result["road_a"] = {"source": f"answers-{name}-{reuse}.sqlite", "seconds": audit.get("pass_seconds"),
                            "peak_rss_mb": None, "coverage": audit.get("graph_use", {}).get("coverage")}
    else:
        report = work / "engine-report.json"
        run = _measured([sys.executable, f"{SCRIPTS}/resolve_edges.py", str(manifest), "--pass",
                         "--report-out", str(report)], SCRIPTS, None, 3 * 3600)
        answers = rx.default_answers_path(manifest)
        result["road_a"] = {"source": "rerun", "seconds": run["seconds"], "peak_rss_mb": run["peak_rss_mb"],
                            "returncode": run["returncode"], "stderr_tail": run["stderr_tail"][-800:]}
        try:
            summary = json.loads(report.read_text(encoding="utf-8"))
            result["road_a"]["coverage"] = {name: engine.get("resolution", {}).get("by_language")
                                            for name, engine in (summary.get("engines") or {}).items()}
        except (OSError, ValueError) as error:
            result["road_a"]["coverage"] = repr(error)
    connection = sqlite3.connect(manifest)
    coverage = connection.execute("SELECT file, language FROM sem_coverage WHERE status='ast'").fetchall()
    connection.close()
    result["indexers"] = {}
    indexes = []
    for language in sorted({language for _, language in coverage if language in INDEXERS}):
        tool = INDEXERS[language]
        if tool in result["indexers"]:
            continue
        files = sorted(rel for rel, lang in coverage if INDEXERS.get(lang) == tool and rel.endswith(SUFFIXES[tool]))
        try:
            info = _index(language, target, work, files)
        except Exception as error:
            info = {"indexer": tool, "error": repr(error)[:3000]}
        result["indexers"][tool] = info
        indexes += [(Path(path), prefix) for path, prefix in info.get("indexes", ())]
    begun = time.time()
    try:
        result["join"] = join(manifest, indexes, answers) if indexes else {"error": "no index"}
    except Exception:
        import traceback
        result["join"] = {"error": traceback.format_exc()[-3000:]}
    result["join_seconds"] = round(time.time() - begun, 1)
    result["seconds"] = round(time.time() - started, 1)
    stem = f"{name}-{label}" if label else name
    destination = Path("/results") / TAG / f"scip-{stem}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    volume.commit()
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("spawn", "fetch", "join"))
    parser.add_argument("--cases", default="chi,semver,tududi")
    parser.add_argument("--label", default="")
    parser.add_argument("--manifest")
    parser.add_argument("--index", action="append", default=[])
    parser.add_argument("--answers")
    parser.add_argument("--out")
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    chosen = [c.strip() for c in args.cases.split(",") if c.strip()]
    if args.command == "spawn":
        function = modal.Function.from_name("daodan-scip-audit", "scip_case")
        for name in chosen:
            print(name, function.spawn(name, CASES[name], args.label).object_id)
    elif args.command == "fetch":
        RESULTS.mkdir(parents=True, exist_ok=True)
        for name in chosen:
            stem = f"{name}-{args.label}" if args.label else name
            data = b"".join(volume.read_file(f"{TAG}/scip-{stem}.json"))
            (RESULTS / f"scip-{stem}.json").write_bytes(data.replace(b"\r\n", b"\n"))
            print(name, len(data))
    else:
        value = join(Path(args.manifest), [(Path(p.split("=")[0]), p.partition("=")[2]) for p in args.index], Path(args.answers) if args.answers else None,
                     args.trace)
        text = json.dumps(value, indent=1, ensure_ascii=False)
        Path(args.out).write_text(text + "\n", encoding="utf-8") if args.out else print(text)
