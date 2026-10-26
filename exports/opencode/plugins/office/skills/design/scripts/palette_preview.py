#!/usr/bin/env python3
"""Render palette candidates as one static comparison page.

    palette_preview.py CANDIDATES.json --out compare.html [--open] [--title TEXT]

CANDIDATES.json is the output of `palette.py candidates` (or any JSON with a
`candidates` list of palettes). The page opens with a compact overview: one
card per candidate with its number, character and colour strip. Hovering a card
previews its detail below (colour fields with role and hex, contrast figures,
the same sample slide and sample page drawn in its colours); clicking pins it,
and the arrow keys move between candidates. The page is self-contained: one
inline script, no external assets. It is a wireframe of the colour roles, not a
rendered deck or document. After the user has seen it, ask which number to use;
the page does not report the choice back.
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from html import escape
from pathlib import Path

SCHEMA = "daodan/palette-preview/v1"
NOTE = ("Colour roles only. Fonts, layouts and rendering come from the saved file; "
        "contrast figures are computed from the hex values.")

ROLES = (("background", "Background", 30), ("surface", "Surface", 14), ("ink", "Ink", 14),
         ("accent", "Accent", 14), ("muted", "Muted text", 10))


def _field(label: str, value: str, text: str, grow: int) -> str:
    return (f'<div class="field" style="background:{escape(value)};color:{escape(text)};flex:{grow}">'
            f'<span class="role">{escape(label)}</span><span class="hex">{escape(value)}</span></div>')


def _luminance(value: str) -> float:
    channels = []
    for i in (0, 2, 4):
        c = int(value.lstrip("#")[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _text_on(value: str, palette: dict) -> str:
    """Whichever of ink and background reads better on this field."""
    field = _luminance(value)
    def ratio(other):
        a, b = _luminance(other), field
        return (max(a, b) + 0.05) / (min(a, b) + 0.05)
    return max((palette["ink"], palette["background"]), key=ratio)


def render_card(index: int, palette: dict) -> str:
    label = palette.get("label") or palette.get("variant") or palette.get("name", "")
    name, _, blurb = label.partition(":")
    passes = palette.get("check", {}).get("passes")
    strip = "".join(f'<i style="background:{escape(palette[role])};flex:{grow}"></i>'
                    for role, _, grow in ROLES)
    strip += "".join(f'<i style="background:{escape(c)};flex:6"></i>' for c in palette.get("data", [])[:4])
    mark = '<span class="mark ok" title="All text 4.5:1, data 3:1">&#10003;</span>' if passes else (
        '<span class="mark warn" title="Below threshold">!</span>' if passes is False else "")
    return f"""
<button class="card" type="button" data-index="{index}" aria-pressed="{'true' if index == 1 else 'false'}" aria-controls="d{index}">
  <span class="strip" aria-hidden="true">{strip}</span>
  <span class="line"><span class="n">{index}</span><span class="name">{escape(name.strip())}</span>{mark}</span>
  <span class="blurb">{escape(blurb.strip()[:1].upper() + blurb.strip()[1:])}</span>
</button>"""


def render_candidate(index: int, palette: dict) -> str:
    bg, ink, sf = palette["background"], palette["ink"], palette["surface"]
    ac, mu = palette["accent"], palette["muted"]
    data = palette.get("data", [])[:4]
    check = palette.get("check", {})
    text = check.get("text", {})
    passes = check.get("passes")
    label = palette.get("label") or palette.get("variant") or palette.get("name", "")
    name, _, blurb = label.partition(":")
    fields = "".join(_field(role_label, palette[role], _text_on(palette[role], palette), grow)
                     for role, role_label, grow in ROLES)
    fields += "".join(_field(f"Data {i + 1}", value, _text_on(value, palette), 7)
                      for i, value in enumerate(data))
    bars = "".join(f'<div class="bar" style="height:{h}%;background:{escape(c)}"></div>'
                   for c, h in zip(data, (72, 46, 88, 34)))
    figures = []
    for role, label_text in (("ink", "Ink"), ("accent", "Accent"), ("muted", "Muted")):
        if role in text:
            figures.append(f"<dt>{label_text}</dt><dd>{min(text[role].values()):.1f}:1</dd>")
    data_contrast = check.get("data_on_background") or []
    if data_contrast:
        figures.append(f"<dt>Data</dt><dd>&ge; {min(data_contrast):.1f}:1</dd>")
    verdict = {True: ("ok", "All text 4.5:1, data 3:1"), False: ("warn", "Below threshold"),
               None: ("", "Not checked")}[passes]
    slide = f"""
