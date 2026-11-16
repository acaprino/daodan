"""The pre-map's `tsc` source: an alias a tsconfig inherits is resolved where it is written.

TypeScript resolves `paths` against the folder of the tsconfig that writes them, and `tsc --showConfig` prints
them as written, whatever file they come from: the answers here are what tsc prints for these files.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/codebase-map/skills/map/scripts"))

from premap import tsc  # noqa: E402


def context(files: dict) -> SimpleNamespace:
    texts = {rel: text if isinstance(text, str) else json.dumps(text) for rel, text in files.items()}
    return SimpleNamespace(inventory=SimpleNamespace(files=sorted(texts), headers=dict.fromkeys(texts, {}),
                                                     text=texts.__getitem__))


def stated(files: dict, shown: dict) -> dict:
    """The aliases each unit gets, by its folder, when tsc shows `shown` for the tsconfigs of `files`."""
    given = context(files)
    commands = tsc.commands(given)
    results = [{"returncode": 0, "stderr": "", "stdout": json.dumps(
        shown[tsc._join(command["cwd"], command["argv"][-1])])} for command in commands]
    read = tsc.read(given, commands, results)
    assert not read["gaps"], read["gaps"]
    return {unit["root"]: unit["config"].get("paths") for unit in read["facts"]["units"]}


def test_an_alias_a_generated_tsconfig_writes_is_resolved_from_that_file():
    """SvelteKit: the root tsconfig extends `.svelte-kit/tsconfig.json`, which the install generates and the
    snapshot does not hold; its `$lib` is `../src/lib` from there."""
    files = {"package.json": {"name": "notes"},
             "tsconfig.json": {"extends": "./.svelte-kit/tsconfig.json", "compilerOptions": {"strict": True}}}
    shown = {"tsconfig.json": {"compilerOptions": {"strict": True, "paths": {
        "$lib": ["../src/lib"], "$lib/*": ["../src/lib/*"]}}}}
    assert stated(files, shown) == {".": {"$lib": ["src/lib"], "$lib/*": ["src/lib/*"]}}


def test_an_alias_a_base_tsconfig_writes_is_resolved_from_the_base_through_the_chain():
    files = {"package.json": {"name": "root"}, "packages/web/package.json": {"name": "web"},
             "tsconfig.base.json": '{\n  // shared\n  "compilerOptions": {"paths": {"@acme/*": ["packages/*/src"]}}\n}',
             "packages/tsconfig.shared.json": {"extends": "../tsconfig.base"},
             "packages/web/tsconfig.json": {"extends": "../tsconfig.shared.json", "include": ["src"]}}
    inherited = {"compilerOptions": {"paths": {"@acme/*": ["packages/*/src"]}}}
    shown = {"tsconfig.base.json": inherited, "packages/tsconfig.shared.json": inherited,
             "packages/web/tsconfig.json": inherited}
    assert stated(files, shown) == {".": {"@acme/*": ["packages/*/src"]},
                                    "packages/web": {"@acme/*": ["packages/*/src"]}}


def test_an_alias_a_tsconfig_writes_itself_or_under_a_base_url_stays_where_it_was():
    files = {"web/package.json": {"name": "web"},
             "web/tsconfig.json": {"extends": "../base.json", "compilerOptions": {"paths": {"@/*": ["./src/*"]}}},
             "api/package.json": {"name": "api"},
             "api/tsconfig.json": {"extends": "@tsconfig/node20/tsconfig.json"}}
    shown = {"web/tsconfig.json": {"compilerOptions": {"paths": {"@/*": ["./src/*"]}}},
             "api/tsconfig.json": {"compilerOptions": {"baseUrl": "./lib", "paths": {"~/*": ["*"]}}}}
    assert stated(files, shown) == {"web": {"@/*": ["web/src/*"]}, "api": {"~/*": ["api/lib/*"]}}
