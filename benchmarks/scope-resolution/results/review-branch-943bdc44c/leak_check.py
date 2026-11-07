"""Where do the words that name the seeded defect reach a review agent's context?

Usage: python -I leak_check.py SESSION
For each sub-agent transcript: the record types carrying the words, with a short
excerpt, split between what the agent received (user, attachment, system) and what
it wrote itself (assistant).
"""
import glob
import json
import os
import re
import sys

BASE = os.path.expanduser("~/.claude/projects/D--Projects-daodan")
WORDS = re.compile(r"seeded|double[- ]discount|bench-seed|f52f7352c|oracle|sconto sottratto")


def texts(record):
    yield json.dumps(record, ensure_ascii=False)


session = sys.argv[1]
for path in sorted(glob.glob(os.path.join(BASE, session, "subagents", "*.jsonl"))):
    meta_path = path[: -len(".jsonl")] + ".meta.json"
    desc = json.load(open(meta_path, encoding="utf-8")).get("description", "") if os.path.exists(meta_path) else ""
    rows = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            record = json.loads(line)
        except ValueError:
            continue
        kind = record.get("type")
        if kind == "api-request-blob":
            continue
        for match in WORDS.finditer(line):
            key = (kind, match.group(0))
            if key not in rows:
                start = max(0, match.start() - 110)
                rows[key] = line[start: match.end() + 90].replace("\\n", " ")
    print("==", os.path.basename(path)[:28], desc)
    for (kind, word), excerpt in sorted(rows.items(), key=str):
        print(f"  [{kind}] {word}: ...{excerpt}...")
