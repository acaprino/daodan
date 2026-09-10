#!/usr/bin/env python3
"""Merge per-batch classification files into one archive index, and render a
local gallery for reviewing it.

The classification itself is done by whatever produced the batch files: this
script only validates them against the archive on disk, joins them to the
grabber's manifest, and writes three artifacts next to the media.

    _labels.json     one entry per file, joined with post code, date and permalink
    _labels.csv      the same, flat, for a spreadsheet
    etichette.html   a local gallery grouped by label, served from the thumbnails

Validation is the point of the merge step. An archive index that silently
omits a third of the files, or that carries a label nobody defined, is worse
than no index, so every gap is reported and the exit code says whether the
index covers the archive.

Usage:
    python label_index.py <archive-dir> [--parts DIR] [--strict]
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

LABELS = [
    "colazione", "panettoni", "colombe", "uova-pasqua", "torte-celebrative",
    "torte-classiche", "piccola-pasticceria", "gelateria", "salato",
    "cioccolateria", "laboratorio", "locale", "team", "eventi-catering",
    "packaging", "promo-grafica", "altro",
]
SEASONS = [
    "natale", "pasqua", "estate", "san-valentino", "matrimonio", "laurea",
    "comunione-battesimo", "compleanno", "halloween", "carnevale",
    "ferragosto", "nessuna",
]

EXIT_OK = 0
EXIT_INCOMPLETE = 1
EXIT_BAD_ARGUMENTS = 2


def log(msg: str) -> None:
    print(f"[label] {msg}", flush=True)


def code_of(filename: str) -> str | None:
    """Filenames are <date>_<shortcode>[_NN][_frame].<ext>, so the shortcode is
    the second underscore-separated field."""
    parts = Path(filename).stem.split("_")
    return parts[1] if len(parts) >= 2 else None


def load_parts(parts_dir: Path) -> tuple[dict[str, dict], list[str]]:
    entries: dict[str, dict] = {}
    problems: list[str] = []
    files = sorted(parts_dir.glob("batch_*.json"))
    if not files:
        problems.append(f"no batch_*.json found in {parts_dir}")
    for path in files:
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{path.name}: unreadable ({exc})")
            continue
        if not isinstance(rows, list):
            problems.append(f"{path.name}: expected a JSON array")
            continue
        for row in rows:
            if not isinstance(row, dict) or not row.get("file"):
                problems.append(f"{path.name}: an entry has no file field")
                continue
            name = str(row["file"]).strip()
            if name in entries:
                problems.append(f"{name}: labelled twice, keeping the first")
                continue
            primary = row.get("primary")
            if primary not in LABELS:
                problems.append(f"{name}: unknown primary label {primary!r}, filed as altro")
                primary = "altro"
            tags = [t for t in (row.get("tags") or []) if t in LABELS and t != primary]
            season = row.get("stagione") if row.get("stagione") in SEASONS else "nessuna"
            entries[name] = {
                "primary": primary,
                "tags": tags,
                "persone": bool(row.get("persone")),
                "stagione": season,
                "descrizione": (row.get("descrizione") or "").strip(),
            }
    return entries, problems


def build_index(archive: Path, entries: dict[str, dict]) -> tuple[list[dict], list[str], list[str]]:
    thumbs = {p.name for p in (archive / "thumbs").glob("*.jpg")}
    manifest_path = archive / "_manifest.json"
    posts = {}
    if manifest_path.exists():
        try:
            posts = json.loads(manifest_path.read_text(encoding="utf-8")).get("posts", {})
        except Exception:
            log("manifest unreadable, the index will carry no captions")

    missing = sorted(thumbs - set(entries))
    unknown = sorted(set(entries) - thumbs)

    index = []
    for name in sorted(thumbs):
        entry = entries.get(name)
        if not entry:
            continue
        code = code_of(name)
        post = posts.get(code, {}) if code else {}
        is_frame = name.endswith("_frame.jpg")
        index.append({
            "file": name,
            "kind": "video-frame" if is_frame else "photo",
            "source": f"frames/{name}" if is_frame else name,
            "thumb": f"thumbs/{name}",
            "code": code,
            "date": name[:10],
            "permalink": post.get("permalink") or (f"https://www.instagram.com/p/{code}/" if code else None),
            "caption": post.get("caption"),
            **entry,
        })
    return index, missing, unknown


GALLERY_CSS = """
:root { --bg:#faf7f2; --ink:#2b2622; --muted:#8a7f75; --line:#e3dbd0; --accent:#8c5a3c; }
* { box-sizing:border-box; }
body { margin:0; padding:24px; background:var(--bg); color:var(--ink);
       font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
h1 { font-size:24px; margin:0 0 4px; font-weight:600; }
.sub { color:var(--muted); margin-bottom:20px; }
.filters { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:24px;
           position:sticky; top:0; background:var(--bg); padding:12px 0; border-bottom:1px solid var(--line); z-index:5; }
.filters button { border:1px solid var(--line); background:#fff; color:var(--ink);
                  padding:6px 12px; border-radius:999px; cursor:pointer; font-size:13px; }
.filters button:hover { border-color:var(--accent); }
.filters button.on { background:var(--accent); color:#fff; border-color:var(--accent); }
.filters button .n { opacity:.6; margin-left:6px; }
section { margin-bottom:36px; }
section h2 { font-size:17px; margin:0 0 12px; padding-bottom:6px; border-bottom:1px solid var(--line); }
section h2 .n { color:var(--muted); font-weight:400; font-size:14px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:14px; }
figure { margin:0; background:#fff; border:1px solid var(--line); border-radius:10px; overflow:hidden; }
figure img { width:100%; aspect-ratio:1; object-fit:cover; display:block; background:var(--line); }
figcaption { padding:8px 10px; font-size:12px; }
figcaption .d { color:var(--ink); }
figcaption .m { color:var(--muted); margin-top:5px; font-size:11px;
                display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.tag { background:var(--bg); border:1px solid var(--line); border-radius:4px; padding:1px 5px; }
.people { color:#a4442e; }
a { color:inherit; }
@media (max-width:520px){ body{padding:14px;} .grid{grid-template-columns:repeat(auto-fill,minmax(140px,1fr));} }
"""

GALLERY_JS = """
const buttons = document.querySelectorAll('.filters button');
buttons.forEach(b => b.onclick = () => {
  const want = b.dataset.f;
  buttons.forEach(x => x.classList.toggle('on', x === b));
  document.querySelectorAll('section').forEach(s => {
    s.hidden = want !== 'all' && s.dataset.label !== want;
  });
});
"""


def render_gallery(index: list[dict], archive: Path, username: str) -> Path:
    by_label: dict[str, list[dict]] = defaultdict(list)
    for row in index:
        by_label[row["primary"]].append(row)

    order = [l for l in LABELS if l in by_label]
    parts = [
        "<!doctype html><html lang='it'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>Archivio @{html.escape(username)}</title><style>{GALLERY_CSS}</style></head><body>",
        f"<h1>Archivio @{html.escape(username)}</h1>",
        f"<p class='sub'>{len(index)} immagini etichettate, "
        f"{sum(1 for r in index if r['kind'] == 'video-frame')} da video. "
        f"Generato il {datetime.now(timezone.utc).strftime('%d/%m/%Y')}.</p>",
        "<div class='filters'><button class='on' data-f='all'>tutte"
        f"<span class='n'>{len(index)}</span></button>",
    ]
    for label in order:
        parts.append(
            f"<button data-f='{label}'>{label}<span class='n'>{len(by_label[label])}</span></button>"
        )
    parts.append("</div>")

    for label in order:
        rows = sorted(by_label[label], key=lambda r: r["date"], reverse=True)
        parts.append(f"<section data-label='{label}'><h2>{label} "
                     f"<span class='n'>{len(rows)}</span></h2><div class='grid'>")
        for row in rows:
            meta = [f"<span>{html.escape(row['date'])}</span>"]
            for tag in row["tags"]:
                meta.append(f"<span class='tag'>{html.escape(tag)}</span>")
            if row["stagione"] != "nessuna":
                meta.append(f"<span class='tag'>{html.escape(row['stagione'])}</span>")
            if row["persone"]:
                meta.append("<span class='people'>persone</span>")
            if row["kind"] == "video-frame":
                meta.append("<span class='tag'>video</span>")
            link = row.get("permalink")
            img = (f"<img loading='lazy' src='{html.escape(row['thumb'])}' "
                   f"alt='{html.escape(row['descrizione'][:120])}'>")
            if link:
                img = f"<a href='{html.escape(link)}' target='_blank' rel='noopener'>{img}</a>"
            parts.append(
                f"<figure>{img}<figcaption>"
                f"<div class='d'>{html.escape(row['descrizione'])}</div>"
                f"<div class='m'>{''.join(meta)}</div>"
                f"</figcaption></figure>"
            )
        parts.append("</div></section>")

    parts.append(f"<script>{GALLERY_JS}</script></body></html>")
    out = archive / "etichette.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="label_index")
    parser.add_argument("archive", type=Path, help="the grabber's output directory")
    parser.add_argument("--parts", type=Path, default=None, help="directory of batch_*.json")
    parser.add_argument("--strict", action="store_true", help="exit non-zero on any gap")
    args = parser.parse_args(argv)

    archive = args.archive
    if not (archive / "thumbs").is_dir():
        log(f"no thumbs/ directory under {archive}")
        return EXIT_BAD_ARGUMENTS
    parts_dir = args.parts or (archive / "_labels_parts")

    entries, problems = load_parts(parts_dir)
    for problem in problems[:20]:
        log(problem)
    if len(problems) > 20:
        log(f"... and {len(problems) - 20} more problems")

    index, missing, unknown = build_index(archive, entries)
    username = "?"
    manifest = archive / "_manifest.json"
    if manifest.exists():
        try:
            username = json.loads(manifest.read_text(encoding="utf-8")).get("username", "?")
        except Exception:
            pass

    (archive / "_labels.json").write_text(
        json.dumps({"username": username,
                    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "labels": LABELS, "items": index}, indent=2, ensure_ascii=False),
        encoding="utf-8")

    with (archive / "_labels.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["file", "tipo", "categoria", "tag", "stagione", "persone",
                         "data", "descrizione", "permalink"])
        for row in index:
            writer.writerow([row["file"], row["kind"], row["primary"], " ".join(row["tags"]),
                             row["stagione"], "si" if row["persone"] else "no",
                             row["date"], row["descrizione"], row["permalink"] or ""])

    gallery = render_gallery(index, archive, username)

    counts = Counter(r["primary"] for r in index)
    log(f"{len(index)} immagini indicizzate")
    for label, n in counts.most_common():
        log(f"  {label:22} {n}")
    if missing:
        log(f"NON etichettate: {len(missing)}")
        for name in missing[:15]:
            log(f"  {name}")
        if len(missing) > 15:
            log(f"  ... e altre {len(missing) - 15}")
    if unknown:
        log(f"etichette per file inesistenti: {len(unknown)} (ignorate)")
    log(f"scritti: _labels.json, _labels.csv, {gallery.name}")

    if missing and args.strict:
        return EXIT_INCOMPLETE
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
