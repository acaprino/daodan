"""The current reader (languages/stylesheet.py, copied unchanged with base.py and comments.py; _treesitter stubbed: not used by parse_sheet) over the corpus."""
import multiprocessing
import os
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, os.environ.get('CURRENT_LANG', str(HERE / 'lang')))
from languages import stylesheet  # noqa: E402

ROOT = os.environ.get('CORPUS', str(HERE / 'corpus/node_modules'))
OUT = Path(os.environ.get('OUT', HERE / 'out'))


def pkg_of(p):
    rel = os.path.relpath(p, ROOT).split(os.sep)
    return f'{rel[0]}/{rel[1]}' if rel[0].startswith('@') else rel[0]


def process(path):
    try:
        text = open(path, encoding='utf-8').read()
    except Exception:  # noqa: BLE001
        return None
    if len(text) > 8_000_000:
        return None
    text = text.replace('\r\n', '\n').replace('\r', '\n')  # snapshot._text
    c = Counter()
    t0 = time.process_time()
    threw = None
    try:
        sheet = stylesheet.parse_sheet(text, 'css')
        stack = list(sheet.nodes)
        while stack:
            n = stack.pop()
            if n.kind in ('rule', 'keyframe'):
                c['rules'] += 1
            elif n.kind == 'at-rule':
                c['atrules'] += 1
            c['decls'] += len(n.declarations)
            stack.extend(n.children)
        c['comments'] += len(sheet.comments)
    except Exception as e:  # noqa: BLE001
        threw = f'{type(e).__name__}: {str(e)[:80]}'
    return {'pkg': pkg_of(path), 'bytes': len(text), 'c': dict(c), 'cpu': time.process_time() - t0, 'threw': threw}


if __name__ == '__main__':
    files = [os.path.join(dp, f) for dp, _dn, fn in os.walk(ROOT) for f in fn if f.lower().endswith('.css')]
    wall = time.time()
    with multiprocessing.Pool(4) as pool:
        res = [r for r in pool.imap_unordered(process, files, chunksize=8) if r]
    wall = time.time() - wall
    tot = Counter()
    for r in res:
        tot['files'] += 1
        tot['bytes'] += r['bytes']
        tot['cpu_ms'] += int(r['cpu'] * 1000)
        if r['threw']:
            tot['threw'] += 1
        for k, v in r['c'].items():
            tot[k] += v
    out = ['tool: current reader (languages/stylesheet.py parse_sheet, css)',
           f"corpus: {tot['files']} files, {tot['bytes'] / 1e6:.1f} MB, cpu {tot['cpu_ms']} ms across 4 workers, wall {wall:.1f} s",
           f"rules {tot['rules']}, declarations {tot['decls']}, at-rule blocks {tot['atrules']}, comments {tot['comments']}",
           f"files that threw: {tot['threw']} (the reader reports no parse errors)"]
    OUT.mkdir(parents=True, exist_ok=True)
    open(OUT / 'corpus_current.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('\n'.join(out))
