"""Why a file has no document, and what an adapter does not read: each reason names the real cause, and a part
no adapter reads is a declared gap, never a silent one. No indexer, no server, no network.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_reasons.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import code_graph  # noqa: E402
import engine_pass  # noqa: E402
import languages  # noqa: E402
import snapshot  # noqa: E402
import source_files  # noqa: E402
from indexers import css, go, rust, typescript  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402


def _project(root: Path, sources: dict[str, str]) -> Path:
    for rel, text in sources.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _index(root: Path, documents: list[str]) -> code_graph.Index:
    """An index holding a document for each of `documents`."""
    index = code_graph.Index(root)
    index.documents = {rel: [] for rel in documents}
    return index


# ---------------------------------------------------------------------------------------------------------------
# Rust and Go: a file of a crate or module whose run wrote no index

NO_MOD = "no crate includes it: no `mod` item of an indexed file loads it"


def test_a_rust_file_of_a_crate_whose_run_wrote_no_index_says_so(tmp_path):
    _project(tmp_path, {"src/lib.rs": "mod used;\n", "src/used.rs": "", "src/orphan.rs": "",
                        "tools/gen/src/main.rs": "mod parse;\n", "tools/gen/src/parse.rs": "",
                        "tools/gen/src/orphan.rs": ""})
    configs = rust.tasks({"roots": ["", "tools/gen"], "failed": {"tools/gen": "exit code 101"}})
    absent = ["src/orphan.rs", "tools/gen/src/main.rs", "tools/gen/src/parse.rs", "tools/gen/src/orphan.rs"]
    failed = "the rust-analyzer run of its crate tools/gen wrote no index (exit code 101)"
    assert rust.missing(_index(tmp_path, ["src/lib.rs", "src/used.rs"]), absent, configs) == {
        "src/orphan.rs": NO_MOD, "tools/gen/src/main.rs": failed, "tools/gen/src/parse.rs": failed,
        "tools/gen/src/orphan.rs": failed}
    # A crate another run read is not failed: the workspace's run indexed it.
    member = _index(tmp_path, ["src/lib.rs", "tools/gen/src/main.rs", "tools/gen/src/parse.rs"])
    assert rust.missing(member, ["tools/gen/src/orphan.rs"], configs) == {"tools/gen/src/orphan.rs": NO_MOD}
    # Without what the run brought back, only the `mod` items speak.
    assert rust.missing(_index(tmp_path, ["src/lib.rs"]), ["src/orphan.rs", "src/used.rs"]) == {"src/orphan.rs": NO_MOD}
    assert rust.tasks(None) == {}


FEATURES = ("pub fn first_newline(haystack: &[u8]) -> Option<usize> {\n"
            "    #[cfg(feature = \"fast\")]\n    {\n        memchr::memchr(b'\\n', haystack)\n    }\n"
            "    #[cfg(not(feature = \"fast\"))]\n    {\n        haystack.iter().position(|&b| b == b'\\n')\n    }\n}\n"
            "#[cfg(any(unix, not(feature = \"fast\")))]\nfn other() { helper(); }\n"
            "#[cfg(all(unix, not(feature = \"fast\")))]\nfn third() { helper(); }\n"
            "#[cfg(target_endian = \"big\")]\nfn fourth() { helper(); }\n")


def test_rust_code_a_cfg_leaves_out_says_so(tmp_path):
    """rust-analyzer reads one configuration (`CONFIGURATION`): every feature on, Linux in Daodan's container, the
    cfgs the build scripts set; it writes nothing of the code a `cfg` false there leaves out. sys-rust-features: the
    `not(feature = "fast")` block; semver: `#[cfg(target_endian = "big")]` and tests/node/mod.rs, whose
    `#![cfg(test_node_semver)]` only RUSTFLAGS sets; hoppscotch: `#[cfg(target_os = "macos")] mod macos;` and
    tauri's `#[cfg(desktop)]`, set by its build script. A cfg rust-analyzer may set (`test`) decides nothing."""
    _project(tmp_path, {"src/lib.rs": "mod node;\nmod plain;\n" + FEATURES
                        + '#[cfg(target_os = "macos")]\nmod macos;\n#[cfg(desktop)]\nmod desktop;\n'
                          "#[cfg(test)]\nmod checks;\n",
                        "src/node.rs": "//! Compared with node-semver.\n#![cfg(test_node_semver)]\nuse x::Y;\n",
                        "src/plain.rs": "", "src/macos.rs": "", "src/desktop.rs": "", "src/checks.rs": ""})
    index = _index(tmp_path, ["src/lib.rs"])
    absent = ["src/node.rs", "src/plain.rs", "src/macos.rs", "src/desktop.rs", "src/checks.rs"]
    host = rust.CONFIGURATION
    assert rust.missing(index, absent) == {
        "src/node.rs": rust.CFG_OFF.format("test_node_semver", host),
        "src/desktop.rs": rust.MOD_OFF.format("desktop", host),
        **({"src/macos.rs": rust.MOD_OFF.format('target_os = "macos"', host)} if sys.platform != "darwin" else {})}
    cause = rust.unanswered(index)
    assert cause(("src/lib.rs", 10, 17)) == rust.INACTIVE.format('not(feature = "fast")', host)  # haystack.iter
    assert cause(("src/lib.rs", 6, 8)) is None  # memchr: the feature is on
    assert cause(("src/lib.rs", 14, 13)) == (None if os.name == "posix" else  # `any`: unix holds on the host
                                             rust.INACTIVE.format('any(unix, not(feature = "fast"))', host))
    assert cause(("src/lib.rs", 16, 13)) == rust.INACTIVE.format('all(unix, not(feature = "fast"))', host)  # `all`
    assert cause(("src/lib.rs", 18, 14)) == (rust.INACTIVE.format('target_endian = "big"', host)
                                            if sys.byteorder == "little" else None)