<figure class="slide" style="background:{escape(bg)};color:{escape(ink)}">
  <div class="headline">Revenue grew 12% while fixed costs stayed flat</div>
  <div class="body">
    <div class="panel" style="background:{escape(sf)}"><b>Growth</b><p style="color:{escape(mu)}">Three regions above plan; EMEA led at +18%.</p></div>
    <div class="panel" style="background:{escape(sf)}"><b>Margin</b><p style="color:{escape(mu)}">Gross margin 41%, up two points year on year.</p></div>
    <div class="panel chart" style="background:{escape(sf)}">{bars}</div>
  </div>
  <div class="foot" style="color:{escape(mu)}">Source: annual report 2025 <span style="color:{escape(ac)}">&bull; Confidential</span></div>
</figure>"""
    page = f"""
<figure class="page" style="background:{escape(bg)};color:{escape(ink)}">
  <div class="rule" style="background:{escape(ac)}"></div>
  <h4>2. Operating review</h4>
  <p>Revenue grew 12% in the year while fixed costs stayed flat, which lifted the operating margin to its highest level since 2021.</p>
  <table><tr style="background:{escape(sf)}"><th>Region</th><th>2024</th><th>2025</th></tr>
  <tr><td>EMEA</td><td>12.4</td><td style="color:{escape(ac)};font-weight:600">14.6</td></tr>
  <tr><td>Americas</td><td>9.8</td><td>10.1</td></tr></table>
  <p class="caption" style="color:{escape(mu)}">Table 1. Revenue by region, EUR m</p>
</figure>"""
    return f"""
<section class="candidate" id="d{index}" aria-labelledby="c{index}"{'' if index == 1 else ' hidden'}>
  <div class="who">
    <div class="num" aria-hidden="true">{index}</div>
    <h2 id="c{index}">{escape(name.strip())}</h2>
    <p>{escape(blurb.strip()[:1].upper() + blurb.strip()[1:])}</p>
    <dl class="figures">{''.join(figures)}</dl>
    <p class="verdict {verdict[0]}">{verdict[1]}</p>
  </div>
  <div class="fields" role="img" aria-label="palette {index}">{fields}</div>
  <div class="samples">{slide}{page}</div>
