"""Two runs of `modal_binding.py --mode after` side by side (T1.C.6, section «Difetti del legatore» of the README): the binder of a commit
(`DAODAN_CODE` a copy of it) and the one of the tree, on the same applications and the same Noir. For every HTTP row: bound in both with the
same symbol, with another symbol (split by how the first bound it: by the name at the line, the 1.631 of the first measure, or by position), bound
by one only (with the cause the other words); and for the rows bound by position to a function written with no name (`nameless`), the edges out
of their node and those whose site lies outside the lines of the function bound, in both runs. Writes `results/t1c6.json`.

    python -I benchmarks/noir-binding/compare_after.py <the folder of the earlier binder's answers> <the folder of the tree's answers>
"""
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apps  # noqa: E402


def rows(folder: pathlib.Path, name: str) -> dict | None:
    path = folder / f"{name}.after.json"
    answer = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"failed": "no answer"}  # btcpayserver: its snapshot takes more than an hour
    if answer.get("failed"):
        return None
    seen, out = collections.Counter(), {}
    for item in answer["facts"]:
        if item["shape"] != "http":
            continue
        key = (item["site"], item["method"], item["path"], item["handler"])
        seen[key] += 1
        out[(*key, seen[key])] = item  # Noir may give one key twice: told apart by their order
    return {"rows": out, "links": answer.get("links"), "links_failed": answer.get("links_failed")}


def nameless(item: dict) -> bool:
    return bool(item.get("ok") and item.get("by") == "position" and item.get("nameless"))


def main(before_folder: str, after_folder: str) -> None:
    totals = collections.Counter()
    applications, changed, lost, gained, edges = {}, [], [], [], []
    for name in apps.APPS:
        before, after = rows(pathlib.Path(before_folder), name), rows(pathlib.Path(after_folder), name)
        if before is None or after is None:
            applications[name] = {"failed": [side for side, got in (("before", before), ("after", after)) if got is None]}
            continue
        count = collections.Counter()
        for key, old in before["rows"].items():
            new = after["rows"].get(key)
            count["rows"] += 1
            count["bound_before"] += old["ok"]
            count["bound_by_name_before"] += old.get("by") == "name"
            if new is None:
                count["missing_after"] += 1
                continue
            count["bound_after"] += new["ok"]
            if old["ok"] and new["ok"]:
                if old["symbol"] != new["symbol"]:
                    count["symbol_changed_" + old["by"]] += 1
                    changed.append({"app": name, "key": list(key[:4]), "by": old["by"], "before": old["symbol"], "after": new["symbol"]})
            elif old["ok"]:
                count["lost_" + old["by"]] += 1
                lost.append({"app": name, "key": list(key[:4]), "by": old["by"], "symbol": old["symbol"], "gap": new.get("gap")})
            elif new["ok"]:
                count["gained"] += 1
                gained.append({"app": name, "key": list(key[:4]), "symbol": new["symbol"], "gap_before": old.get("gap")})
            if nameless(old) and nameless(new):
                count["nameless_in_both"] += 1
                row = {"app": name, "path": key[2], "method": key[1], "site": key[0], "symbol": new["symbol"], "lines": new["lines"],
                       "edges_before": old["edges_out"], "edges_after": new["edges_out"],
                       "outside_before": old["edges_outside_its_lines"], "outside_after": new["edges_outside_its_lines"]}
                count["edges_before"] += row["edges_before"]
                count["edges_after"] += row["edges_after"]
                count["outside_before"] += row["outside_before"]
                count["outside_after"] += row["outside_after"]
                if (row["edges_before"], row["outside_before"]) != (row["edges_after"], row["outside_after"]) or name in ("eshop", "go-admin"):
                    edges.append(row)
        count["links_failed"] = int(bool(after["links_failed"]))
        count["links_other_symbols"] = int(bool(after["links"]) and not after["links"]["same_symbols_as_the_binder_rows"])
        applications[name] = dict(count)
        totals.update(count)
    out = {"total": dict(totals), "applications": applications, "symbol_changed": changed, "lost": lost, "gained": gained,
           "nameless_edges": edges}
    (HERE / "results" / "t1c6.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out["total"], indent=1))
    print("changed", len(changed), "lost", len(lost), "gained", len(gained), "nameless rows with other edges or of eshop/go-admin", len(edges))


if __name__ == "__main__":
    main(*sys.argv[1:3])