def test_a_rust_file_whose_loader_is_left_out_says_which_and_why(tmp_path):
    """hoppscotch's tauri-plugin-appload: `#[cfg(target_os = "macos")] mod macos;` leaves out src/ui/macos/mod.rs,
    and with it the posit.rs its `mod posit;` loads, which read "no crate includes it" (D-143). A file loaded only
    by files left out names the one that loads it and the cause that leaves the chain out; one no file loads at all
    still says so."""
    _project(tmp_path, {"src/lib.rs": '#[cfg(target_os = "macos")]\nmod macos;\n',
                        "src/macos/mod.rs": "mod posit;\nmod deeper;\n", "src/macos/posit.rs": "",
                        "src/macos/deeper.rs": "mod leaf;\n", "src/macos/deeper/leaf.rs": "", "src/orphan.rs": ""})
    absent = ["src/macos/mod.rs", "src/macos/posit.rs", "src/macos/deeper.rs", "src/macos/deeper/leaf.rs",
              "src/orphan.rs"]
    reasons = rust.missing(_index(tmp_path, ["src/lib.rs"]), absent)
    if sys.platform == "darwin":
        return
    first = rust.MOD_OFF.format('target_os = "macos"', rust.CONFIGURATION)
    loaded = rust.LOADER_OFF.format("src/macos/mod.rs", first)
    assert reasons == {"src/macos/mod.rs": first, "src/macos/posit.rs": loaded, "src/macos/deeper.rs": loaded,
                       "src/macos/deeper/leaf.rs": rust.LOADER_OFF.format("src/macos/deeper.rs", first),
                       "src/orphan.rs": rust.NO_CRATE}


