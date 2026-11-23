"""`scan` reads no symbol (spec of the pipeline, 8.11 step 5, piece B): what the pre-map's sources write does not depend on
the snapshot's declarations, so `scan` can run before `parse`.

Angular's source keeps its own binding (spec 8.13 point 2: the class of the component and the type-checker's answer are not
one of the binder's two forms), but the binding runs when the links are made: the pre-map row carries the class, the call and
the type-checker's answer, never a method looked up in the snapshot.
"""
from __future__ import annotations

import sqlite3
import sys
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_codebase_map_premap_angular as angular_tests  # noqa: E402
from test_codebase_map_premap_container_runner import manifest_of, premap  # noqa: E402


def _without_declarations(manifest: Path) -> None:
    with closing(sqlite3.connect(manifest)) as db:
        db.execute("DELETE FROM sem_declarations")
        db.commit()


def test_angulars_pre_map_rows_are_the_same_whether_or_not_the_snapshot_declares_anything(tmp_path):
    rows = []
    for name, strip in (("whole", False), ("stripped", True)):
        _, manifest = manifest_of(tmp_path / name, angular_tests.project_files())
        if strip:
            _without_declarations(manifest)
        record = premap.write(manifest, sources=(premap.angular,), runner=lambda commands: angular_tests.recorded("fixture.json"))
        rows.append(sorted(record["framework_entries"], key=lambda row: (row["site"], row["column"], repr(row))))
    assert rows[0] and rows[0] == rows[1]
    assert not [row for row in rows[0] if row.get("gap", "").startswith("the snapshot declares no class")]


def test_the_links_still_bind_each_event_to_the_method_of_its_class(tmp_path):
    """The binding moved to the links: the three cases of the fixture still end on their methods there."""
    import entries
    _, manifest = manifest_of(tmp_path, angular_tests.project_files())
    premap.write(manifest, sources=(premap.angular,), runner=lambda commands: angular_tests.recorded("fixture.json"))
    bound = {(row["site"], row["symbol"]) for row in entries.compiled([], manifest) if not row.get("gap")}
    app, html = angular_tests.APP, "src/app/app.component.html"
    assert {(f"{html}:2", f"{app}::AppComponent.save"), (f"{html}:3", f"{app}::AppComponent.save"),
            (f"{html}:4", "src/app/order.service.ts::OrderService.cancel")} <= bound
