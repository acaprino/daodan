"""The results the benchmark leaves in `results/` hold together: the hand annotations fit the measured records and are the
seeded sample the README says, `summary.json` is what the scorer writes from them, and the README's tables are the ones
`header_tables.py` writes from `summary.json` and `loc.json`. Standard library only."""
import ast
import json
from pathlib import Path

import pytest

import header_patterns as patterns
import header_report as report
import header_tables as tables

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
needs_results = pytest.mark.skipif(not (RESULTS / "headers.json.gz").exists(), reason="the measured headers are not here")


@pytest.fixture(scope="module")
def records():
    return [r for r in report.load(RESULTS / "headers.json.gz")["records"] if "error" not in r]


@pytest.fixture(scope="module")
def annotations():
    return json.loads((HERE / "labels.json").read_text(encoding="utf-8"))


@needs_results
def test_every_annotation_fits_the_record_and_the_pool_it_was_made_in(records, annotations):
    strata = report.flat_strata(report.pools(records))
    assert report.audit_labels(records, annotations, strata) == []


@needs_results
def test_the_annotated_headers_are_the_seeded_sample_the_readme_names(records, annotations):
    pool = report.pools(records)
    chosen = set()
    for label, total in zip(("cpp", "c", "objc"), (90, 30, 25)):
        strata = {name: [report.key(r) for r in rows] for name, rows in pool[label].items() if rows}
        chosen |= set(report.annotation_sample(strata, total, seed=f"annotate-{label}"))
    assert chosen == set(annotations)


@needs_results
def test_every_label_is_a_known_category_and_says_why(annotations):
    for key, note in annotations.items():
        assert note["label"] in report.CATEGORIES and note["why"].strip(), key


@needs_results
def test_the_variant_runs_read_the_same_headers_and_today_s_rule_answers_the_same_as_in_the_first_run(records):
    """`r0check` and `capcost` ran at a later commit than `headers.json.gz`: the same files, the same answer of today's rule."""
    first = {report.key(r): r for r in records}
    for name, field in (("r0check", "r0"), ("capcost", None)):
        path = RESULTS / f"{name}.json.gz"
        if not path.exists():
            continue
        rows = report.load(path)["rows"]
        assert {report.key(r) for r in rows} == set(first), name
        for row in rows:
            assert row["size"] == first[report.key(row)]["size"], (name, report.key(row))
            if field:
                assert row[field] == first[report.key(row)]["r0"], (name, report.key(row))


@needs_results
def test_summary_is_what_the_scorer_writes_from_the_results():
    written = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(report.build(RESULTS, HERE / "labels.json"))) == written


@needs_results
def test_readme_tables_are_the_ones_the_results_write():
    summary = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    loc = json.loads((RESULTS / "loc.json").read_text(encoding="utf-8"))
    text = (HERE / "README.md").read_text(encoding="utf-8")
    assert tables.render(text, tables.tables(summary, loc)) == text
    assert sorted(m.group(2) for m in tables.BLOCK.finditer(text)) == sorted(tables.TABLES)  # every table is in the README, once


def test_readme_gives_the_two_final_patterns_exactly_as_the_code_has_them():
    text = (HERE / "README.md").read_text(encoding="utf-8")
    assert patterns.NOISE_FIXQ in text and patterns.CPP_FIXQC in text


HEADER = HERE.parents[1] / "daodan" / "core" / "languages" / "detect" / "__init__.py"


def _shipped_bound() -> int:
    """The `MAX_CHARS` of the product, read from its syntax tree."""
    tree = ast.parse(HEADER.read_text(encoding="utf-8"))
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and n.targets[0].id == "MAX_CHARS")


@needs_results
def test_the_product_file_is_what_the_scorer_writes_and_with_no_bound_the_product_answers_as_route_r3dx():
    notes = json.loads((HERE / "labels.json").read_text(encoding="utf-8"))
    scored = report.product(report.load(RESULTS / "headers.json.gz"), report.load(RESULTS / "product.json.gz"), notes)
    written = json.loads((RESULTS / "product.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(scored)) == written
    assert written["0"]["differences"] == [] and written[str(_shipped_bound())]["differences"] == []  # the bound of the product reaches no header


@needs_results
def test_the_readme_gives_the_numbers_of_the_bound_the_product_ships():
    written = json.loads((RESULTS / "product.json").read_text(encoding="utf-8"))
    text = (HERE / "README.md").read_text(encoding="utf-8")
    for bound, label in (("0", "nessuno"), (str(_shipped_bound()), f"**{_shipped_bound():,} (prodotto)**")):
        found, accuracy, cost = written[bound], written[bound]["accuracy"], written[bound]["cost_ms"]
        row = (f"| {label} | {len(found['differences'])} | {found['lost']:,} | {accuracy['c'][0]} / {accuracy['cpp'][0]} | "
               f"{cost['median']:.2f} / {cost['p95']:.1f} / {cost['max']:,.0f} | {cost['total_s']:.1f} |")
        assert row in text, row
