"""The pure part of `modal_ts_imports.py`: which tsconfig holds a file (the files tsc lists, the project tsserver opens it
in), the settings of a tsconfig as `import_resolution` reads them, the comparison of two resolutions (pairs, file edges,
module edges), the examples and the totals. Run on Modal: python tests/modal_pytest.py benchmarks/project-model/test_modal_ts_imports.py"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1] / "daodan/core")]

import modal_ts_imports as ts  # noqa: E402


def tsc(files_of, references=None, no_references=(), no_ancestors=()):
    return {"files_of": {config: set(files) for config, files in files_of.items()}, "references": references or {},
            "no_references": set(no_references), "no_ancestors": set(no_ancestors)}


# ---------------------------------------------------------------- which tsconfig holds a file

def test_a_config_is_a_tsconfig_or_jsconfig_json_outside_node_modules():
    assert ts.is_config("tsconfig.json") and ts.is_config("a/b/tsconfig.app.json") and ts.is_config("jsconfig.json")
    assert ts.is_config("x/jsconfig.dev.json")
    assert not ts.is_config("tsconfig.json.bak") and not ts.is_config("tsconfig-base.txt")
    assert not ts.is_config("node_modules/pkg/tsconfig.json") and not ts.is_config("a/mytsconfig.json")


def test_tsserver_tries_the_nearest_tsconfig_then_its_jsconfig_then_those_of_the_folders_above():
    configs = {"tsconfig.json", "src/tsconfig.json", "src/jsconfig.json", "other/tsconfig.json", "src/tsconfig.app.json"}
    assert ts.config_chain("src/a/b.ts", configs) == ["src/tsconfig.json", "src/jsconfig.json", "tsconfig.json"]
    assert ts.config_chain("main.ts", configs) == ["tsconfig.json"]
    assert ts.config_chain("src/a/b.ts", configs, no_ancestors={"src/tsconfig.json"}) == ["src/tsconfig.json"]
    assert ts.config_chain("lib/x.ts", {"src/tsconfig.json"}) == []


def test_a_file_a_solution_style_root_does_not_list_is_held_by_the_referenced_config_not_by_the_nearest_folder():
    # vite: the root tsconfig.json has `files: []` and references; the aliases are in tsconfig.app.json
    held = tsc({"tsconfig.json": [], "tsconfig.app.json": ["src/main.ts"], "tsconfig.node.json": ["vite.config.ts"]},
               {"tsconfig.json": ["tsconfig.app.json", "tsconfig.node.json"]})
    assert ts.owner_of("src/main.ts", held) == ts.Owner("tsconfig.app.json", "one", ["tsconfig.app.json"])
    assert ts.owner_of("vite.config.ts", held).config == "tsconfig.node.json"


def test_a_file_held_by_several_configs_goes_to_the_nearest_tsconfig_json_that_tsserver_finds_first():
    held = tsc({"tsconfig.json": ["src/a.ts"], "tsconfig.build.json": ["src/a.ts"]})
    owner = ts.owner_of("src/a.ts", held)
    assert (owner.config, owner.how, owner.held) == ("tsconfig.json", "many", ["tsconfig.build.json", "tsconfig.json"])


def test_a_nearer_config_that_leaves_the_file_out_hands_it_to_the_one_above():
    held = tsc({"src/tsconfig.json": ["src/b.ts"], "tsconfig.json": ["src/a.ts"]})
    assert ts.owner_of("src/a.ts", held) == ts.Owner("tsconfig.json", "one", ["tsconfig.json"])


def test_the_references_of_a_config_are_tried_in_order_before_the_references_of_its_references():
    held = tsc({"tsconfig.json": [], "a/tsconfig.json": [], "b/tsconfig.json": ["x.ts"], "c/tsconfig.json": ["x.ts"]},
               {"tsconfig.json": ["a/tsconfig.json", "b/tsconfig.json"], "a/tsconfig.json": ["c/tsconfig.json"]})
    owner = ts.owner_of("x.ts", held)
    assert (owner.config, owner.how) == ("b/tsconfig.json", "many")  # a direct reference before one a reference holds


def test_references_are_not_followed_when_the_config_disables_them():
    held = tsc({"tsconfig.json": [], "app.json": ["x.ts"]}, {"tsconfig.json": ["app.json"]}, no_references={"tsconfig.json"})
    owner = ts.owner_of("x.ts", held)
    assert (owner.config, owner.how) == ("app.json", "one")  # held by one config: that one, tsserver or not


def test_a_file_several_configs_hold_that_no_tsserver_walk_reaches_is_ambiguous_and_goes_to_the_deepest_then_first_by_name():
    held = tsc({"web/tsconfig.spec.json": ["web/a.ts"], "web/tsconfig.app.json": ["web/a.ts"], "tsconfig.base.json": ["web/a.ts"]})
    owner = ts.owner_of("web/a.ts", held)
    assert (owner.config, owner.how) == ("web/tsconfig.app.json", "unreached")
    assert owner.held == ["tsconfig.base.json", "web/tsconfig.app.json", "web/tsconfig.spec.json"]


def test_a_file_no_config_lists_has_no_owner():
    assert ts.owner_of("a.ts", tsc({"tsconfig.json": ["b.ts"]})) == ts.Owner(None, "none", [])


# ---------------------------------------------------------------- the settings of a config

def test_paths_are_resolved_against_the_base_url_or_else_against_the_folder_that_declares_them():
    inherited = {"paths": {"ui-kit": ["./dist/ui-kit"], "@/*": ["src/*"]}, "baseUrl": None, "pathsBasePath": "/p"}
    assert ts.settings_of(inherited) == {"paths": {"ui-kit": ["/p/dist/ui-kit"], "@/*": ["/p/src/*"]}}
    based = {"paths": {"@/*": ["./src/*"]}, "baseUrl": "/p/app", "pathsBasePath": "/p"}
    assert ts.settings_of(based) == {"baseUrl": "/p/app", "paths": {"@/*": ["/p/app/src/*"]}}
    assert ts.settings_of({"baseUrl": "/p/src", "paths": None, "pathsBasePath": None}) == {"baseUrl": "/p/src"}
    assert ts.settings_of({"baseUrl": None, "paths": None, "pathsBasePath": None}) == {}


def test_a_target_that_is_not_a_string_is_left_out():
    assert ts.settings_of({"paths": {"a": ["x", 3]}, "baseUrl": None, "pathsBasePath": "/p"}) == {"paths": {"a": ["/p/x"]}}


# ---------------------------------------------------------------- the comparison

A = {"a.ts": {"./x": ["x.ts"], "@/y": [], "react": [], "./gone": ["gone.ts"], "./old": ["old.ts"]},
     "b.ts": {"@/y": []}}
B = {"a.ts": {"./x": ["x.ts"], "@/y": ["src/y.ts"], "react": [], "./gone": [], "./old": ["new.ts"]},
     "b.ts": {"@/y": ["src/y.ts"]}}


def test_each_pair_of_importer_and_specifier_is_the_same_unresolved_gained_lost_or_changed():
    found = ts.classify_pairs(A, B)
    assert found["counts"] == {"same": 1, "unresolved": 1, "gained": 2, "lost": 1, "changed": 1}
    assert found["pairs"]["gained"] == [("a.ts", "@/y", [], ["src/y.ts"]), ("b.ts", "@/y", [], ["src/y.ts"])]
    assert found["pairs"]["lost"] == [("a.ts", "./gone", ["gone.ts"], [])]
    assert found["pairs"]["changed"] == [("a.ts", "./old", ["old.ts"], ["new.ts"])]


def test_the_comparison_leaves_out_the_importers_outside_the_scope():
    found = ts.classify_pairs(A, B, scope={"b.ts"})
    assert found["counts"] == {"same": 0, "unresolved": 0, "gained": 1, "lost": 0, "changed": 0}


def test_file_edges_are_the_distinct_importer_target_pairs_and_their_changes_are_counted_both_ways():
    before, after = ts.file_edges(A), ts.file_edges(B)
    assert before == {("a.ts", "x.ts"), ("a.ts", "gone.ts"), ("a.ts", "old.ts")}
    assert ts.edge_changes(before, after) == {"before": 3, "after": 4, "gained": 3, "lost": 2}


def test_module_edges_join_the_owners_of_the_two_files_and_leave_out_a_module_to_itself():
    owners = {"a.ts": ["m1"], "x.ts": ["m1"], "src/y.ts": ["m2", "m3"], "new.ts": ["m2"], "b.ts": ["m3"]}
    edges = ts.module_edges({("a.ts", "x.ts"), ("a.ts", "src/y.ts"), ("a.ts", "new.ts"), ("b.ts", "src/y.ts"),
                             ("a.ts", "nobody.ts")}, owners)
    assert edges == {("m1", "m2"), ("m1", "m3"), ("m3", "m2")}  # m1 -> m1 and m3 -> m3 are left out, nobody.ts has no owner


def test_at_most_five_examples_alternate_lost_changed_and_gained_in_the_order_of_their_paths():
    found = {"gained": [(f"g{i}.ts", "s", [], ["t.ts"]) for i in range(4)], "lost": [("l.ts", "s", ["t.ts"], [])],
             "changed": [("c0.ts", "s", ["a.ts"], ["b.ts"]), ("c1.ts", "s", ["a.ts"], ["b.ts"])]}
    shown = ts.examples(found, {("g0.ts", "s"): "paths"})
    assert [(e["kind"], e["importer"]) for e in shown] == [("lost", "l.ts"), ("changed", "c0.ts"), ("gained", "g0.ts"),
                                                           ("changed", "c1.ts"), ("gained", "g1.ts")]
    assert shown[2] == {"kind": "gained", "importer": "g0.ts", "specifier": "s", "before": [], "after": ["t.ts"],
                        "via": "paths"}


def test_examples_say_which_config_an_importer_has_and_which_ones_list_it_when_the_owners_are_given():
    found = {"gained": [], "lost": [("l.ts", "s", ["t.ts"], [])], "changed": []}
    owners = {"l.ts": ts.Owner("tsconfig.json", "many", ["tsconfig.build.json", "tsconfig.json"])}
    assert ts.examples(found, owners=owners)[0]["config"] == "tsconfig.json"
    assert ts.examples(found, owners=owners)[0]["held"] == ["tsconfig.build.json", "tsconfig.json"]


def test_the_resolution_that_hits_first_names_where_a_gained_pair_came_from():
    class Resolver:
        root, config = Path("/p"), {"packages": {}}

        def keeps(self, hit, importer):
            return bool(hit) and hit != importer

        def lookup(self, candidate, importer):
            return {"/p/src/y": "src/y.ts", "/p/lib/z": "lib/z.ts"}.get(candidate)

    resolver = Resolver()
    both = {"baseUrl": "/p", "paths": {"@/*": ["/p/src/*"]}}
    assert ts.hit_kind(resolver, "a.ts", "@/y", both) == "paths"
    assert ts.hit_kind(resolver, "a.ts", "lib/z", both) == "baseUrl"
    assert ts.hit_kind(resolver, "a.ts", "./q", both) == "relative"
    assert ts.hit_kind(resolver, "a.ts", "nope", both) is None


# ---------------------------------------------------------------- the totals

def test_totals_add_up_the_projects_that_ran_and_list_the_ones_that_failed():
    one = {"pairs": {"same": 5, "gained": 2, "lost": 0}, "edges": {"files": {"gained": 2}}, "gained_by": {"paths": 1, "baseUrl": 1}}
    two = {"pairs": {"same": 1, "gained": 1, "lost": 3}, "edges": {"files": {"gained": 1}}, "gained_by": {"paths": 1}}
    found = ts.totals({"p1": one, "p2": two, "p3": {"error": "no archive"}})
    assert found["projects"] == 2 and found["failed"] == {"p3": "no archive"}
    assert found["pairs"] == {"same": 6, "gained": 3, "lost": 3}
    assert found["edges"] == {"files": {"gained": 3}}
    assert found["gained_by"] == {"paths": 2, "baseUrl": 1}
