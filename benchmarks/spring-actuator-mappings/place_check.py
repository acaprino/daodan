"""From a route to its handler's file and line, with what the probe recorded and Daodan's own parser: the check of the design,
not a source of the pre-map. Runs on this machine over text only (the JSON of Actuator's `mappings`, the report of `javap`, the
fixture's `.java` files): no code of the fixture runs here.

    python -I benchmarks/spring-actuator-mappings/place_check.py          (after `modal_probe.py`; writes results/place-check.json)

What it does, from `daodan/core/dynamic/jvm.py` `place` (a class file's `SourceFile`, the first line of a method, the declaration of
the snapshot's parse that has the method's name and holds that line):
1. Actuator names the handler as class (canonical name: `demo.Inherited.Base`), method name and descriptor.
2. `javap -l -p -s` names, per class file, its binary name, `SourceFile`, and per method its descriptor and the first line of its
   `LineNumberTable`. The binary name with `$` as `.` is Actuator's canonical name: no guess about where a nested class begins.
3. The snapshot's java parse (`languages.get_adapter("java").parse`, tree-sitter) has the declarations of the file named by the
   package and `SourceFile`; the handler is the `function` whose `qualified_name` is the class (without its package) and the method
   name, and whose span holds the line: two overloads are told apart by their spans, with no reading of types.

The one reading that is not a parser's is the text of `javap`'s report (lines such as `line 26: 0`): a tool's report with no grammar
to give a parser, matched line by line. Evaluated and not used here: a structured reader of the class file (ASM, which Daodan already
pins for `dynamic/jvm_record`), which needs a helper compiled in the container.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "daodan" / "core"))
import languages  # noqa: E402

SOURCES = HERE / "fixture" / "src" / "main" / "java"
KINDS = ("class", "interface", "enum", "record")


def javap_classes(text: str) -> dict[str, dict]:
    """`javap -l -p -s`'s report: binary class name -> {source, methods: {(name, descriptor): first line}}."""
    classes, current, method = {}, None, None
    source = None
    for line in text.splitlines():
        found = re.fullmatch(r'Compiled from "(.+)"', line)
        if found:
            source = found.group(1)
            continue
        if not line.startswith(" ") and line.rstrip().endswith("{"):
            words = line.rstrip(" {").split()
            kind = next(at for at, word in enumerate(words) if word in KINDS)
            name = words[kind + 1].split("<")[0]
            current = classes[name] = {"source": source, "methods": {}}
            continue
        if current is None:
            continue
        found = re.fullmatch(r"  ([^ ].*);", line)  # the line of a member: a method, a constructor, `static {}` or a field
        if found:
            member = found.group(1)
            method = {"name": member.split("(")[0].split()[-1] if "(" in member else member, "descriptor": None, "first_line": None}
            continue
        found = re.fullmatch(r"    descriptor: (.+)", line)
        if found and method:
            method["descriptor"] = found.group(1)
            current["methods"][(method["name"], method["descriptor"])] = method
            continue
        found = re.fullmatch(r"      line (\d+): \d+", line)
        if found and method and method["first_line"] is None:
            method["first_line"] = int(found.group(1))
    return classes


def declarations(text: str, rel: str) -> list[dict]:
    """The declarations of the snapshot's java parse of a file: what `dynamic/jvm.py` `place` reads."""
    return languages.get_adapter("java").parse(text, rel).semantic["declarations"]


def place(row: dict, classes: dict[str, dict], source) -> dict:
    """The handler of one Actuator row: its file and line, or the gap and its cause. `source(rel)` gives the files of the
    project whose path ends with `rel` (a package folder and a `SourceFile`) as a list of `(path in the project, declarations)`."""
    class_name, name, descriptor = row["class"], row["name"], row["descriptor"]
    binary = next((binary for binary in classes if binary.replace("$", ".") == class_name), None)
    if binary is None:
        return {"gap": "the class is not in the project's classes"}
    record = classes[binary]["methods"].get((name, descriptor))
    if record is None or record["first_line"] is None:
        return {"gap": "no line in the class file for that method"}
    package, _, _ = binary.rpartition(".")
    rel = f"{package.replace('.', '/')}/{classes[binary]['source']}"
    files = source(rel)
    if not files:
        return {"gap": "no source file in the snapshot"}
    if len(files) > 1:
        return {"gap": f"{len(files)} files of the snapshot are {rel}"}
    [(path, found)] = files
    wanted = class_name[len(package) + 1:] + "." + name
    spans = [item for item in found if item["kind"] == "function" and item["qualified_name"] == wanted
             and item["span"][0] <= record["first_line"] <= item["span"][2]]
    if len(spans) != 1:
        return {"gap": f"{len(spans)} declarations of {wanted} hold line {record['first_line']}"}
    declaration = spans[0]
    return {"file": path, "line": declaration["name_span"][0], "span": [declaration["span"][0], declaration["span"][2]],
            "first_line_in_class_file": record["first_line"]}


def main() -> None:
    results = HERE / "results"
    classes = javap_classes((results / "javap.txt").read_text(encoding="utf-8"))
    mappings = json.loads(json.loads((results / "actuator-boot3.json").read_text(encoding="utf-8"))[0]["written"])
    parsed = {}

    def source(rel: str) -> list:
        path = SOURCES / rel
        if rel not in parsed:
            parsed[rel] = declarations(path.read_text(encoding="utf-8"), rel) if path.is_file() else None
        return [(rel, parsed[rel])] if parsed[rel] is not None else []

    rows = []
    for entry in mappings["contexts"]["application"]["mappings"]["dispatcherServlets"]["dispatcherServlet"]:
        details = entry["details"] or {}
        handler, conditions = details.get("handlerMethod"), details.get("requestMappingConditions")
        if not handler:
            rows.append({"predicate": entry["predicate"], "handler": entry["handler"][:80], "gap": "no handler method (a function or a resource handler)"})
            continue
        row = {"class": handler["className"], "name": handler["name"], "descriptor": handler["descriptor"]}
        for method in conditions["methods"] or ["ANY"]:
            for path in conditions["patterns"]:
                rows.append({"method": method, "path": path, **row, **place(row, classes, source)})
    rows.sort(key=lambda row: (row.get("path", ""), row.get("method", ""), row.get("name", "")))
    placed = [row for row in rows if "file" in row]
    summary = {"rows": len(rows), "placed": len(placed), "gaps": sorted({row["gap"] for row in rows if "gap" in row})}
    (results / "place-check.json").write_bytes((json.dumps({"summary": summary, "rows": rows}, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    for row in rows:
        print(row.get("method", "-").ljust(7), row.get("path", row.get("predicate", ""))[:34].ljust(34),
              f"{row['file']}:{row['line']} (span {row['span'][0]}-{row['span'][1]}, first line {row['first_line_in_class_file']})"
              if "file" in row else f"GAP {row['gap']}")
    print(summary)


if __name__ == "__main__":
    main()
