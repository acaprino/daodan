"""Token accounting of one review run from the Claude Code session transcripts.

Usage:
    python -I tokens.py SESSION                  # a fresh process: its transcript and all sub-agents
    python -I tokens.py SESSION ROOT_PREFIX      # a coordinator sub-agent and its descendants

A request occupies several transcript lines, one per content block, each repeating
its usage: count one per request (message id), keeping the last.

- final: input + cache read + cache write of the last request, plus its output.
- new: sum per request of input + cache write + output. It counts cache rewrites, so
  it grows with waiting time; rewr is the number of requests that wrote more than half
  of their context again. Compare runs on final and output.
- leak: context records (attachment, user, system) that carry the seed words.
"""
import glob
import json
import os
import re
import sys

BASE = os.path.expanduser("~/.claude/projects/D--Projects-daodan")
SEED = re.compile(r"seeded defect|review-light-943bdc44c")


def scan(path):
    last = {}
    leak = 0
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("type") in ("attachment", "user", "system") and SEED.search(line):
            leak += 1
        message = record.get("message")
        usage = message.get("usage") if isinstance(message, dict) else None
        if usage:
            last[message.get("id") or record.get("requestId") or record.get("uuid")] = usage
    row = dict(requests=len(last), out=0, new=0, rewr=0, final=0, leak=leak)
    for usage in last.values():
        inp, cc = usage.get("input_tokens", 0), usage.get("cache_creation_input_tokens", 0)
        ctx = inp + cc + usage.get("cache_read_input_tokens", 0)
        out = usage.get("output_tokens", 0)
        row["out"] += out
        row["new"] += inp + cc + out
        row["rewr"] += ctx > 20000 and cc > ctx / 2
        row["final"] = ctx + out
    return row


def main(session, prefix=None):
    subdir = os.path.join(BASE, session, "subagents")
    metas = {}
    for path in glob.glob(os.path.join(subdir, "*.meta.json")):
        metas[os.path.basename(path)[len("agent-"):-len(".meta.json")]] = json.load(open(path, encoding="utf-8"))
    rows = []
    if prefix is None:
        rows.append(("coordinator", scan(os.path.join(BASE, session + ".jsonl"))))
        tree = list(metas)
    else:
        roots = [a for a in metas if a.startswith(prefix)]
        if len(roots) != 1:
            sys.exit(f"prefix {prefix!r} matches {roots}")
        tree, grew = roots, True
        while grew:
            grew = False
            for agent, meta in metas.items():
                if agent not in tree and meta.get("parentAgentId") in tree:
                    tree.append(agent)
                    grew = True
    for agent in tree:
        rows.append((metas[agent].get("description", agent), scan(os.path.join(subdir, f"agent-{agent}.jsonl"))))
    print(f"{'agent':46} {'req':>4} {'out':>7} {'new':>8} {'rewr':>4} {'final':>7} {'leak':>4}")
    total = dict(requests=0, out=0, new=0)
    for name, row in rows:
        for key in total:
            total[key] += row[key]
        print(f"{name[:46]:46} {row['requests']:4} {row['out']:7} {row['new']:8} {row['rewr']:4} {row['final']:7} {row['leak']:4}")
    print("totals", total)


if __name__ == "__main__":
    main(*sys.argv[1:3])