def test_a_go_file_left_out_by_its_name_or_by_a_run_without_index_says_so(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOS", "linux")
    monkeypatch.setenv("GOARCH", "amd64")
    _project(tmp_path, {name: "package a\n" for name in (
        "a.go", "a_windows.go", "a_linux.go", "a_linux_arm64_test.go", "a_amd64.go", "windows.go", "a_helper.go",
        "tools/tool.go")} | {"tagged.go": "//go:build ignore\n\npackage a\n"})
    configs = go.tasks({"roots": ["", "tools"], "failed": {"tools": "exit code 1"}})
    absent = ["a_windows.go", "a_linux.go", "a_linux_arm64_test.go", "a_amd64.go", "windows.go", "a_helper.go",
              "tagged.go", "tools/tool.go"]
    assert go.missing(_index(tmp_path, ["a.go"]), absent, configs) == {
        "a_windows.go": "file name constraint `windows`: the indexer's build is linux/amd64",
        "a_linux_arm64_test.go": "file name constraint `linux_arm64`: the indexer's build is linux/amd64",
        "tagged.go": "build constraint `//go:build ignore`",
        "tools/tool.go": "the scip-go run of its module tools wrote no index (exit code 1)"}
    assert go.missing(_index(tmp_path, ["a.go"]), ["a_windows.go"]) == {
        "a_windows.go": "file name constraint `windows`: the indexer's build is linux/amd64"}
    assert go.tasks(None) == {}
    # real-svc-robot-shop's dispatch: Go files and no go.mod, which its Dockerfile writes at build time.
    _project(tmp_path, {"dispatch/main.go": "package main\n"})
    assert go.missing(_index(tmp_path, []), ["dispatch/main.go"], go.tasks({"roots": [], "failed": {}})) == {
        "dispatch/main.go": go.NO_MODULE}


def test_a_declaration_file_beside_a_typescript_file_of_its_name_says_typescript_leaves_it_out(tmp_path):
    """D-160, measured with scip-typescript 0.6.2 on Modal: memos' web/src/types/common.d.ts has its document alone
    and none once common.ts is beside it; hoppscotch's packages/hoppscotch-kernel/vite.config.d.ts is beside
    vite.config.ts. Where an `include` matches both, TypeScript keeps the .ts or .tsx and leaves the .d.ts of
    the same name out of the program. A .d.ts with no such sibling, and any other file, keep no reason here."""
    index = _index(tmp_path, ["web/src/types/common.ts", "packages/kernel/vite.config.ts", "ui/Button.tsx"])
    absent = ["web/src/types/common.d.ts", "packages/kernel/vite.config.d.ts", "ui/Button.d.ts", "web/src/alone.d.ts",
              "web/src/lost.ts"]
    leaves = "TypeScript leaves it out of the program: {} beside it has its name, and an `include` that matches " \
             "both keeps that one"
    assert typescript.missing(index, absent) == {
        "web/src/types/common.d.ts": leaves.format("common.ts"),
        "packages/kernel/vite.config.d.ts": leaves.format("vite.config.ts"),
        "ui/Button.d.ts": leaves.format("Button.tsx")}


# ---------------------------------------------------------------------------------------------------------------
# The stylesheet graph: every markup file of the snapshot is read or declared missing

def test_every_markup_suffix_of_the_snapshot_is_read_or_declared_missing_with_its_reason(tmp_path):
    markup = {suffix for suffix, language in languages.SUPPORTED_EXTENSIONS.items()
              if language == languages.Language.MARKUP}
    assert markup <= set(css.READS)
    unread = sorted(markup - set(css.MARKUP) - set(css.COMPONENTS))
    assert unread == [".cshtml", ".erb", ".ftl", ".handlebars", ".hbs", ".j2", ".jinja", ".jsp", ".jspx",
                      ".liquid", ".mustache", ".njk", ".razor", ".twig", ".vm", ".xhtml"]
    assert {".pug", ".jade"} <= source_files.PRESENTATION_EXTENSIONS <= set(css.READS)  # file-level entries
    files = [f"views/page{suffix}" for suffix in unread]
    _project(tmp_path, {rel: "<p class=\"card\">x</p>\n" for rel in files})
    parsed = css.parse(tmp_path, files)
    assert parsed["records"] == [] and sorted(parsed["missing"]) == files
    assert {parsed["missing"][f"views/page{suffix}"] for suffix in (".cshtml", ".razor", ".jsp", ".jspx", ".ftl",
                                                                    ".vm")} == {"template language: no reader"}
    assert parsed["missing"]["views/page.xhtml"] == "XHTML: no reader"


def test_a_project_of_components_alone_brings_the_stylesheet_graph_into_the_pass(tmp_path):
    root = _project(tmp_path / "proj", {"App.vue": "<template>\n  <p class=\"x\">x</p>\n</template>\n"
                                                   "<style>\n.x { color: red }\n</style>\n"})
    snapshot.write_snapshot(root, tmp_path / "manifest.sqlite")
    with open_snapshot(tmp_path / "manifest.sqlite") as store:
        assert "stylesheet" in engine_pass.pass_languages(store.connection)
