"""The position stage: one engine asked at each call position of its languages (`resolve_edges`),
with the answer cache that spares it what cannot have changed."""
from __future__ import annotations

import json
import math
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import semantic_store
from code_graph import dependency_digests, file_dependencies
from snapshot_store import _unpack, open_snapshot
from source_positions import EngineFailure
from edge_grading import (callee_column, CANDIDATE_REASONS, classify_reference, edge_destination, grade, grade_all,
                          inventory_files, POSITION_ENDS, project_callee_names, symbol_table, verify_sources)
from edge_store import (coverage_violation, default_edge_store, EDGE_SCHEMA, kept_languages, language_coverage,
                        store_binding, write_edge_store)


MEMORY_EXHAUSTED = re.compile(r"MemoryError|out of memory|OutOfMemoryError|bad_alloc|Cannot allocate memory",
                              re.IGNORECASE)


def snapshot_languages(connection) -> list[str]:
    return [row[0] for row in connection.execute(
        "SELECT DISTINCT language FROM sem_coverage WHERE status IN ('ast', 'partial') AND language IS NOT NULL "
        "ORDER BY language")]


def engine_languages(engine, connection) -> tuple[str, ...]:
    """The snapshot languages an engine answers for: its declared ones the snapshot holds a file of, parsed or not
    (a language of whose files the engine reads nothing is `failed`, never left out), or every parsed one."""
    declared = getattr(engine, "languages", ("python",))
    if declared is None:
        return tuple(snapshot_languages(connection))
    present = {row[0] for row in connection.execute("SELECT DISTINCT language FROM sem_coverage")}
    return tuple(language for language in declared if language in present) or tuple(declared[:1])


ANSWERS_NAME = "engine-answers.sqlite"


# A running pass publishes what it has proved at most this often.
PUBLISH_SECONDS = 30


def default_answers_path(manifest: Path) -> Path:
    """The answer cache of the analysis a snapshot belongs to, beside its card store."""
    import card_store
    return card_store.default_cards_path(manifest).with_name(ANSWERS_NAME)


def file_ranks(connection) -> dict[str, float]:
    """The snapshot's PageRank of each file, or nothing when the graph metrics are absent."""
    try:
        return {row[0]: row[1] or 0.0 for row in connection.execute("SELECT node, score FROM sem_rank")}
    except sqlite3.Error:
        return {}


ANSWER_COLUMNS = ("context", "engine", "reference_id", "file", "file_hash", "file_digest", "verdict",
                  "target_id", "targets", "resolver", "line", "column")


def _answers_connection(path: Path):
    connection = sqlite3.connect(path, timeout=30)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS answers(context TEXT NOT NULL,engine TEXT NOT NULL,reference_id TEXT NOT NULL,"
        "file TEXT NOT NULL,file_hash TEXT NOT NULL,file_digest TEXT NOT NULL,verdict TEXT NOT NULL,"
        "target_id TEXT,targets TEXT NOT NULL,resolver TEXT NOT NULL,line INTEGER,column INTEGER,"
        "PRIMARY KEY(context,reference_id))")
    connection.execute("CREATE INDEX IF NOT EXISTS answers_file ON answers(engine,file)")
    return connection


def load_answers(path: Path, context: str, engine: str) -> tuple[dict[str, dict], dict[str, str]]:
    """The cached answers of this engine context by reference, and the file hashes the engine last answered for."""
    if not path.is_file():
        return {}, {}
    connection = _answers_connection(path)
    try:
        answers = {row[2]: dict(zip(ANSWER_COLUMNS, row)) for row in connection.execute(
            f"SELECT {','.join(ANSWER_COLUMNS)} FROM answers WHERE context=?", (context,))}
        known = dict(connection.execute("SELECT DISTINCT file, file_hash FROM answers WHERE engine=?", (engine,)))
    finally:
        connection.close()
    return answers, known


