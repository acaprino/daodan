"""Vue and Svelte templates in the snapshot: each expression the framework's template grammar gives, read in the
script's language, its calls, reads and handlers references of the template, and the names a template introduces
declared in their block.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_sfc_templates.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import snapshot  # noqa: E402
from languages import _treesitter, get_adapter  # noqa: E402

FIXTURES = HERE.parent / "benchmarks/project-model/fixtures"

VUE = """<script setup lang="ts">
const n = ref(0);
function inc(by: number) { n.value += by; }
function label(v: number) { return String(v); }
let saved = false;
</script>
<template>
  <button @click="inc" :title="label(n as number)">{{ n }}</button>
  <li v-for="(item, i) in items" :key="item.id" @click="inc(i)">{{ item.name }}</li>
  <Comp #row="{ row }" @save="saved = true">{{ row.x }}</Comp>
</template>
"""

SVELTE = """<script lang="ts">
  let { data } = $props();
  let count = $state(0);
  function select(id: string) {}
  function title(s: string) { return s; }
</script>

<h1 onclick={select} class:big={count > 2}>{title(data.heading)}</h1>
{#each data.items as item, i (item.id)}
  <p on:click={() => select(item.id)}>{i}: {item.name}</p>
{/each}
{#snippet row(entry)}<b>{entry}</b>{/snippet}
{@render row(count)}
<div class="a {title('x')} b"></div>
"""


def _semantic(tmp_path: Path, files: dict[str, str]) -> dict[str, dict]:
    for rel, text in files.items():
        (tmp_path / rel).write_text(text, encoding="utf-8")
    manifest = snapshot.build_manifest(tmp_path)
    return {rel: manifest["files"][rel]["semantic"] for rel in files}


def _at(source: str, line: int, text: str) -> tuple[int, int]:
    """The 1-based line and byte column of `text` on `line`."""
    row = source.split("\n")[line - 1]
    return line, len(row[:row.index(text)].encode("utf-8"))


def _bound(payload: dict, ref: dict) -> str | None:
    """What a reference's first name binds to, lexically: `kind name@line` of the one declaration or import of
    the nearest scope that has one, `ambiguous` for several, None when no scope binds it."""
    parents = {scope["id"]: scope.get("parent") for scope in payload["scopes"]}
    scope, name = ref["scope"], ref["parts"][0]
    while scope is not None:
        found = [f"{item['kind']} {name}@{item['span'][0]}" for item in payload["declarations"]
                 if item["scope"] == scope and item["name"] == name and item.get("lexical") is not False]
        found += [f"import {name}@{item['span'][0]}" for item in payload["imports"]
                  if item["scope"] == scope and item["local"] == name]
        if found:
            return found[0] if len(found) == 1 else "ambiguous"
        scope = parents[scope]
    return None


def _references(payload: dict, first_line: int) -> dict:
    """`{(line, column): (kind, parts, binding)}` of the references from `first_line` on."""
    return {tuple(ref["span"][:2]): (ref["kind"], ref["parts"], _bound(payload, ref))
            for ref in payload["references"] if ref["span"][0] >= first_line and ref["parts"]}


def test_a_vue_templates_calls_reads_and_handlers_are_references_bound_by_the_script_and_the_template(tmp_path):
    payload = _semantic(tmp_path, {"Button.vue": VUE})["Button.vue"]
    expected = {
        _at(VUE, 8, "inc"): ("call", ["inc"], "function inc@3"),  # a method handler: Vue calls it on the event
        _at(VUE, 8, "label"): ("call", ["label"], "function label@4"),
        _at(VUE, 8, "n as"): ("read", ["n"], "binding n@2"),  # TypeScript in a TypeScript component's template
        _at(VUE, 8, "n }}"): ("read", ["n"], "binding n@2"),
        _at(VUE, 9, "items"): ("read", ["items"], None),
        _at(VUE, 9, "item.id"): ("read", ["item", "id"], "binding item@9"),  # the alias, on its own element
        _at(VUE, 9, "inc(i)"): ("call", ["inc"], "function inc@3"),
        _at(VUE, 9, "i)\""): ("read", ["i"], "binding i@9"),
        _at(VUE, 9, "item.name"): ("read", ["item", "name"], "binding item@9"),
        _at(VUE, 10, "row.x"): ("read", ["row", "x"], "parameter row@10"),  # the slot's props, in its content
    }
    found = _references(payload, 8)
    assert {place: found.get(place) for place in expected} == expected
    # An inline handler's assignment writes the script's binding, as an assignment in the script does.
    [write] = [item for item in payload["declarations"] if tuple(item["span"][:2]) == _at(VUE, 10, "saved")]
    assert write["scope"] == "module"
    # The v-for alias is no name outside its element.
    assert not [ref for ref in payload["references"] if ref["parts"][:1] == ["item"] and ref["span"][0] != 9]


def test_a_svelte_templates_expressions_blocks_and_snippets_are_references_bound_by_the_script_and_the_template(
        tmp_path):
    payload = _semantic(tmp_path, {"Panel.svelte": SVELTE})["Panel.svelte"]
    expected = {
        _at(SVELTE, 8, "select"): ("call", ["select"], "function select@4"),  # an event attribute's handler
        _at(SVELTE, 8, "count"): ("read", ["count"], "binding count@3"),
        _at(SVELTE, 8, "title"): ("call", ["title"], "function title@5"),
        _at(SVELTE, 8, "data"): ("read", ["data", "heading"], "binding data@2"),
        _at(SVELTE, 9, "data"): ("read", ["data", "items"], "binding data@2"),  # the list, outside the block
        _at(SVELTE, 9, "item.id"): ("read", ["item", "id"], "binding item@9"),  # the key, inside it
        _at(SVELTE, 10, "select"): ("call", ["select"], "function select@4"),
        _at(SVELTE, 10, "item.id"): ("read", ["item", "id"], "binding item@9"),
        _at(SVELTE, 10, "i}"): ("read", ["i"], "binding i@9"),
        _at(SVELTE, 10, "item.name"): ("read", ["item", "name"], "binding item@9"),
        _at(SVELTE, 12, "entry}"): ("read", ["entry"], "parameter entry@12"),
        _at(SVELTE, 13, "row"): ("call", ["row"], "function row@12"),  # a snippet rendered is called
        _at(SVELTE, 13, "count"): ("read", ["count"], "binding count@3"),
        _at(SVELTE, 14, "title"): ("call", ["title"], "function title@5"),  # inside a quoted attribute value
    }
    found = _references(payload, 8)
    assert {place: found.get(place) for place in expected} == expected


def test_the_fixtures_templates_are_read(tmp_path):
    """js-vue-pnpm's Counter.vue and js-sveltekit's +page.svelte: their template calls and reads are sites."""
    vue = (FIXTURES / "js-vue-pnpm/src/components/Counter.vue").read_text(encoding="utf-8")
    page = (FIXTURES / "js-sveltekit/src/routes/+page.svelte").read_text(encoding="utf-8")
    found = _semantic(tmp_path, {"Counter.vue": vue, "page.svelte": page})
    line = vue.split("\n").index("  <button @click=\"n++\">{{ n }}</button>") + 1
    # `n++` writes the script's `n`: a second binding site, so its reads bind to no one (the analyzer answers them).
    assert _references(found["Counter.vue"], line)[_at(vue, line, "n }}")] == ("read", ["n"], "ambiguous")
    line = page.split("\n").index("<h1>{title(data.heading)}</h1>") + 1
    references = _references(found["page.svelte"], line)
    assert references[_at(page, line, "title")] == ("call", ["title"], "import title@2")
    assert references[_at(page, line, "data")] == ("read", ["data", "heading"], "binding data@3")


def test_a_template_its_grammar_cannot_read_is_said_and_the_script_is_still_read():
    real = _treesitter.get_parser

    def without_vue(language):
        return None if language == "vue" else real(language)

    with mock.patch.object(_treesitter, "get_parser", without_vue):
        result = get_adapter("vue").parse(VUE, "Button.vue")
    assert any(note.startswith("template not read: no vue grammar") for note in result.notes)
    assert result.semantic["references"] and max(ref["span"][0] for ref in result.semantic["references"]) < 6


def test_the_template_grammar_is_part_of_the_parser_profile():
    """A changed template grammar reads the component again, as a changed script grammar does."""
    from parser_identity import parser_profile
    for suffix, grammar in ((".vue", "vue"), (".svelte", "svelte")):
        profile = parser_profile(Path(f"a{suffix}"))
        assert profile["backend"] == "tree-sitter" and profile["template"]["grammar"] == grammar
        assert "abi_version" in profile["template"]
