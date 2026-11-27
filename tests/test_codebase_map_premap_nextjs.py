"""The routes a Next.js project's own `next typegen` writes, read from its output and bound to the snapshot.

The container is a fake: each folder's answers are recorded, and the validator.ts is the one the real tool wrote
for `benchmarks/system-map/real-paths/next-shop` (`tests/fixtures/premap/next/validator.ts`).
"""
from pathlib import Path
from unittest.mock import patch

from test_codebase_map_container_runner import container, container_runner, manifest_of, premap, recorder

SHOP_DIR = Path(__file__).resolve().parents[1] / "benchmarks/system-map/real-paths/next-shop"
SHOP = {path.relative_to(SHOP_DIR).as_posix(): path.read_text(encoding="utf-8")
        for path in SHOP_DIR.rglob("*") if path.is_file() and path.name != "package-lock.json"}
VALIDATOR = (Path(__file__).parent / "fixtures/premap/next/validator.ts").read_text(encoding="utf-8")
SOURCE = "next@daodan/premap/v4"
CANDIDATES = {  # the five blocks of the validator: file -> (shape, route, kind)
    "app/checkout/page.tsx": ("AppPageConfig", "/checkout", "rotta"),
    "app/orders/[id]/page.tsx": ("AppPageConfig", "/orders/[id]", "rotta"),
    "app/page.tsx": ("AppPageConfig", "/", "rotta"),
    "app/api/pay/route.ts": ("RouteHandlerConfig", "/api/pay", "rotta"),
    "app/layout.tsx": ("LayoutConfig", "/", "nessun ingresso"),
}


def done(text=VALIDATOR):
    """What the container answers for a folder: `next typegen`, then the `cat` of its validator.ts."""
    return ({"returncode": 0, "stdout": "Generating route types...\n", "stderr": ""},
            {"returncode": 0, "stdout": text, "stderr": ""})


def failed(error):
    return ({"returncode": 1, "stdout": "", "stderr": error},
            {"returncode": 1, "stdout": "", "stderr": "cat: .next/types/validator.ts: No such file or directory"})


def runner_for(answers):
    """A runner that answers each command from `answers`, folder -> (typegen answer, cat answer)."""
    asked = []

    def run(commands):
        asked.extend(commands)
        return [{"root": "/work", **answers[c["cwd"]][0 if c["argv"][0] == "npx" else 1]} for c in commands]
    return asked, run


def read(tmp_path, files, answers):
    _, manifest = manifest_of(tmp_path, files)
    asked, run = runner_for(answers)
    record = premap.write(manifest, sources=(premap.nextjs,), runner=run)
    return record, [g for g in record["gaps"] if g.get("source") == SOURCE], asked


def found(record):
    return {c["site"]: (c["shape"], c["path"], c.get("kind")) for c in record.get("framework_entries", [])}


def test_the_pages_the_route_handler_and_the_layout_of_typegen_become_candidates_with_their_files(tmp_path):
    record, gaps, asked = read(tmp_path, SHOP, {".": done()})
    assert found(record) == CANDIDATES and gaps == []
    page = next(c for c in record["framework_entries"] if c["site"] == "app/page.tsx")
    assert (page["reader"], page["symbol"], page["sources"]) == ("next", "app/page.tsx::<module>", [SOURCE])
    assert all(":" not in c["site"] for c in record["framework_entries"])  # the tool gives no line
    assert [c["argv"] for c in asked] == [["npx", "--no-install", "next", "typegen"], ["cat", ".next/types/validator.ts"]]


def test_each_row_carries_the_exports_or_the_methods_its_table_says_and_binds_nothing(tmp_path):
    """No source binds a row (spec 8.13, point 2): a page has its `exports`, a route handler its `methods`, a layout neither; the
    links' binder ties them to the functions."""
    record, _, _ = read(tmp_path, SHOP, {".": done()})
    by_file = {c["site"]: c for c in record["framework_entries"]}
    assert by_file["app/page.tsx"]["exports"] == ["default"] and "methods" not in by_file["app/page.tsx"]
    assert by_file["app/api/pay/route.ts"]["methods"][:2] == ["GET", "HEAD"] and "exports" not in by_file["app/api/pay/route.ts"]
    assert "exports" not in by_file["app/layout.tsx"] and "methods" not in by_file["app/layout.tsx"]
    assert not [c for c in record["framework_entries"] if "handler" in c or "handler_source" in c]


