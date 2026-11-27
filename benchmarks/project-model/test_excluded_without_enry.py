"""Che cosa cambia in `excluded` senza go-enry, dai dati di Linguist (T1.B.2).

Per ogni fixture con un `output` in tutti e due, le voci `{path, why}` di `fixtures.*.output.excluded` di
`results/enry.json` (go-enry v2.9.6) contro quelle di `results/linguist_data.json` (i dati del gem 9.7.0: `vendor.yml`,
`documentation.yml`, `.gitattributes`): per motivo, uguali, mancanti (solo go-enry) e in più (solo i dati). Le cifre vengono
dalla traduzione `rx` di `tools/linguist_data.py`, un lettore scritto a mano usato solo come misura; la cifra vera è quella
di `run=corpus` in `T1.B.6`. I `generated` mancanti si dividono in lockfile e codice generato: `LOCKFILES` sono i nomi che
`lib/linguist/generated.rb` di Linguist 9.7.0 riconosce come lockfile (`cargo_lock?`, `npm_shrinkwrap_or_package_lock?`,
`pnpm_lock?`, `uv_lock?`, `poetry_lock?`, `pdm_lock?`, `pipenv_lock?`, `terraform_lock?`, `composer_lock?`, `go_lock?`,
`deno_lock?`, `flake_lock?`, `bazel_lock?`), trascritti: `generated.rb` è codice Ruby, non un dato da leggere.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath, Path

RESULTS = Path(__file__).parent / "results"
LOCKFILES = frozenset({"Cargo.lock", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "uv.lock",
                       "poetry.lock", "pdm.lock", "Pipfile.lock", ".terraform.lock.hcl", "composer.lock", "Gopkg.lock",
                       "glide.lock", "deno.lock", "flake.lock", "MODULE.bazel.lock"})


def _excluded(name: str) -> dict[str, set[tuple[str, str]]]:
    fixtures = json.loads((RESULTS / name).read_text(encoding="utf-8"))["fixtures"]
    return {fixture: {(item["path"], item["why"]) for item in record["output"].get("excluded") or ()}
            for fixture, record in fixtures.items() if "output" in record}


def compare(enry: dict, linguist: dict) -> tuple[dict[str, dict[str, int]], list[tuple[str, str]]]:
    """Per motivo, `{same, missing, extra}` sulle fixture in comune, e le voci `generated` che solo go-enry dà."""
    counts, generated = {}, []
    for fixture in sorted(set(enry) & set(linguist)):
        a, b = enry[fixture], linguist[fixture]
        for key, items in (("same", a & b), ("missing", a - b), ("extra", b - a)):
            for path, why in items:
                line = counts.setdefault(why, {"same": 0, "missing": 0, "extra": 0})
                line[key] += 1
                if key == "missing" and why == "generated":
                    generated.append((fixture, path))
    return counts, sorted(generated)


def test_compare_counts_each_reason_and_keeps_the_generated_only_go_enry_gives():
    counts, generated = compare({"a": {("x.png", "binary"), ("v/", "vendored")}, "b": {("Cargo.lock", "generated")}},
                                {"a": {("v/", "vendored"), ("docs/", "documentation")}, "b": set(), "c": {("y", "vendored")}})
    assert counts == {"binary": {"same": 0, "missing": 1, "extra": 0}, "vendored": {"same": 1, "missing": 0, "extra": 0},
                      "documentation": {"same": 0, "missing": 0, "extra": 1},
                      "generated": {"same": 0, "missing": 1, "extra": 0}}
    assert generated == [("b", "Cargo.lock")]


def test_excluded_without_go_enry_on_the_corpus():
    enry, linguist = _excluded("enry.json"), _excluded("linguist_data.json")
    assert len(set(enry) & set(linguist)) == 124
    counts, generated = compare(enry, linguist)
    assert counts == {"vendored": {"same": 393, "missing": 1, "extra": 1},
                      "documentation": {"same": 540, "missing": 1, "extra": 25},
                      "generated": {"same": 3, "missing": 146, "extra": 2},
                      "binary": {"same": 0, "missing": 554, "extra": 0}}
    locks = [(fixture, path) for fixture, path in generated if PurePosixPath(path).name in LOCKFILES]
    assert (len(locks), len({fixture for fixture, _ in locks})) == (40, 27)
    assert len(generated) - len(locks) == 106
