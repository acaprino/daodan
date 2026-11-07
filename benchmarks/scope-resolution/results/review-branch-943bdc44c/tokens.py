"""Token accounting of a Claude Code review run from the session transcripts.

Usage: python -I tokens.py SESSION_ID ROOT_AGENT_PREFIX
Prints, per agent in the tree rooted at the coordinator: turns, output tokens,
cache-creation (new input) tokens, max context, final context, and totals.
Formulas:
  final context = input + cache_read + cache_creation of the last turn, + its output
  new tokens    = sum over turns of input + cache_creation + output
"""
import glob
import json
import os
import sys

BASE = os.path.expanduser("~/.claude/projects/D--Projects-daodan")


def tally(path):
    t = {"turns": 0, "out": 0, "cc": 0, "inp": 0, "maxctx": 0, "final": 0}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            m = o.get("message") or {}
            u = m.get("usage") if isinstance(m, dict) else None
            if not u:
                continue
            t["turns"] += 1
            inp = u.get("input_tokens", 0)
            cc = u.get("cache_creation_input_tokens", 0)
            cr = u.get("cache_read_input_tokens", 0)
            out = u.get("output_tokens", 0)
            t["out"] += out
            t["cc"] += cc
            t["inp"] += inp
            ctx = inp + cr + cc
            t["maxctx"] = max(t["maxctx"], ctx)
            t["final"] = ctx + out
    t["new"] = t["inp"] + t["cc"] + t["out"]
    return t


def main(session, root_prefix):
    subdir = os.path.join(BASE, session, "subagents")
    metas = {}
    for mp in glob.glob(os.path.join(subdir, "*.meta.json")):
        aid = os.path.basename(mp)[len("agent-"):-len(".meta.json")]
        with open(mp, encoding="utf-8") as f:
            metas[aid] = json.load(f)
    roots = [a for a in metas if a.startswith(root_prefix)]
    if len(roots) != 1:
        sys.exit(f"root agent prefix {root_prefix!r} matches {roots}")
    root = roots[0]
    tree = [root]
    changed = True
    while changed:
        changed = False
        for aid, m in metas.items():
            if aid not in tree and m.get("parentAgentId") in tree:
                tree.append(aid)
                changed = True
    totals = {"turns": 0, "out": 0, "cc": 0, "inp": 0, "new": 0}
    print(f"{'agent':20} {'type':34} {'description':46} {'turns':>5} {'out':>7} {'new':>8} {'maxctx':>8} {'final':>8}")
    for aid in tree:
        m = metas[aid]
        t = tally(os.path.join(subdir, f"agent-{aid}.jsonl"))
        for k in totals:
            totals[k] += t[k]
        print(f"{aid[:20]:20} {m.get('agentType','')[:34]:34} {m.get('description','')[:46]:46} {t['turns']:5} {t['out']:7} {t['new']:8} {t['maxctx']:8} {t['final']:8}")
    print("totals", totals)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