def save_answers(path: Path, context: str, engine: str, rows: list[dict]) -> None:
    """Add answers, keeping one engine context and one generation per file."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = _answers_connection(path)
    try:
        with connection:
            connection.execute("DELETE FROM answers WHERE engine=? AND context<>?", (engine, context))
            for file, digest in sorted({(row["file"], row["file_digest"]) for row in rows}):
                connection.execute("DELETE FROM answers WHERE context=? AND file=? AND file_digest<>?",
                                   (context, file, digest))
            connection.executemany(
                f"INSERT OR REPLACE INTO answers VALUES({','.join('?' for _ in ANSWER_COLUMNS)})",
                [tuple(row[key] for key in ANSWER_COLUMNS) for row in rows])
    finally:
        connection.close()


def answer_targets(definitions, root: Path, hashes: dict[str, str]) -> str:
    """The project files an answer points into, with their bytes: a reused answer needs them unchanged."""
    targets = {}
    for definition in definitions or ():
        module_path = getattr(definition, "module_path", None)
        if not module_path:
            continue
        try:
            relative = Path(module_path).resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        targets[relative] = hashes.get(relative)
    return json.dumps(dict(sorted(targets.items())))


def resolve_edges(manifest: Path, *, engine, limit: int | None, stride: int,
                  dry_run: bool = False, out: Path | None = None) -> dict:
    """Ask the engine about the unresolved calls of its languages and record what it proves.

    The store keeps one entry per language. A pass replaces the entries and edges
    of its own languages and keeps those another engine wrote for this snapshot.
    Work goes where it is worth most: an answer whose file and imports are unchanged
    since the engine gave it comes from the answer cache; edited and new files are
    asked first, then files by rank; the engine starts only when a position needs
    it; and the pass publishes what it has proved every `PUBLISH_SECONDS`, so a
    stopped or failed pass resumes where it ended. A dry run neither reuses nor publishes.
    """
    run_started = time.perf_counter()
    if limit is not None and (type(limit) is not int or limit < 0):
        raise ValueError("limit must be a nonnegative integer")
    if type(stride) is not int or stride < 1:
        raise ValueError("stride must be a positive integer")
    with open_snapshot(manifest) as store:
        refused = _refusal(store, engine)
        if refused is not None:
            return refused
        stage = PositionStage(manifest, store, engine, stride, dry_run)
        refused = stage.prepare(out)
        if refused is not None:
            return refused
        stage.select(limit)
        refused = stage.run()
        if refused is not None:
            return refused
    return stage.report(run_started)


def _refusal(store, engine) -> dict | None:
    """Why a snapshot cannot take an engine's edges: a JSON manifest, or a parser that is not the current one."""
    if store.format != "sqlite" or store.connection is None:
        return {"engine": engine.name, "available": False,
                "reason": "a JSON manifest holds no reference table; write the snapshot "
                          "in its default sqlite format to attach an engine"}
    import snapshot
    if store.metadata.get("parser_fingerprint") != snapshot.parser_fingerprint():
        return {"engine": engine.name, "available": False,
                "reason": "the snapshot's parser fingerprint is not the current one; "
                          "write a current snapshot before attaching an engine"}
    return None


class _NotReady(Exception):
    """The engine did not start: the stage's report, returned as it is."""

    def __init__(self, report: dict):
        super().__init__(report.get("reason"))
        self.report = report


