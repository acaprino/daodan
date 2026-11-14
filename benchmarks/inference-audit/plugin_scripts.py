"""The plugin's scripts the benchmark runs: found beside the checkout this file sits in, or where the Modal
images mount them, and put on the import path. `code_sha256` names the graph code a container runs."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = next((parent / "plugins/codebase-map/skills/map/scripts" for parent in Path(__file__).resolve().parents
                if (parent / "plugins/codebase-map/skills/map/scripts").is_dir()), Path("/daodan/map/scripts"))
sys.path.insert(0, str(SCRIPTS))


def code_sha256() -> dict[str, str]:
    """The first twelve hex digits of the sha256 of the plugin's graph module and indexer adapters and of each
    adapter beside this file: what a container runs, to compare with the checkout before trusting its results."""
    files = {"code_graph.py": SCRIPTS / "code_graph.py"}
    files.update({f"indexers/{path.name}": path for path in sorted((SCRIPTS / "indexers").glob("*.py"))})
    files.update({f"adapters/{path.name}": path for path in sorted((HERE / "adapters").glob("*.py"))})
    return {name: hashlib.sha256(path.read_bytes()).hexdigest()[:12] for name, path in files.items()}
