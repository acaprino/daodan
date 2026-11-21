"""Specfy with Daodan's curated package/file rules, scored like the bare Specfy adapter.

`detail.ids` includes every detected technology. Both adapters use Specfy's historical service
facet: e.g. it includes storage, while network gateways and generic SaaS appear only in `detail`.
Specfy 1.27.6 splits Compose image references at the first colon before handing them to rules,
so a registry with an explicit port needs Daodan's manifest reader to retain the full image path.
"""
from __future__ import annotations

import json
from pathlib import Path

import _fw
from daodan_registry import SCRIPTS
from specfy_stack_analyser import PACKAGE, VERSION, catalogue, normalise


def run(fixture_dir, work_dir) -> dict:
    work = Path(work_dir).resolve()
    work.mkdir(parents=True, exist_ok=True)
    output, rule_catalogue = work / "out.json", work / "catalogue.json"
    code, _, err = _fw.execute(
        ["node", SCRIPTS / "specfy_rules.mjs", PACKAGE, Path(fixture_dir).resolve(), output, rule_catalogue], work)
    if code:
        raise RuntimeError(f"Specfy with Daodan rules exited {code}: {err[-400:]}")
    known = catalogue() | json.loads(rule_catalogue.read_text(encoding="utf-8"))
    return normalise(json.loads(output.read_text(encoding="utf-8")), known)
