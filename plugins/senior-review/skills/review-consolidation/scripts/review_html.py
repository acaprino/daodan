"""Render review findings as one standalone HTML page with a navigable index.

The page is a view of records that already exist: it reads `retained_findings`
(final-report) or `findings` (reviewer-result) and their `gaps`, and adds no
finding, field or judgement. Each finding opens with its `example`, the plain
explanation through one realistic case. A missing field is shown as `unknown`; a field the
page has no place for is listed under "Other fields". With `--root` each finding
also shows the cited source lines. The page needs no server and no Daodan UI:
the reader accepts or rejects each fix on it and pastes the reply block back.

Standard library only.

Usage:

    python review_html.py render RESULT.json [RESULT.json ...] --out REPORT.html
        [--root PROJECT_ROOT] [--title TEXT]
"""

import argparse
import json
import sys
from html import escape
from pathlib import Path

SEVERITIES = ["Critical", "High", "Medium", "Low"]
SHOWN = {"file", "line", "title", "severity", "confidence", "evidence_class", "premise_provenance", "reviewer",
         "introduced_by_candidate", "example", "premise", "trigger", "evidence", "counterevidence_checked", "fix"}
CONTEXT_LINES = 2

CSS = """
:root{color-scheme:light dark;--line:#d9dde3;--soft:#f4f5f7;--muted:#57606a;--link:#1d4ed8;--bad:#b42318;--warn:#b45309}
@media(prefers-color-scheme:dark){:root{--line:#30363d;--soft:#161b22;--muted:#9aa4af;--link:#7aa7ff;--bad:#ff8577;--warn:#f0a35e}}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 system-ui,sans-serif}
a{color:var(--link)}
code,pre{font:13px/1.6 ui-monospace,Menlo,Consolas,monospace}
pre{margin:0;padding:12px;background:var(--soft);border:1px solid var(--line);border-radius:6px;white-space:pre-wrap;overflow-wrap:anywhere}
header,.layout{max-width:1200px;margin:0 auto;padding:24px 16px}
header{padding-bottom:0}
h1{margin:0;font-size:28px;line-height:1.25}
h2{margin:0;font-size:20px;line-height:1.35}
h3{margin:20px 0 6px;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
p,ul,dl{margin:0}
.muted{color:var(--muted)}
.layout{display:flex;flex-wrap:wrap;align-items:flex-start;gap:24px}
nav{flex:1 1 260px}
main{flex:999 1 520px;min-width:0}
nav ol,nav ul{list-style:none;margin:0 0 16px;padding:0}
nav a{display:block;padding:8px;border-radius:6px;text-decoration:none}
nav a:hover{background:var(--soft)}
article,section.block{margin-bottom:16px;padding:20px;border:1px solid var(--line);border-radius:8px}
dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 16px;margin-top:12px;padding:12px;background:var(--soft);border-radius:6px}
dt{font-size:12px;color:var(--muted)}
dd{margin:0;font-weight:600}
.sev-Critical,.sev-High{color:var(--bad)}
.sev-Medium{color:var(--warn)}
mark{background:none;color:inherit;font-weight:700}
fieldset{margin:20px 0 0;padding:12px;border:1px solid var(--line);border-radius:6px}
label{display:inline-flex;align-items:center;gap:6px;min-height:44px;margin-right:16px}
"""

JS = """
const reply = () => {
  document.getElementById('reply').textContent = [...document.querySelectorAll('article[data-ref]')].map((a) => {
    const pick = a.querySelector('input:checked');
    return a.dataset.ref + '  fix ' + (pick ? pick.value : 'undecided');
  }).join('\\n');
};
document.addEventListener('change', reply);
reply();
"""


def load(paths):
    """The findings and gaps of the given result files, each finding with its file's `reviewer` when it has none."""
    findings, gaps = [], []
    for path in paths:
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError(f"{path}: not a JSON object")
        items = record.get("retained_findings", record.get("findings"))
        if not isinstance(items, list):
            raise ValueError(f"{path}: no retained_findings or findings list")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"{path}: a finding is not an object")
            findings.append({"reviewer": record.get("reviewer"), **item})
        gaps.extend(record.get("gaps") or [])
    return findings, gaps


def text(value):
    """A field as escaped text: `unknown` when absent, JSON when it is not a string."""
    if value is None or value == "":
        return "unknown"
    return escape(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))


def rank(finding):
    severity = finding.get("severity")
    order = SEVERITIES.index(severity) if severity in SEVERITIES else len(SEVERITIES)
    line = finding.get("line")
    return order, str(finding.get("file")), line if isinstance(line, int) else 0


def source_lines(root, finding):
    """The cited line with its neighbours as escaped HTML, or None when the file is not under `root`."""
    file, line = finding.get("file"), finding.get("line")
    if root is None or not isinstance(file, str) or not isinstance(line, int):
        return None
    path = (root / file).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    for number in range(max(1, line - CONTEXT_LINES), min(len(lines), line + CONTEXT_LINES) + 1):
        row = f"{number:>4}  {escape(lines[number - 1])}"
        rows.append(f"<mark>{row}</mark>" if number == line else row)
    return "\n".join(rows) or None


def section(title, body):
    return f"<h3>{title}</h3>{body}"


