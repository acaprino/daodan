"""The preparation's dependency restores: each package manager's own command, run in Daodan's container.

The answers are in `tests/fixtures/premap/restore/<manager>.json`, recorded once in a real container from the
projects beside them (`tests/fixtures/premap/restore/<manager>/`): `good` restores, `bad` names a package no
registry has.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

import preparation  # noqa: E402

ANSWERS = Path(__file__).with_name("fixtures") / "premap" / "restore"


def recorded(manager):
    stored = json.loads((ANSWERS / f"{manager}.json").read_text(encoding="utf-8"))
    assert stored["line"] == preparation.restore(manager, ["good", "bad"]), "the recorded line is not the current one"
    return stored["result"]


def test_gradle_resolves_every_configuration_and_a_package_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("gradle")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "gradle", "bad")]
    assert "org.example.missing:nothing:9.9.9" in gaps[0]["detail"]


def test_maven_goes_offline_and_a_package_no_registry_has_is_a_gap():
    gaps = preparation.restore_gaps(recorded("maven")["stderr"])
    assert [(g["kind"], g["manager"], g["path"]) for g in gaps] == [("restore_failed", "maven", "bad")]
    assert "org.example.missing:nothing" in gaps[0]["detail"]


def test_a_restore_runs_where_the_build_starts_and_its_hosts_are_declared_once():
    files = ["settings.gradle", "app/build.gradle", "lib/build.gradle", "tools/x/build.gradle.kts", "pom.xml",
             "core/pom.xml", "other/pom.xml"]
    assert preparation.restores(files) == {"gradle": ["."], "maven": ["."]}
    assert preparation.restores(["a/pom.xml", "b/pom.xml", "b/c/pom.xml"]) == {"maven": ["a", "b"]}
    assert set(preparation.RESTORES["gradle"]["hosts"]) >= {"plugins.gradle.org", "services.gradle.org"}


def test_every_restore_line_reports_its_failure_and_the_run_goes_on():
    for manager in preparation.RESTORES:
        line = preparation.restore(manager, ["x"])
        assert "DAODAN-RESTORE-FAILED" in line and line.endswith("true"), manager
