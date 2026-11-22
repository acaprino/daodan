# The current reader (languages/stylesheet.py parse_sheet, dialect css) behind the same shape. It reads only the strings of inputs.json.
# usage: python -B norm_current.py   (env OUT; the reader's files are in lang/languages/: modal_candidates.py puts them there)
import json
import os
import sys
from pathlib import Path

os.environ["DAODAN_CONTAINER"] = "off"
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OUT", HERE / "out"))
sys.path.insert(0, os.environ.get("CURRENT_LANG", str(HERE / "lang")))
from languages import stylesheet  # noqa: E402

inputs = json.load(open(HERE / "inputs.json", encoding="utf-8"))
items = []
for inp in inputs:
    out = {"id": inp["id"], "threw": None, "errors": 0, "rules": [], "decls": [], "atrules": [], "comments": []}
    try:
        # snapshot._text turns CRLF and CR into LF before any parser reads the text
        sheet = stylesheet.parse_sheet(inp["src"].replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10)), "css")

        def walk(nodes):
            for n in nodes:
                if n.kind in ("rule", "keyframe"):
                    out["rules"].append({"sel": None, "line": n.line, "col": None, "endLine": n.end_line})
                for d in n.declarations:
                    out["decls"].append({"property": d.property, "value": [d.value], "important": d.important, "line": d.line})
                walk(n.children)
        walk(sheet.nodes)
        out["comments"] = [{"text": c.text, "line": c.line_number, "column": c.column + 1} for c in sheet.comments]
    except Exception as e:  # noqa: BLE001
        out["threw"] = f"{type(e).__name__}: {str(e)[:100]}"
    items.append(out)
caps = {"ruleSel": False, "ruleEnd": True, "declLine": True, "declValue": True, "atrules": False, "atrulePrelude": False, "comments": True, "declOrder": False, "errors": False}
OUT.mkdir(parents=True, exist_ok=True)
json.dump({"tool": "current", "caps": caps, "position": {}, "items": items}, open(OUT / "norm_current.json", "w", encoding="utf-8"), ensure_ascii=False)
print("current reader:", len(items), "inputs, threw", sum(1 for i in items if i["threw"]))
