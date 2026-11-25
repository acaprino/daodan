"""A parser that flags an error and shows no ERROR or missing node: the file is read around the node that carries it."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daodan/core"))
import semantic_store  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

# The companion object of a Spring controller of a real project, as written: two properties on one line, a `;` between them.
# tree-sitter's Kotlin grammar flags the class body (`has_error`) and gives no ERROR node and no missing token.
CONTROLLER = "\n".join([
    "class AccountDeletionController(private val deletion: AccountDeletionService) {",
    '    companion object { const val RECEIPT="ACCOUNT_DELETION_RECEIPT"; private val random=SecureRandom() }',
    '    @GetMapping("/api/v1/account/deletion")',
    "    fun summary() = deletion.summary()",
    "}", ""])


def test_a_file_whose_parser_flags_an_error_with_no_place_keeps_its_declarations_and_names_the_lines_it_distrusts(tmp_path):
    """Before, the file was read as `lexical` (source-not-successfully-parsed): no declaration at all, so a route handler of the
    file was none and every call to its routes found no handler (measured on a Next.js and Spring project, 5 calls of 33)."""
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src/Account.kt").write_text(CONTROLLER, encoding="utf-8")
    manifest = tmp_path / "out/manifest.sqlite"
    manifest.parent.mkdir()
    snapshot.read_project(project, manifest)
    with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
        functions = {name for [name] in db.execute("SELECT name FROM sem_declarations WHERE kind IN ('function', 'method')")}
        [[status]] = db.execute("SELECT status FROM sem_coverage WHERE file = 'src/Account.kt'")
        notes = (store.get_file_header("src/Account.kt") or {}).get("parser_notes")
    assert functions == {"summary"}
    assert status == "partial"
    assert "syntax error: line 2" in notes  # the line of the node that carries the error, not line 1