def test_the_comment_above_a_block_is_not_read(tmp_path):
    misleading = VALIDATOR.replace("// Validate ../../app/", "// Validate ../../nowhere/")
    record, gaps, _ = read(tmp_path, SHOP, {".": done(misleading)})
    assert found(record) == CANDIDATES and gaps == []


# The two blocks Next.js 16.4.6 wrote for `pages/about.tsx` and `pages/api/hello.ts` in a real run (Modal, 22 November
# 2026): the config types of the Pages Router are not generic, so no route is written in them. Their words are the
# gap text of that run, whitespace folded; the line breaks here are the template of the App Router's blocks.
PAGES_BLOCKS = """
// Validate ../../pages/about.tsx
{
  type __IsExpected<Specific extends PagesPageConfig> = Specific
  const handler = {} as typeof import("../../pages/about.js")
  type __Check = __IsExpected<typeof handler>
  // @ts-ignore
  type __Unused = __Check
}

// Validate ../../pages/api/hello.ts
{
  type __IsExpected<Specific extends ApiRouteConfig> = Specific
  const handler = {} as typeof import("../../pages/api/hello.js")
  type __Check = __IsExpected<typeof handler>
  // @ts-ignore
  type __Unused = __Check
}
"""


def test_a_block_with_no_route_in_its_config_type_is_a_gap_naming_its_file_and_the_others_are_read(tmp_path):
    files = {**SHOP, "pages/about.tsx": "export default function About() { return null; }\n",
             "pages/api/hello.ts": "export default function handler() {}\n"}
    record, gaps, _ = read(tmp_path, files, {".": done(VALIDATOR + PAGES_BLOCKS)})
    assert found(record) == CANDIDATES
    assert [(g["kind"], g["path"]) for g in gaps] == [("model_partial", "pages/about.tsx"),
                                                      ("model_partial", "pages/api/hello.ts")]
    for gap, config in zip(gaps, ("PagesPageConfig", "ApiRouteConfig")):
        assert "no route" in gap["detail"] and config in gap["detail"]


def test_a_config_type_the_table_does_not_know_gives_a_candidate_without_a_kind(tmp_path):
    unknown = VALIDATOR.replace('AppPageConfig<"/checkout">', 'ParallelSlotConfig<"/checkout">')
    record, _, _ = read(tmp_path, SHOP, {".": done(unknown)})
    assert found(record)["app/checkout/page.tsx"] == ("ParallelSlotConfig", "/checkout", None)
    assert found(record)["app/page.tsx"] == CANDIDATES["app/page.tsx"]


def test_an_import_that_matches_no_snapshot_file_is_a_gap_and_no_candidate(tmp_path):
    files = {rel: text for rel, text in SHOP.items() if rel != "app/orders/[id]/page.tsx"}
    record, [gap], _ = read(tmp_path, files, {".": done()})
    assert gap["kind"] == "outside_snapshot" and gap["path"] == "app/orders/[id]/page.js"
    assert "no file" in gap["detail"] and "stem" in gap["detail"]
    assert found(record) == {site: row for site, row in CANDIDATES.items() if site != "app/orders/[id]/page.tsx"}