</section>"""


def render(document: dict, title: str) -> str:
    candidates = document.get("candidates") or []
    if not candidates:
        raise ValueError("no candidates in the input")
    seeds = document.get("seeds") or candidates[0].get("seeds") or []
    seed_dots = "".join(f'<span class="seed" style="background:{escape(s)}" title="{escape(s)}"></span>'
                        f'<code>{escape(s)}</code>' for s in seeds)
    cards = "".join(render_card(i + 1, c) for i, c in enumerate(candidates))
    body = "".join(render_candidate(i + 1, c) for i, c in enumerate(candidates))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<style>
:root{{--paper:#E9E7E2;--ink:#1F1D1A;--mute:#6B665E;--line:#D2CEC6;--ok:#1F6B3A;--warn:#9A3B1E;--focus:#1F1D1A}}
*{{box-sizing:border-box}}
html{{background:var(--paper)}}
body{{margin:0;padding:40px clamp(16px,4vw,56px) 64px;font:15px/1.45 system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);font-variant-numeric:tabular-nums}}
::selection{{background:var(--ink);color:var(--paper)}}
h1{{font-size:clamp(26px,3vw,36px);line-height:1.1;letter-spacing:-0.02em;margin:0 0 10px;text-wrap:balance}}
.seeds{{display:flex;align-items:center;gap:8px;color:var(--mute);margin:0 0 6px;flex-wrap:wrap}}
.seed{{width:18px;height:18px;border-radius:50%;display:inline-block;border:1px solid rgba(0,0,0,.12)}}
.seeds code{{font-size:13px;margin-right:10px}}
.how{{margin:0 0 36px;color:var(--mute);max-width:70ch}}
.overview{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:0 0 32px}}
.card{{all:unset;display:flex;flex-direction:column;gap:10px;padding:12px 12px 14px;border-radius:10px;background:#F4F3EF;border:1px solid var(--line);cursor:pointer;transition:transform .18s cubic-bezier(.2,.8,.2,1),box-shadow .18s,border-color .18s}}
.card:hover,.card.hover{{transform:translateY(-2px);box-shadow:0 2px 4px rgba(0,0,0,.06),0 14px 28px -16px rgba(0,0,0,.3)}}
.card:focus-visible{{outline:2px solid var(--focus);outline-offset:3px}}
.card[aria-pressed="true"]{{border-color:var(--ink);box-shadow:inset 0 0 0 1px var(--ink)}}
.strip{{display:flex;height:34px;border-radius:6px;overflow:hidden}} .strip i{{display:block}}
.line{{display:flex;align-items:center;gap:8px}} .n{{font-weight:700;font-size:18px;letter-spacing:-0.02em}} .name{{font-weight:600;flex:1}}
.mark{{font-size:12px;font-weight:700;width:18px;height:18px;border-radius:50%;display:inline-grid;place-items:center;color:#fff}} .mark.ok{{background:var(--ok)}} .mark.warn{{background:var(--warn)}}
.blurb{{color:var(--mute);font-size:13px;line-height:1.35}}
.candidate{{display:grid;grid-template-columns:200px minmax(260px,1.1fr) minmax(420px,2fr);gap:28px;align-items:stretch;padding:28px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}
.candidate[hidden]{{display:none}}
.who{{display:flex;flex-direction:column}}
.num{{font-size:56px;line-height:1;font-weight:700;letter-spacing:-0.04em;margin:-6px 0 8px}}
.who h2{{font-size:20px;margin:0 0 4px;letter-spacing:-0.01em}}
.who p{{margin:0;color:var(--mute);max-width:26ch}}
.figures{{display:grid;grid-template-columns:auto auto;gap:2px 12px;margin:18px 0 0;font-size:13px}}
.figures dt{{color:var(--mute)}} .figures dd{{margin:0;font-weight:600}}
.verdict{{margin-top:auto !important;padding-top:14px;font-size:13px;font-weight:600}}
.verdict.ok{{color:var(--ok)}} .verdict.warn{{color:var(--warn)}}
.fields{{display:flex;flex-direction:column;border-radius:10px;overflow:hidden;min-height:300px;box-shadow:0 1px 2px rgba(0,0,0,.08),0 8px 24px -12px rgba(0,0,0,.25)}}
.field{{display:flex;justify-content:space-between;align-items:center;padding:0 16px;font-size:13px;min-height:28px}}
.field .role{{font-weight:600}} .field .hex{{font-family:ui-monospace,Consolas,monospace;font-size:12px;opacity:.85}}
.samples{{display:grid;grid-template-columns:16fr 7fr;gap:14px;align-items:start}}
figure{{margin:0;border-radius:8px;box-shadow:0 1px 2px rgba(0,0,0,.08),0 10px 28px -14px rgba(0,0,0,.3);overflow:hidden}}
.slide{{aspect-ratio:16/9;padding:5.5% 6%;display:flex;flex-direction:column;font-size:clamp(9px,0.9vw,13px)}}
.headline{{font-size:1.75em;font-weight:700;line-height:1.15;letter-spacing:-0.015em;margin:0 0 .9em;text-wrap:balance;max-width:24ch}}
.body{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.7em;flex:1;min-height:0}}
.panel{{border-radius:.4em;padding:.8em .9em;font-size:.95em}} .panel b{{display:block;margin-bottom:.25em}} .panel p{{margin:0;line-height:1.35}}
.chart{{display:flex;align-items:flex-end;gap:.5em}} .bar{{flex:1;border-radius:.2em .2em 0 0}}
.foot{{font-size:.8em;margin-top:.9em}}
.page{{aspect-ratio:1/1.414;padding:11% 10%;font-size:clamp(7px,0.62vw,10px);position:relative}}
.rule{{position:absolute;left:0;right:0;top:0;height:3.5%}}
.page h4{{margin:.6em 0 .5em;font-size:1.5em;letter-spacing:-0.01em}} .page p{{margin:0 0 .8em;line-height:1.45}}
.page table{{width:100%;border-collapse:collapse;margin:.4em 0}} .page th,.page td{{padding:.45em .5em;text-align:left}} .page th:not(:first-child),.page td:not(:first-child){{text-align:right}}
.caption{{font-size:.9em}}
.note{{margin:28px 0 0;color:var(--mute);max-width:70ch;font-size:13px}}
@media (max-width:1100px){{.candidate{{grid-template-columns:1fr 1fr}} .samples{{grid-column:1/-1}}}}
@media (max-width:640px){{.candidate{{grid-template-columns:1fr}} .samples{{grid-template-columns:1fr}} .page{{display:none}}}}
</style></head><body>
<h1>{escape(title)}</h1>
<p class="seeds">Seeds {seed_dots}</p>
<p class="how">{len(candidates)} palettes from the same seeds, one change each. Hover a card to preview it, click to pin it, use the arrow keys to move. The same slide and page are drawn for every palette. Then answer with the number of the one to use.</p>
<div class="overview" role="group" aria-label="palette candidates">{cards}</div>
{body}
<p class="note">{NOTE}</p>
<script>
(() => {{
  const cards = [...document.querySelectorAll('.card')];
  const details = [...document.querySelectorAll('.candidate')];
  let pinned = 1;
  const show = (n) => {{
    details.forEach(d => d.hidden = d.id !== 'd' + n);
    cards.forEach(c => c.classList.toggle('hover', c.dataset.index == n));
  }};
  const pin = (n) => {{
    pinned = n;
    cards.forEach(c => c.setAttribute('aria-pressed', c.dataset.index == n ? 'true' : 'false'));
    show(n);
  }};
  cards.forEach(c => {{
    c.addEventListener('mouseenter', () => show(c.dataset.index));
    c.addEventListener('focus', () => show(c.dataset.index));
    c.addEventListener('click', () => pin(Number(c.dataset.index)));
  }});
  document.querySelector('.overview').addEventListener('mouseleave', () => show(pinned));
  document.addEventListener('keydown', (e) => {{
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const next = e.key === 'ArrowRight' ? Math.min(cards.length, pinned + 1) : Math.max(1, pinned - 1);
    pin(next);
    cards[next - 1].focus();
  }});
}})();
</script>
</body></html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("candidates", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", default="Palette candidates")
    parser.add_argument("--open", action="store_true", help="open the page in the default browser")
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.candidates.read_text(encoding="utf-8"))
        html = render(document, args.title)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(html, encoding="utf-8", newline="\n")
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"schema": SCHEMA, "ok": False, "error": str(error)}, indent=2))
        return 1
    opened = bool(args.open and webbrowser.open(args.out.resolve().as_uri()))
    print(json.dumps({"schema": SCHEMA, "ok": True, "path": str(args.out), "opened": opened,
                      "candidates": len(document["candidates"]), "notice": NOTE}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
