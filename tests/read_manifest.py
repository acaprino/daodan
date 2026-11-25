"""The manifest dict the tests read: the snapshot `snapshot.read_project`, the one reading, writes of a tree.

`snapshot.build_manifest` returned this dict from a reading of its own; the JSON snapshot `read_project` writes holds the
same keys and files, so a test that needs the dict reads that file back.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import snapshot  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402


def read_manifest(target, *, previous: dict | None = None, parse_results: dict | None = None,
                  observations: dict | None = None) -> dict:
    """The manifest of `target`. A `previous` dict is the manifest to reuse the entries of, as `read_project(previous=)`
    reuses a store's. `observations`, when given, receives the bytes of each file by relative path, as a caller that read
    them passes them to the consumers (`source_observations`); they come from the disk, so not with `parse_results`."""
    if observations is not None and parse_results is not None:
        raise ValueError("observations are the bytes on disk: they are not those of parse_results")
    with tempfile.TemporaryDirectory(prefix="manifest-") as temporary:
        folder = Path(temporary).resolve()
        out, kept = folder / "manifest.json", folder / "previous.json"
        if previous is None:
            snapshot.read_project(target, out, format="json", parse_results=parse_results)
        else:
            kept.write_text(json.dumps(previous), encoding="utf-8")
            with open_snapshot(kept) as store:
                snapshot.read_project(target, out, format="json", previous=store, parse_results=parse_results)
        manifest = json.loads(out.read_text(encoding="utf-8"))
    if observations is not None:
        root = Path(manifest["root"])
        observations.clear()
        observations.update({rel: (root / rel).read_bytes() for rel in manifest["files"]})
    return manifest