def test_a_page_in_a_file_that_is_no_script_is_a_gap_naming_that_file_and_no_candidate(tmp_path):
    """`app/orders/[id]/page.md` is in the snapshot (a `.mdx` is not: the snapshot holds no file of that suffix, and
    the gap that says so is true): what typegen writes for it is not guessed, so it is no candidate, and the gap does
    not say that the snapshot lacks the file."""
    files = {rel: text for rel, text in SHOP.items() if rel != "app/orders/[id]/page.tsx"}
    files["app/orders/[id]/page.md"] = "# An order\n"
    record, [gap], _ = read(tmp_path, files, {".": done()})
    assert (gap["kind"], gap["path"]) == ("model_partial", "app/orders/[id]/page.md")
    assert "page.md" in gap["detail"] and "no file" not in gap["detail"]
    assert found(record) == {site: row for site, row in CANDIDATES.items() if site != "app/orders/[id]/page.tsx"}
    files["app/orders/[id]/page.mdx"] = "# An order\n"
    files.pop("app/orders/[id]/page.md")
    _, [gap], _ = read(tmp_path / "mdx", files, {".": done()})
    assert gap["kind"] == "outside_snapshot" and "no file" in gap["detail"]


def test_a_page_beside_a_stylesheet_of_the_same_name_is_still_one_candidate(tmp_path):
    """The import ends in `.js`: it names a script, never `page.css` or `page.scss`."""
    files = {**SHOP, "app/checkout/page.css": "form { margin: 0; }\n", "app/page.scss": "h1 { color: red; }\n"}
    record, gaps, _ = read(tmp_path, files, {".": done()})
    assert found(record) == CANDIDATES and gaps == []


def test_an_import_that_matches_two_snapshot_files_is_a_gap_and_no_candidate(tmp_path):
    files = {**SHOP, "app/checkout/page.jsx": "export default function Page() { return null; }\n"}
    record, [gap], _ = read(tmp_path, files, {".": done()})
    assert gap["kind"] == "model_partial" and gap["path"] == "app/checkout/page.js"
    assert "app/checkout/page.jsx" in gap["detail"] and "app/checkout/page.tsx" in gap["detail"]
    assert found(record) == {site: row for site, row in CANDIDATES.items() if site != "app/checkout/page.tsx"}


def test_typegen_failing_in_one_folder_is_that_folder_s_gap_and_the_other_is_still_read(tmp_path):
    files = {f"apps/{name}/{rel}": text for name in "ab" for rel, text in SHOP.items()}
    answers = {"apps/a": failed("Error: Cannot find module 'next/dist/bin/next'"), "apps/b": done()}
    record, [gap], _ = read(tmp_path, files, answers)
    assert gap["kind"] == "model_failed" and gap["path"] == "apps/a"
    assert "exited with 1" in gap["detail"] and "Cannot find module" in gap["detail"]
    assert found(record) == {f"apps/b/{site}": row for site, row in CANDIDATES.items()}


def test_a_validator_that_typegen_did_not_write_is_a_gap_naming_the_likely_causes(tmp_path):
    record, [gap], _ = read(tmp_path, SHOP, {".": (done()[0], failed("")[1])})
    assert gap["kind"] == "model_failed" and gap["path"] == "."
    assert "distDir" in gap["detail"] and "typegen" in gap["detail"] and ".next/types/validator.ts" in gap["detail"]
    assert "framework_entries" not in record


def test_a_validator_cut_in_the_middle_of_a_block_is_a_gap_and_no_candidate_from_that_file(tmp_path):
    cut = VALIDATOR[:VALIDATOR.index('typeof import("../../app/orders') + 20]  # the first block is whole
    record, [gap], _ = read(tmp_path, SHOP, {".": done(cut)})
    assert gap["kind"] == "model_partial" and gap["path"] == "."
    assert "did not parse whole" in gap["detail"] and "line" in gap["detail"]
    assert "framework_entries" not in record


def test_a_validator_that_parses_clean_and_holds_no_block_is_a_gap_saying_none_was_found(tmp_path):
    header = VALIDATOR[:VALIDATOR.index("// Validate")]  # the type declarations above the first block
    record, [gap], _ = read(tmp_path, SHOP, {".": done(header)})
    assert gap["kind"] == "model_partial" and gap["path"] == "."
    assert "no block of the known layout" in gap["detail"] and "no page" in gap["detail"]
    assert "framework_entries" not in record