class PositionStage:
    """One engine asked at the call positions of its languages, inside one open snapshot (`resolve_edges`)."""

    def __init__(self, manifest: Path, store, engine, stride: int, dry_run: bool):
        self.manifest, self.store, self.engine, self.stride, self.dry_run = manifest, store, engine, stride, dry_run
        self.connection = store.connection
        project_root = (Path(store["root"]) / store["target"]).resolve()
        self.project_root = project_root.parent if project_root.is_file() else project_root
        self.fingerprint = store.metadata.get("parser_fingerprint")
        self.languages = engine_languages(engine, self.connection)
        # The files hashed against the snapshot: those of its languages and of the ones its answers read.
        self.checked = (*self.languages, *getattr(engine, "reads", ()))
        self.edges: list[dict] = []
        self.answers: list[dict] = []
        self.skipped_position = 0
        self.latencies: list[float] = []
        self.declarations: dict[str, dict] = {}
        self.source_lines: dict[str, list[str]] = {}
        self.contracts: dict[str, bool] = {}
        self.holes_of: dict[str, tuple[str, str]] = {}
        self.progress = {"probed": False, "probe_elapsed": 0.0, "saved": 0, "published": time.perf_counter(),
                         "binding": None, "verified_after": None, "reused_identity": None, "written": None}

    def prepare(self, out: Path | None) -> dict | None:
        """The verified sources, the store's destination and the population; a refusal or None."""
        try:
            self.store_root, self.source_paths, self.verified_before = verify_sources(self.store, self.checked)
            self.destination = edge_destination(out or default_edge_store(self.manifest), self.manifest,
                                                self.source_paths)
        except (OSError, ValueError) as error:
            return {"engine": self.engine.name, "available": False,
                    "reason": str(error), "stage": "before-inference", "edges_store": None}
        if hasattr(self.engine, "sources"):
            # An engine that loads the sources itself gets the snapshot's perimeter, never the directory.
            wanted = set(self.engine.source_languages)
            self.engine.sources = sorted(self.source_paths[rel] for rel, language in self.connection.execute(
                "SELECT file, language FROM sem_coverage") if language in wanted and rel in self.source_paths)
        self.inventory = inventory_files(self.connection)
        self.hashes = {rel: entry.get("raw_hash") for rel, entry in self.store.iter_file_headers_only()}
        self._population()
        self.files = {language: self._files(language) for language in self.counts}
        return None

    def _files(self, language: str) -> dict | None:
        """A language's files and those the engine reads in part or not at all, with what it leaves out (`unread`,
        `nothing_read`): the `files` of its coverage. None for an engine that states nothing of it."""
        unread = getattr(self.engine, "unread", None)
        if unread is None:
            return None
        nothing_read = getattr(self.engine, "nothing_read", lambda path: None)
        rels = sorted(rel for rel, held in self.connection.execute("SELECT file, language FROM sem_coverage")
                      if held == language and rel in self.source_paths)
        missing = [{"path": rel, "reason": reason} for rel in rels
                   if (reason := nothing_read(self.source_paths[rel]) or unread(self.source_paths[rel]))]
        return {"snapshot": len(rels), "indexed": len(rels) - len(missing), "missing": missing}

    def _population(self) -> None:
        """The calls of the engine's languages: those to ask, those the lexical resolver bound, the sites."""
        connection, languages = self.connection, self.languages
        placeholders = ",".join("?" for _ in languages)
        rows = connection.execute(
            f"SELECT r.id, r.file, r.payload, r.l0, r.c0, r.l1, r.c1, c.language FROM sem_references r "
            f"JOIN sem_coverage c ON c.file=r.file "
            f"WHERE r.kind='call' AND r.resolution IN ('unresolved','resolved') AND c.language IN ({placeholders}) "
            f"ORDER BY r.id", tuple(languages)).fetchall()
        # The calls the lexical resolver bound, with the target the engine is checked against.
        self.lexical = dict(connection.execute(
            "SELECT id, target_id FROM sem_references WHERE kind='call' AND resolution='resolved'"))
        # Every call and read of these languages ends in an edge row or a hole (`holes_of`, by reference).
        self.sites = connection.execute(
            f"SELECT r.id, r.file, r.kind, r.l0, r.c0, c.language, r.resolution FROM sem_references r "
            f"JOIN sem_coverage c ON c.file=r.file WHERE r.kind IN ('call','read') AND c.language IN ({placeholders}) "
            f"ORDER BY r.id", tuple(languages)).fetchall()
        self.callee_names = project_callee_names(connection)
        self.counts = {language: {"population": 0, "selected": 0, "asked": 0, "reused": 0, "confirmed": 0,
                                  "candidates": 0, "verdicts": {}, "excluded_classes": {},
                                  "checked": {"population": 0, "asked": 0, "same": 0, "corrected": 0,
                                              "external": 0}}
                       for language in languages}
        self.population, self.bound = [], []
        for row in rows:
            if row[0] in self.lexical:
                self.bound.append(row)
                self.counts[row[7]]["checked"]["population"] += 1
                continue
            reference_class = classify_reference(_unpack(row[2]), self.callee_names)
            if reference_class in ("askable", "dynamic"):
                self.population.append(row)
                self.counts[row[7]]["population"] += 1
            else:
                excluded = self.counts[row[7]]["excluded_classes"]
                excluded[reference_class] = excluded.get(reference_class, 0) + 1
                self.holes_of[row[0]] = ("not-asked", reference_class)

    def select(self, limit: int | None) -> None:
        """The answers to reuse and the positions to ask, in the order they are worth most."""
        # Reuse: same engine context, same file and imports, same target bytes.
        self.context = None if self.dry_run else getattr(self.engine, "context", lambda: None)()
        cached, known, self.cache_path, self.cache_note, self.digests = {}, {}, None, None, {}
        if self.context is not None:
            self.context = (f"{self.context}|{self.store['target']}|{self.fingerprint}|"
                            f"{semantic_store.RESOLVER_VERSION}|{EDGE_SCHEMA}")
            if hasattr(self.engine, "implementations"):
                self.context += "|implementation"
            self.digests = dependency_digests(self.hashes, file_dependencies(self.connection))
            try:
                self.cache_path = edge_destination(default_answers_path(self.manifest), self.manifest,
                                                   self.source_paths)
                cached, known = load_answers(self.cache_path, self.context, self.engine.name)
            except (OSError, ValueError, sqlite3.Error) as error:
                self.cache_path, self.cache_note = None, f"answer cache unusable: {error}"
        ranks = file_ranks(self.connection)
        for group in (self.population, self.bound):
            group.sort(key=lambda row: (known.get(row[1]) == self.hashes.get(row[1]),
                                        ((_unpack(row[2]).get("parts") or [""])[-1] not in self.callee_names),
                                        -ranks.get(row[1], 0.0),
                                        row[1], row[3] or 0, row[4] or 0, row[0]))

        def reusable(row):
            answer = cached.get(row[0])
            if answer is None or answer["file"] != row[1] or answer["file_digest"] != self.digests.get(row[1]):
                return None
            if any(self.hashes.get(rel) != digest for rel, digest in json.loads(answer["targets"]).items()):
                return None
            return answer

        self.reused, pending, unchecked = [], [], []
        for row in self.population + self.bound:
            answer = reusable(row)
            if answer is None:
                (unchecked if row[0] in self.lexical else pending).append(row)
            else:
                self.reused.append((row, answer))
        # The unresolved calls come first: a limit spends its questions on them.
        self.selected = pending[::self.stride] + unchecked[::self.stride]
        if limit is not None:
            self.selected = self.selected[:limit]
        self.kept_entries, self.kept_edges, self.kept_holes, self.kept_reports = kept_languages(
            self.destination, self.store, self.counts)

    def lines_for(self, rel: str) -> list[str]:
        if rel not in self.source_lines:
            self.source_lines[rel] = self.source_paths[rel].read_text(encoding="utf-8").split("\n")
        return self.source_lines[rel]

    def contract(self, identity: str) -> bool:
        """Whether a declaration is a method an interface, a trait or a type declares."""
        if identity not in self.contracts:
            row = self.connection.execute("SELECT payload FROM sem_declarations WHERE id=?", (identity,)).fetchone()
            self.contracts[identity] = bool(row and (_unpack(row[0]) or {}).get("contract"))
        return self.contracts[identity]

    def count(self, language: str, verdict: str, reference_id=None, asked: bool = False) -> None:
        """One verdict on an unresolved call; the bound calls are counted in `checked`.

        A call named by `reference_id` gets no edge: a hole, `engine-unresolved` once asked, else `not-asked`.
        """
        if reference_id is not None:
            self.holes_of[reference_id] = ("engine-unresolved" if asked else "not-asked", verdict)
        if reference_id in self.lexical:
            return
        verdicts = self.counts[language]["verdicts"]
        verdicts[verdict] = verdicts.get(verdict, 0) + 1

    def record(self, reference_id, rel, language, payload, verdict, target_id, resolver, line, column) -> None:
        """One answer as an edge row: the end class in `verdict`, the engine's own verdict in `payload.detail`."""
        if reference_id in self.lexical:
            # The engine agrees with the lexical target, names another declaration or a place outside.
            checked = self.counts[language]["checked"]
            if verdict.startswith("edge-") and target_id:
                checked["same" if target_id == self.lexical[reference_id] else "corrected"] += 1
            elif verdict == "external-definition":
                checked["external"] += 1
            else:
                self.holes_of[reference_id] = ("engine-unresolved", verdict)
                return
        else:
            self.count(language, verdict)
            if verdict.startswith("edge-") and target_id:
                self.counts[language]["confirmed"] += 1
            elif verdict in CANDIDATE_REASONS:
                self.counts[language]["candidates"] += 1
            else:
                # Any other verdict, an outside place included, is a hole: the view reads the call as today.
                self.holes_of[reference_id] = ("engine-unresolved", verdict)
                return
        sure = verdict.startswith("edge-") or verdict == "external-definition"
        confidence = "confirmed" if sure else "uncertain"
        doubt = {} if sure else {"uncertain": {"reason": verdict, "candidates": []}}
        self.edges.append({
            "reference_id": reference_id, "file": rel, "language": language, "kind": "call",
            # The stored payload already qualifies its caller with its file.
            "caller": payload.get("caller"), "l0": line, "c0": column,
            "verdict": "project-callable" if verdict.startswith("edge-") else POSITION_ENDS[verdict],
            "target_id": target_id, "symbol": None, "resolver": resolver, "confidence": confidence,
            "payload": {**payload, "resolver": resolver, "confidence": confidence, "reason": f"engine-{verdict}",
                        "detail": verdict, "chain": [], **doubt},
        })

    def identity(self) -> str:
        return self.engine.identity() if self.progress["probed"] else (
            self.progress["reused_identity"] or self.engine.name)

    def holes(self) -> list[dict]:
        # A call the limit or the stride left out is `not-selected`; what no rule asks is `not-asked`.
        answered = {edge["reference_id"] for edge in self.edges}
        holes_of = self.holes_of
        return [{"reference_id": reference_id, "file": rel, "language": language, "kind": kind, "l0": l0, "c0": c0,
                 "class": holes_of[reference_id][0] if reference_id in holes_of else
                 "not-selected" if kind != "read" and resolution in ("unresolved", "resolved") else "not-asked",
                 "resolver": self.identity(),
                 "reason": holes_of[reference_id][1] if reference_id in holes_of else
                 "read" if kind == "read" else "not-selected" if resolution in ("unresolved", "resolved")
                 else resolution}
                for reference_id, rel, kind, l0, c0, language, resolution in self.sites if reference_id not in answered]

    def _coverage(self, written_holes: list[dict]) -> dict:
        return {language: language_coverage(
            [{"reference_id": reference_id, "kind": kind, "site": f"{rel}:{l0}", "lexical": resolution == "resolved"}
             for reference_id, rel, kind, l0, _c0, site_language, resolution in self.sites
             if site_language == language],
            [edge for edge in self.edges if edge["language"] == language],
            [hole for hole in written_holes if hole["language"] == language], self.files[language])
            for language in self.counts}

    def _none_read(self, language: str) -> str | None:
        """Why a language is not fresh when the engine reads nothing of any of its files: none is read whole (its
        `files`, with each missing one's reason) and no call of theirs is one the engine is given (`population`,
        the lexically bound ones checked), as `engine_pass.index_stage` fails a language none of whose files is
        in the index. A file read in part, a script block with a call to ask, keeps the language fresh, with its
        coverage a lower bound."""
        files, numbers = self.files[language], self.counts[language]
        if not files or not files["snapshot"] or files["indexed"] or numbers["population"] \
                or numbers["checked"]["population"]:
            return None
        import collections
        causes = collections.Counter(item["reason"] for item in files["missing"]).most_common(3)
        excluded = numbers["excluded_classes"]
        return (f"nothing of the {files['snapshot']} {language} files is read: "
                + ", ".join(f"{reason} ({count})" for reason, count in causes)
                + (f"; none of their {sum(excluded.values())} calls is asked: "
                   + ", ".join(f"{name} ({count})" for name, count in sorted(excluded.items())) if excluded else ""))

    def _entries(self, partial: bool, covered: dict, verified_after) -> dict:
        """Each language's store entry as the stage stands: `partial` while the stage runs, then `fresh`, or
        `failed` with the `reason` for a language of whose files nothing is read (`_none_read`)."""
        created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entries = {}
        for language, numbers in self.counts.items():
            if numbers["confirmed"] + numbers["candidates"]:
                no_edges_reason = None
            elif not numbers["population"]:
                no_edges_reason = "no-unresolved-calls"
            elif not numbers["selected"] or not numbers["asked"] + numbers["reused"]:
                no_edges_reason = "not-sampled"
            else:
                no_edges_reason = "no-project-targets"
            unread = None if partial else self._none_read(language)
            entries[language] = {
                "engine": self.identity(), "state": "partial" if partial else "failed" if unread else "fresh",
                **({"reason": unread} if unread else {}), "coverage": covered[language],
                **numbers, "stride": self.stride, "verdicts": dict(sorted(numbers["verdicts"].items())),
                "excluded_classes": dict(sorted(numbers["excluded_classes"].items())),
                "no_edges_reason": no_edges_reason, "created_at": created,
                "source_verification": {"before_inference": self.verified_before, "after_inference": verified_after}}
        return entries

    def publish(self, partial: bool) -> dict | None:
        """Verify the sources, then write the store and the new answers; a failure or None."""
        written_holes = self.holes()
        covered = self._coverage(written_holes)
        broken = [coverage_violation(language, coverage) for language, coverage in covered.items()]
        if any(broken):
            return {"reason": "; ".join(reason for reason in broken if reason), "stage": "coverage"}
        try:
            _root, _paths, verified_after = verify_sources(self.store, self.checked)
            edge_destination(self.destination, self.manifest, self.source_paths)
        except (OSError, ValueError) as error:
            return {"reason": str(error), "stage": "after-inference"}
        entries = self._entries(partial, covered, verified_after)
        report = self.engine.report() if hasattr(self.engine, "report") else {}
        binding = store_binding(self.store, self.manifest, self.fingerprint, {**self.kept_entries, **entries},
                                {**self.kept_reports, self.identity(): report})
        self.progress.update(binding=binding, verified_after=verified_after, published=time.perf_counter())
        if self.dry_run:
            return None
        try:
            self.progress["written"] = write_edge_store(self.destination, self.kept_edges + self.edges, binding,
                                                        self.kept_holes + written_holes)
        except (OSError, sqlite3.Error, ValueError) as error:
            return {"reason": f"could not publish the engine edge store: {error}", "stage": "write"}
        if self.cache_path is not None:
            try:
                save_answers(self.cache_path, self.context, self.engine.name, self.answers[self.progress["saved"]:])
                self.progress["saved"] = len(self.answers)
            except (OSError, sqlite3.Error) as error:
                self.progress["cache_error"] = f"answer cache not written: {error}"
        return None

    def run(self) -> dict | None:
        """Record the reused answers, ask the selected positions and publish; the stage's refusal or None."""
        counts = self.counts
        for (reference_id, rel, blob, _l0, _c0, _l1, _c1, language), answer in self.reused:
            if reference_id in self.lexical:
                counts[language]["checked"]["asked"] += 1
            else:
                counts[language]["selected"] += 1
                counts[language]["reused"] += 1
            self.progress["reused_identity"] = self.progress["reused_identity"] or answer["resolver"]
            self.record(reference_id, rel, language, _unpack(blob), answer["verdict"], answer["target_id"],
                        answer["resolver"], answer["line"], answer["column"])
        if self.reused and self.selected and not self.dry_run:
            # The reusable part of the graph is usable at once, before the engine starts.
            early = self.publish(partial=True)
            if early is not None:
                return {"engine": self.identity(), "available": False, "languages": list(self.languages),
                        "edges_store": None, **early}
        failure = None
        try:
            for row in self.selected:
                failure = self._ask(row)
                if failure is not None:
                    break
        except _NotReady as refused:
            return refused.report
        except EngineFailure as error:
            failure = {"reason": str(error), "stage": "inference",
                       "memory_exhausted": bool(MEMORY_EXHAUSTED.search(str(error)))}
        except MemoryError:
            failure = {"reason": "MemoryError during inference", "stage": "inference", "memory_exhausted": True}
        finally:
            closer = getattr(self.engine, "close", None)
            if closer is not None:
                closer()
        if failure is not None and failure["stage"] == "inference":
            # What the engine proved before it failed stays, and the next pass resumes from it.
            self.publish(partial=True)
        if failure is None:
            failure = self.publish(partial=False)
        if failure is not None:
            return {"engine": self.identity(), "available": False, "languages": list(self.languages),
                    "edges_store": None, **failure}
        return None

    def _position(self, rel, payload, l0, c0, l1, c1, language, reference_id) -> int | None:
        """The byte column of the callee name, or None when the call has no position to ask, counted."""
        parts = payload.get("parts") or []
        if not parts:
            # A reference with no parts is a dynamic callee, not a position this
            # command failed to find: the verdict keeps the payload's own reason
            # so the declared coverage says what was really asked about.
            self.count(language, payload.get("reason") or "dynamic-reference", reference_id)
            return None
        if not l0 or not l1:
            self.count(language, "no-position", reference_id)
            return None
        try:
            lines = self.lines_for(rel)
        except (OSError, UnicodeError):
            lines = []
        if not 1 <= l0 <= l1 <= len(lines):
            self.count(language, "no-position", reference_id)
            return None
        column = callee_column(lines[l1 - 1], [l0, c0, l1, c1], parts[-1])
        if column is None:
            self.skipped_position += 1
            self.count(language, "position-unverified", reference_id)
        return column

    def _start(self) -> None:
        """The engine starts only once a position needs it; one that does not start ends the stage."""
        started = time.perf_counter()
        try:
            ready, reason = self.engine.probe()
        except MemoryError:
            ready, reason = False, "MemoryError while the engine started"
        self.progress["probe_elapsed"] = time.perf_counter() - started
        if not ready:
            raise _NotReady({"engine": self.engine.name, "available": False, "reason": reason,
                             "install": getattr(self.engine, "install", None), "languages": list(self.languages),
                             "memory_exhausted": bool(MEMORY_EXHAUSTED.search(reason or ""))})
        self.progress["probed"] = True

    def _ask(self, row) -> dict | None:
        """Ask one selected position and record the answer; a failure that ends the loop, or None."""
        reference_id, rel, blob, l0, c0, l1, c1, language = row
        counts = self.counts
        counts[language]["selected"] += reference_id not in self.lexical
        payload = _unpack(blob)
        column = self._position(rel, payload, l0, c0, l1, c1, language, reference_id)
        if column is None:
            return None
        if not self.progress["probed"]:
            self._start()
        started = time.perf_counter()
        (counts[language]["checked"] if reference_id in self.lexical else counts[language])["asked"] += 1
        try:
            inferred = self.engine.definitions(self.source_paths[rel], l1, column)
        except (EngineFailure, MemoryError):
            raise
        except Exception as error:
            self.count(language, f"infer-error:{type(error).__name__}", reference_id, asked=True)
            return None
        finally:
            self.latencies.append(time.perf_counter() - started)
        try:
            verdict, target, witnesses = self._grade(inferred, rel, l1, column)
        except (OSError, UnicodeError) as error:
            return {"reason": f"target source became unavailable during inference: {error}",
                    "stage": "after-inference"}
        target_id = (target or {}).get("id")
        self.record(reference_id, rel, language, payload, verdict, target_id, self.engine.identity(), l1, column)
        if self.context is not None:
            self.answers.append({"context": self.context, "engine": self.engine.name, "reference_id": reference_id,
                                 "file": rel, "file_hash": self.hashes.get(rel) or "",
                                 "file_digest": self.digests.get(rel, ""), "verdict": verdict, "target_id": target_id,
                                 "targets": answer_targets(witnesses, self.store_root, self.hashes),
                                 "resolver": self.engine.identity(), "line": l1, "column": column})
        if not self.dry_run and time.perf_counter() - self.progress["published"] >= PUBLISH_SECONDS:
            return self.publish(partial=True)
        return None

    def _table_for(self, name: str):
        return symbol_table(self.connection, name, "\n".join(self.lines_for(name)))

    def _grade(self, inferred, rel: str, line: int, column: int) -> tuple:
        """The verdict and target of an engine's answer, with every location it named (`witnesses`)."""
        witnesses = list(inferred)

        def follow(location):
            try:
                children = self.engine.definitions(Path(location.module_path), location.line, location.column)
            except (EngineFailure, MemoryError):
                raise
            except Exception:
                # An unsupported follow-up is missing evidence, never external.
                return []
            witnesses.extend(children)
            return children

        verdict, target = grade_all(inferred, self.inventory, self.declarations, self.store_root, self._table_for,
                                    follow=follow)
        if hasattr(self.engine, "implementations") and (
                verdict in ("project-not-a-symbol", "ambiguous-target")
                or (verdict.startswith("edge-") and target and self.contract(target["id"]))):
            verdict, target = self._implementation(rel, line, column, witnesses, verdict, target)
        return verdict, target, witnesses

    def _implementation(self, rel: str, line: int, column: int, witnesses: list, verdict: str, target) -> tuple:
        """The declaration is a contract or a value: the target is the one place that implements it,
        when no implementation falls outside the project's declarations."""
        try:
            implemented = list(self.engine.implementations(self.source_paths[rel], line, column))
        except (EngineFailure, MemoryError):
            raise
        except Exception:
            implemented = []
        witnesses.extend(implemented)
        concrete, elsewhere = {}, False
        for item in implemented:
            found_verdict, found = grade(item, self.inventory, self.declarations, self.store_root, self._table_for)
            if not (found_verdict.startswith("edge-") and found):
                elsewhere = True
            elif not self.contract(found["id"]):
                concrete[found["id"]] = (found_verdict, found)
        if len(concrete) == 1 and not elsewhere:
            return next(iter(concrete.values()))
        return verdict, target

    def _totals(self, entries: dict) -> tuple[dict, dict, dict]:
        totals = {key: sum(entry[key] for entry in entries.values())
                  for key in ("population", "selected", "reused", "confirmed", "candidates")}
        verdicts: dict[str, int] = {}
        excluded_classes: dict[str, int] = {}
        for entry in entries.values():
            for key, value in entry["verdicts"].items():
                verdicts[key] = verdicts.get(key, 0) + value
            for key, value in entry["excluded_classes"].items():
                excluded_classes[key] = excluded_classes.get(key, 0) + value
        return totals, verdicts, excluded_classes

    def report(self, run_started: float) -> dict:
        """The stage's report once its store is published."""
        latencies, progress = sorted(self.latencies), self.progress
        entries = {language: progress["binding"]["languages"][language] for language in self.counts}
        asked = sum(entry["asked"] for entry in entries.values())
        totals, verdicts, excluded_classes = self._totals(entries)
        reasons = {entry["no_edges_reason"] for entry in entries.values()} - {None}
        engine_report = self.engine.report() if hasattr(self.engine, "report") else {}
        unread = [{"kind": "language_not_indexed", "language": language, "detail": entry["reason"]}
                  for language, entry in entries.items() if entry["state"] == "failed"]
        return {
            "engine": self.identity(),
            "available": True,
            "project_root": self.project_root.as_posix(),
            **engine_report,
            "languages": entries,
            "population": totals["population"],
            "population_language": self.languages[0] if len(self.languages) == 1 else "multi",
            "selected": totals["selected"],
            "asked": asked,
            "reused": totals["reused"],
            "answer_cache": self.cache_path.as_posix() if self.cache_path else None,
            **({"answer_cache_note": progress.get("cache_error") or self.cache_note}
               if progress.get("cache_error") or self.cache_note else {}),
            "stride": self.stride,
            "confirmed_edges": totals["confirmed"],
            "candidates": totals["candidates"],
            "no_edges_reason": None if totals["confirmed"] or totals["candidates"] else
            (reasons.pop() if len(reasons) == 1 else "no-project-targets"),
            "position_unverified": self.skipped_position,
            "excluded_classes": excluded_classes,
            "coverage": {language: entry["coverage"] for language, entry in entries.items()},
            "source_verification": {"before_inference": self.verified_before,
                                    "after_inference": progress["verified_after"]},
            "verdicts": verdicts,
            **self._timings(latencies, asked, totals, run_started),
            "dry_run": self.dry_run,
            "edges_store": progress["written"].as_posix() if progress["written"] else None,
            **({"gaps": unread} if unread else {}),
            "note": "Engine edges live in a derived store bound to this snapshot; the "
                    "snapshot itself is unchanged. Every edge names payload.resolver, so "
                    "engine edges are never counted together with builtin-lexical ones.",
        }

    def _timings(self, latencies: list[float], asked: int, totals: dict, run_started: float) -> dict:
        return {
            "probe_init_elapsed_ms": round(1000 * self.progress["probe_elapsed"], 1),
            "inference_elapsed_ms": round(1000 * sum(latencies), 1),
            "total_elapsed_ms": round(1000 * (time.perf_counter() - run_started), 1),
            "latency_mean_ms": round(1000 * sum(latencies) / len(latencies), 1) if latencies else None,
            "latency_p95_ms": round(1000 * latencies[math.ceil(len(latencies) * 0.95) - 1], 1) if latencies else None,
            "inference_only_extrapolation": {
                "estimated_ms": round(1000 * sum(latencies) / asked * totals["population"], 1) if asked else None,
                "asked": asked, "selected": totals["selected"], "population": totals["population"],
                "stride": self.stride,
                "sampling_bias": "References are ordered deterministically by value: edited and new files first, "
                                 "then files by rank, then by position; reused answers are taken first, the rest "
                                 "sampled by stride, then truncated by limit. Dynamic or unverified selected "
                                 "references receive no inference request.",
                "assumption": "Every population reference requires one request at the observed mean request cost.",
                "cost_scope": "Engine inference only; probe/init, source verification, grading and output writing "
                              "excluded.",
            },
        }
