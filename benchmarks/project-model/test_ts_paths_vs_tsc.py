"""The committed comparison of Daodan's TypeScript path reader with tsc must equal a fresh run."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))

import ts_paths_vs_tsc as compare  # noqa: E402


def test_committed_result_equals_a_fresh_run():
    assert json.loads(compare.RESULT.read_text()) == compare.compare()


def test_no_pattern_differs_from_tsc():
    assert compare.compare()["counts"]["different"] == 0


def test_angular_units_are_same():
    # `paths` is declared in the root tsconfig and inherited by projects/ui-kit: tsc resolves it against the file that
    # declares it, so both units give dist/ui-kit, in tsc and in Daodan.
    units = compare.compare()["fixtures"]["js-angular"]["units"]
    for root in (".", "projects/ui-kit"):
        assert units[root]["ui-kit"] == {"class": "same", "tsc": ["dist/ui-kit"], "daodan": ["dist/ui-kit"]}
