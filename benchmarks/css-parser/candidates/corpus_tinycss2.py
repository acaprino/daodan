"""tinycss2 over the corpus (data only): parse_stylesheet, then parse_blocks_contents on every block. ParseError nodes are the errors."""
import multiprocessing
import os
import time
from collections import Counter
from pathlib import Path

import tinycss2

HERE = Path(__file__).resolve().parent
ROOT = os.environ.get('CORPUS', str(HERE / 'corpus/node_modules'))
OUT = Path(os.environ.get('OUT', HERE / 'out'))


def pkg_of(p):
    rel = os.path.relpath(p, ROOT).split(os.sep)
    return f'{rel[0]}/{rel[1]}' if rel[0].startswith('@') else rel[0]


def blocks(content):
    return tinycss2.parse_blocks_contents(content, skip_comments=False, skip_whitespace=True)


def process(path):
    try:
        text = open(path, encoding='utf-8').read()
    except Exception:  # noqa: BLE001
        return None
    if len(text) > 8_000_000:
        return None
    c = Counter()
    kinds = Counter()
    t0 = time.process_time()
    try:
        stack = [tinycss2.parse_stylesheet(text, skip_comments=False, skip_whitespace=True)]
        while stack:
            for n in stack.pop():
                t = n.type
                if t == 'qualified-rule':
                    c['rules'] += 1
                    stack.append(blocks(n.content))
                elif t == 'at-rule':
                    c['atrules'] += 1
                    if n.content is not None:
                        stack.append(blocks(n.content))
                elif t == 'declaration':
                    c['decls'] += 1
                elif t == 'comment':
                    c['comments'] += 1
                elif t == 'error':
                    c['errors'] += 1
                    kinds[n.message[:80]] += 1
        threw = None
    except Exception as e:  # noqa: BLE001
        threw = f'{type(e).__name__}: {str(e)[:80]}'
    return {'path': path, 'pkg': pkg_of(path), 'bytes': len(text), 'c': dict(c), 'kinds': dict(kinds), 'cpu': time.process_time() - t0, 'threw': threw}


if __name__ == '__main__':
    files = []
    for dp, _dn, fn in os.walk(ROOT):
        for f in fn:
            if f.lower().endswith('.css'):
                files.append(os.path.join(dp, f))
    wall = time.time()
    with multiprocessing.Pool(4) as pool:
        res = [r for r in pool.imap_unordered(process, files, chunksize=8) if r]
    wall = time.time() - wall
    tot = Counter()
    per = {}
    kinds = Counter()
    sample = {}
    for r in res:
        p = per.setdefault(r['pkg'], Counter())
        for X in (tot, p):
            X['files'] += 1
            X['bytes'] += r['bytes']
            X['cpu_ms'] += int(r['cpu'] * 1000)
            if r['threw']:
                X['threw'] += 1
                X['filesWithError'] += 1
            else:
                for k, v in r['c'].items():
                    X[k] += v
                if r['c'].get('errors'):
                    X['filesWithError'] += 1
        for k, v in r['kinds'].items():
            kinds[k] += v
            sample.setdefault(k, r['path'])
    out = ['tool: tinycss2 1.5.1',
           f"corpus: {tot['files']} files, {tot['bytes'] / 1e6:.1f} MB, cpu time {tot['cpu_ms']} ms across 4 workers, wall {wall:.1f} s",
           f"rules {tot['rules']}, declarations {tot['decls']}, at-rules {tot['atrules']}, comments {tot['comments']}",
           f"files with an error: {tot['filesWithError']}; errors (ParseError nodes): {tot['errors']}; files that threw: {tot['threw']}",
           '\n## per package: files, errors, rules, decls, atrules']
    for n, X in sorted(per.items(), key=lambda kv: -kv[1]['errors'])[:14]:
        out.append(f"{n:<34} {X['files']:>4} err {X['errors']:>6} threw {X['threw']:>3} rules {X['rules']:>7} decls {X['decls']:>8} at {X['atrules']:>5}")
    out.append('\n## messages (count, first file)')
    for k, v in kinds.most_common(14):
        out.append(f'{v:>6}  {k}   [{os.path.relpath(sample[k], ROOT)}]')
    OUT.mkdir(parents=True, exist_ok=True)
    open(OUT / 'corpus_tinycss2.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('\n'.join(out[:4]))