def article(ref, anchor, finding, root):
    severity = text(finding.get("severity"))
    place = f"{text(finding.get('file'))}:{text(finding.get('line'))}"
    facts = [("Severity", f'<span class="sev-{severity}">{severity}</span>'),
             ("Confidence", text(finding.get("confidence"))),
             ("Evidence class", text(finding.get("evidence_class"))),
             ("Premise provenance", text(finding.get("premise_provenance"))),
             ("Reviewer", text(finding.get("reviewer")))]
    if "introduced_by_candidate" in finding:
        facts.append(("Introduced by the change", text(finding["introduced_by_candidate"])))
    parts = [f'<article id="{anchor}" data-ref="{ref}  {place}">',
             f"<h2>{ref} · {text(finding.get('title') or finding.get('premise'))}</h2>",
             f"<p><code>{place}</code></p>",
             "<dl>" + "".join(f"<div><dt>{name}</dt><dd>{value}</dd></div>" for name, value in facts) + "</dl>",
             section("In plain words, with an example", f"<p>{text(finding.get('example'))}</p>"),
             section("Premise", f"<p>{text(finding.get('premise'))}</p>"),
             section("Trigger", f"<p>{text(finding.get('trigger'))}</p>"),
             section("Evidence", f"<pre>{text(finding.get('evidence'))}</pre>")]
    excerpt = source_lines(root, finding)
    if excerpt:
        parts.append(section("Source", f"<pre>{excerpt}</pre>"))
    checked = finding.get("counterevidence_checked")
    if isinstance(checked, list) and checked:
        parts.append(section("Counterevidence checked", "<ul>" + "".join(f"<li>{text(item)}</li>" for item in checked) + "</ul>"))
    others = {name: value for name, value in finding.items() if name not in SHOWN}
    if others:
        parts.append(section("Other fields", "<ul>" + "".join(
            f"<li><code>{escape(name)}</code>: {text(value)}</li>" for name, value in others.items()) + "</ul>"))
    parts.append(f"<fieldset><legend>Fix</legend><p>{text(finding.get('fix'))}</p>"
                 f'<label><input type="radio" name="{anchor}" value="accepted"> Accept</label>'
                 f'<label><input type="radio" name="{anchor}" value="rejected"> Reject</label></fieldset>')
    parts.append("</article>")
    return "".join(parts)


def render(findings, gaps, title="Review findings", root=None):
    """The whole page for these findings, ordered by severity, file and line."""
    ordered = sorted(findings, key=rank)
    width = max(2, len(str(len(ordered))))
    entries = [(f"F-{number:0{width}}", f"f-{number:0{width}}", finding) for number, finding in enumerate(ordered, 1)]
    counts = [f"{sum(1 for f in ordered if f.get('severity') == name)} {name}" for name in SEVERITIES
              if any(f.get("severity") == name for f in ordered)]
    by_finding = "".join(
        f'<li><a href="#{anchor}"><b class="sev-{text(f.get("severity"))}">{ref} · {text(f.get("severity"))}</b><br>'
        f'{text(f.get("title") or f.get("premise"))}<br><code>{text(f.get("file"))}:{text(f.get("line"))}</code></a></li>'
        for ref, anchor, f in entries)
    files = {}
    for ref, anchor, finding in entries:
        files.setdefault(text(finding.get("file")), []).append(f'<a href="#{anchor}">{ref}</a>')
    by_file = "".join(f"<li><code>{file}</code>{''.join(links)}</li>" for file, links in sorted(files.items()))
    gap_items = "".join(f"<li>{text(gap)}</li>" for gap in gaps) or "<li>none declared</li>"
    summary = f"{len(ordered)} findings" + (f" ({', '.join(counts)})" if counts else "") + f" · {len(gaps)} gaps"
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)}</title>'
            f"<style>{CSS}</style></head><body>"
            f'<header><h1>{escape(title)}</h1><p class="muted">{summary}</p></header><div class="layout">'
            f'<nav aria-label="Index"><h3>Findings</h3><ol>{by_finding}</ol><h3>By file</h3><ul>{by_file}</ul>'
            f'<ul><li><a href="#gaps">Coverage gaps</a></li><li><a href="#reply-block">Reply for the agent</a></li></ul></nav>'
            f"<main>{''.join(article(ref, anchor, finding, root) for ref, anchor, finding in entries)}"
            f'<section class="block" id="gaps"><h2>Coverage gaps</h2><ul>{gap_items}</ul></section>'
            f'<section class="block" id="reply-block"><h2>Reply for the agent</h2>'
            f'<p class="muted">Paste this block into the session.</p><pre id="reply"></pre></section>'
            f"</main></div><script>{JS}</script></body></html>\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("render")
    command.add_argument("results", nargs="+")
    command.add_argument("--out", required=True)
    command.add_argument("--root")
    command.add_argument("--title", default="Review findings")
    args = parser.parse_args(argv)
    try:
        findings, gaps = load(args.results)
    except (OSError, ValueError) as error:
        print(f"review_html: {error}", file=sys.stderr)
        return 1
    page = render(findings, gaps, args.title, Path(args.root) if args.root else None)
    Path(args.out).write_text(page, encoding="utf-8")
    print(json.dumps({"output_path": args.out, "findings": len(findings), "gaps": len(gaps)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