def test_a_snapshot_with_no_package_json_declaring_next_runs_nothing(tmp_path):
    from snapshot_store import open_snapshot
    files = {"web/package.json": '{"dependencies": {"react": "19.3.1"}}\n', "docs/package.json": "{",
             "tools/package.json": '["next"]\n', "app/page.tsx": "export default function Page() { return null; }\n"}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        assert premap.nextjs.commands(premap.Context(manifest, store)) is None
    record = premap.write(manifest, sources=(premap.nextjs,), runner=lambda commands: 1 / 0)
    assert record["sources"][0]["state"] == "not_needed" and "framework_entries" not in record


def test_each_package_json_declaring_next_among_its_dependencies_or_dev_dependencies_is_one_run(tmp_path):
    from snapshot_store import open_snapshot
    files = {"apps/a/package.json": '{"dependencies": {"next": "16.4.6"}}\n',
             "apps/b/package.json": '{"devDependencies": {"next": "16.4.6"}}\n',
             "apps/c/package.json": '{"dependencies": {"react": "19.3.1"}}\n'}
    _, manifest = manifest_of(tmp_path, files)
    with open_snapshot(manifest) as store:
        asked = premap.nextjs.commands(premap.Context(manifest, store))
    assert [(c["cwd"], c["argv"][0]) for c in asked] == [("apps/a", "npx"), ("apps/a", "cat"),
                                                          ("apps/b", "npx"), ("apps/b", "cat")]


def test_the_commands_use_the_projects_own_next_without_network_and_the_setup_installs_no_package(tmp_path):
    import preparation
    from snapshot_store import open_snapshot
    project, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"next": "16.4.6"}}\n'})
    with open_snapshot(manifest) as store:
        asked = premap.nextjs.commands(premap.Context(manifest, store))
    # `npm_config_offline`: without `next` installed `npx --no-install` still asks the registry and fails after 70 seconds with a network
    # error (measured for `react-router` and `remix`, `benchmarks/react-router-routes/`); offline it fails at once, saying what is missing
    assert asked == [
        {"tool": "next", "argv": ["npx", "--no-install", "next", "typegen"], "cwd": ".",
         "env": {"NEXT_TELEMETRY_DISABLED": "1", "npm_config_offline": "true"}, "network": "none"},
        {"tool": "next", "argv": ["cat", ".next/types/validator.ts"], "cwd": ".", "env": {}, "network": "none"}]
    spec = container_runner.TOOLS["next"]
    assert spec["setup"] == [container_runner.UNPACK["node"]]  # Node only: `next` is the project's own
    assert (spec["restores"], spec["runs_on"]) == ("node", ("node",))
    calls, fake = recorder()
    with patch.object(container, "run_commands", fake):
        container_runner.runner(manifest)(asked)
    first, *rest = calls[0]["commands"]
    plan = preparation.node_prepare(["package.json"], lambda rel: (project / rel).read_text(encoding="utf-8"))
    assert f"( {plan['lines'][0]} )" in first["argv"][-1] and "install -g" not in first["argv"][-1]
    assert [c["network"] for c in rest] == ["none", "none"]


def test_in_an_analysis_the_source_has_a_preparation_that_takes_the_shared_restore_before_its_commands(tmp_path):
    import node_preparation
    from snapshot_store import open_snapshot
    _, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"next": "16.4.6"}}\n'})
    with open_snapshot(manifest) as store:
        asked = premap.nextjs.commands(premap.Context(manifest, store))
    calls, fake = recorder()
    with node_preparation.analysis(), patch.object(container, "run_commands", fake):  # as the pipeline runs it
        container_runner.runner(manifest)(asked)
    [call] = calls
    assert call["commands"][0]["network"] == "registries" and call["node_restore"]["script"]  # the restore runs there
    assert [c["network"] for c in call["commands"][1:]] == ["none", "none"]


def test_no_engine_carries_the_reason_and_never_runs_typegen_on_the_host(tmp_path):
    _, manifest = manifest_of(tmp_path, SHOP)
    _, run = recorder(state="gap")
    with patch.object(container, "run_commands", run):
        record = premap.write(manifest, sources=(premap.nextjs,), runner=container_runner.runner(manifest))
    [gap] = [g for g in record["gaps"] if g.get("source") == SOURCE]
    assert gap["kind"] == "model_not_run" and "no engine" in gap["detail"] and gap["remedy"] == "start one"
    assert "framework_entries" not in record


def test_the_source_is_registered_with_a_facet_that_joins_nothing():
    assert premap.nextjs in premap.SOURCES and premap.IDENTITY["framework_entries"] == ()


def test_a_premap_made_before_the_source_is_stale(tmp_path):
    _, manifest = manifest_of(tmp_path, SHOP)
    before = tuple(source for source in premap.SOURCES if source is not premap.nextjs)
    premap.write(manifest, sources=before)
    assert premap.state(manifest, sources=before)["state"] == "fresh"
    assert premap.state(manifest)["state"] == "stale"


def test_the_framework_entries_and_the_gaps_of_the_source_reach_the_flow_evidence(tmp_path):
    from premap.flow_entries import evidence
    files = {rel: text for rel, text in SHOP.items() if rel != "app/orders/[id]/page.tsx"}  # its import has no file
    _, manifest = manifest_of(tmp_path, files)
    premap.write(manifest, sources=(premap.nextjs,), runner=runner_for({".": done()})[1])
    rows, gaps = evidence(manifest)
    assert {(r["site"], r["path"]) for r in rows if r["reader"] == "next"} == {
        ("app/page.tsx", "/"), ("app/checkout/page.tsx", "/checkout"), ("app/api/pay/route.ts", "/api/pay"),
        ("app/layout.tsx", "/")}
    assert [(g["kind"], g["path"]) for g in gaps if g.get("source") == SOURCE] == [
        ("outside_snapshot", "app/orders/[id]/page.js")]


def test_a_premap_where_the_source_was_not_needed_gives_the_evidence_no_framework_entry_and_no_gap(tmp_path):
    from premap.flow_entries import evidence
    _, manifest = manifest_of(tmp_path, {"package.json": '{"dependencies": {"react": "19.3.1"}}\n'})
    premap.write(manifest, sources=(premap.nextjs,), runner=lambda commands: 1 / 0)
    rows, gaps = evidence(manifest)
    assert [r for r in rows if r["reader"] == "next"] == [] and [g for g in gaps if g.get("source") == SOURCE] == []


def test_a_classification_of_a_next_shape_is_a_valid_rule():
    import flows
    rule = {"link": "ingresso", "reader": "next", "shape": "ParallelSlotConfig", "entry": "rotta", "source": "modello"}
    assert flows.validate_rules([rule]) == [rule]


def test_the_source_file_of_the_next_reader_is_part_of_the_key_of_the_cached_links():
    import flows
    from pathlib import Path as Reader
    seen = []
    with patch.object(Reader, "read_bytes", autospec=True, side_effect=lambda self: seen.append(self.name) or b""):
        flows._links_reader_digest.__wrapped__()
    assert "nextjs.py" in seen



def test_each_row_carries_the_path_schema_as_rest_reads_it_and_the_page_mark_from_its_table(tmp_path):
    """`schema`: `[id]` is a parameter, a catch-all has none (None); `page` is the table's mark, on `AppPageConfig` alone."""
    record, _, _ = read(tmp_path, SHOP, {".": done()})
    by_file = {c["site"]: c for c in record["framework_entries"]}
    assert by_file["app/orders/[id]/page.tsx"]["schema"] == "/orders/{}" and by_file["app/checkout/page.tsx"]["schema"] == "/checkout"
    assert by_file["app/orders/[id]/page.tsx"]["page"] is True and "page" not in by_file["app/api/pay/route.ts"]
    assert "page" not in by_file["app/layout.tsx"]
    from premap import nextjs
    assert nextjs._next_path("/docs/[...slug]") is None and nextjs._next_path("/a/[[...x]]") is None
