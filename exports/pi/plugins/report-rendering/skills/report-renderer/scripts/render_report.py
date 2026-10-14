"""Original, dependency-free Markdown report presentation and confined publication."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import unicodedata
from urllib.parse import quote, unquote, urlsplit, urlunsplit


PROFILES = ("report", "naming", "review")
ASSETS = Path(__file__).resolve().parent.parent / "assets"
LIST = re.compile(r"^( *)([-+*]|\d+[.)])\s+(.*)$")
HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)\s*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
QUALIFIERS = ("unverified", "not screened")
SCORECARD_LABELS = {
    "criterion": {"criterion", "criteria", "criterio", "criteri", "critere", "criteres", "kriterium", "kriterien", "criterium", "criteria", "kryterium", "kriterium"},
    "weight": {"weight", "peso", "poids", "gewicht", "ponderacion", "ponderacao", "ponderazione", "waga", "vikt"},
    "overall": {"overall", "totale", "complessivo", "punteggio complessivo", "total", "global", "score global", "promedio general", "general", "gesamt", "gesamtwertung", "gesamtnote", "geral", "totaal", "totaalscore", "ocena laczna", "ocena łaczna", "sammanlagt"},
}
UNSCORED = {
    "not scored", "non valutato", "non valutata", "non assegnato", "non attribuito",
    "senza punteggio", "non calcolato", "non note", "non evalue", "no puntuado",
    "sin puntuacion", "no evaluado", "nao pontuado", "nao avaliado",
    "nicht bewertet", "nicht benotet", "niet beoordeeld", "nie oceniono",
    "ej poangsatt",
}


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def plain(value: str) -> str:
    """Strip only decoration recognized by the inline renderer."""
    value = re.sub(r"(`+)(.+?)\1", r"\2", value)
    value = re.sub(r"(\*\*|__)(\S(?:.*?\S)?)\1", r"\2", value)
    return re.sub(r"(?<!\w)([*_])(\S(?:.*?\S)?)\1(?!\w)", r"\2", value).strip()


def label_key(value: str) -> str:
    """Match documented labels without guessing the report's language."""
    value = unicodedata.normalize("NFKD", plain(value).casefold())
    return " ".join("".join(char for char in value if not unicodedata.combining(char)).split())


def unscored_label(value: str) -> str | None:
    value = re.sub(r"\s*\([^()]*\)\s*$", "", plain(value))
    return value if label_key(value) in UNSCORED else None


def safe_uri(uri: str, *, image: bool = False) -> bool:
    """Allow web references and relative URLs, never executable schemes."""
    if not uri or uri != uri.strip() or any(ord(char) < 32 or ord(char) == 127 for char in uri):
        return False
    if "\\" in uri or uri.startswith("//"):
        return False
    decoded = html.unescape(uri)
    if decoded != uri and (any(ord(char) < 32 for char in decoded) or re.match(r"\s*(?:javascript|vbscript|data|file|blob)\s*:", decoded, re.I)):
        return False
    try:
        parts = urlsplit(uri)
    except ValueError:
        return False
    if parts.scheme:
        if parts.scheme.lower() not in ({"http", "https"} if image else {"http", "https", "mailto"}):
            return False
        if parts.scheme.lower() in {"http", "https"} and not parts.netloc:
            return False
    elif re.match(r"^[^/?#]*:", uri):
        return False
    return not parts.netloc or bool(parts.scheme)


def table_cells(line: str) -> list[str]:
    """Split pipes while retaining escaped pipes and inline-code pipes."""
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    cells: list[str] = []
    current: list[str] = []
    index = 0
    code = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            current.extend(text[index:index + 2])
            index += 2
            continue
        if char == "`":
            end = index
            while end < len(text) and text[end] == "`":
                end += 1
            count = end - index
            if not code:
                code = count
            elif code == count:
                code = 0
            current.append(text[index:end])
            index = end
            continue
        if char == "|" and not code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return cells


def separator(line: str) -> bool:
    cells = table_cells(line)
    return "|" in line and len(cells) > 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


class MarkdownRenderer:
    def __init__(self, profile: str, source_dir: Path | None = None, output_dir: Path | None = None):
        self.profile = profile
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.headings: list[tuple[int, str, str]] = []
        self.anchors: set[str] = set()
        self.table_number = 0
        self.scorecard_number = 0
        self.section = "Report"

    def uri(self, value: str, *, image: bool = False) -> str | None:
        if not safe_uri(value, image=image):
            return None
        parts = urlsplit(value)
        if parts.scheme or not parts.path or self.source_dir is None or self.output_dir is None:
            return value
        # No referenced file is read. Only the reference's browser-relative base changes.
        target = self.source_dir / unquote(parts.path)
        try:
            relative = os.path.relpath(target, self.output_dir).replace(os.sep, "/")
        except ValueError:
            return None
        path = quote(relative, safe="/~!$&'()*+,;=@-")
        return urlunsplit(("", "", path, parts.query, parts.fragment))

    def inline(self, text: str, depth: int = 0) -> str:
        if depth > 20:
            return escape(text)
        output: list[str] = []
        index = 0
        while index < len(text):
            if text[index] == "\\" and index + 1 < len(text) and text[index + 1] in r"\`*_{}[]()#+-.!|>":
                output.append(escape(text[index + 1]))
                index += 2
                continue
            if text[index] == "`":
                match = re.match(r"`+", text[index:])
                marker = match.group(0)
                end = text.find(marker, index + len(marker))
                if end >= 0:
                    output.append("<code>" + escape(text[index + len(marker):end]) + "</code>")
                    index = end + len(marker)
                    continue
            image = text.startswith("![", index)
            start = index + 1 if image else index
            if text[start:start + 1] == "[":
                link = self.link(text, start)
                if link is not None:
                    end, label, destination, title = link
                    href = self.uri(destination, image=image)
                    raw = text[index:end]
                    if href is None:
                        output.append(escape(raw) if image else '<span class="unsafe-link">' + self.inline(label, depth + 1) + " [" + escape(destination) + "]</span>")
                    else:
                        title_attr = ' title="' + escape(title) + '"' if title else ""
                        if image:
                            output.append('<img src="' + escape(href) + '" alt="' + escape(plain(label)) + '" loading="lazy"' + title_attr + ">")
                        else:
                            output.append('<a href="' + escape(href) + '"' + title_attr + ">" + self.inline(label, depth + 1) + "</a>")
                    index = end
                    continue
            matched = False
            for marker, tag in (("**", "strong"), ("__", "strong"), ("*", "em"), ("_", "em")):
                if not text.startswith(marker, index):
                    continue
                if marker.startswith("_") and index and text[index - 1].isalnum():
                    continue
                end = text.find(marker, index + len(marker))
                if end > index + len(marker):
                    content = text[index + len(marker):end]
                    if not content.startswith(" ") and not content.endswith(" "):
                        output.append("<" + tag + ">" + self.inline(content, depth + 1) + "</" + tag + ">")
                        index = end + len(marker)
                        matched = True
                        break
            if matched:
                continue
            output.append(escape(text[index]))
            index += 1
        return "".join(output)

    @staticmethod
    def link(text: str, start: int) -> tuple[int, str, str, str] | None:
        """Parse balanced inline links; unsupported reference links stay visible."""
        cursor = start + 1
        depth = 1
        while cursor < len(text):
            if text[cursor] == "\\":
                cursor += 2
                continue
            if text[cursor] == "[":
                depth += 1
            if text[cursor] == "]":
                depth -= 1
                if depth == 0:
                    break
            cursor += 1
        if cursor + 1 >= len(text) or text[cursor + 1] != "(":
            return None
        label = text[start + 1:cursor]
        dest_start = cursor + 2
        cursor = dest_start
        depth = 1
        in_angle = False
        while cursor < len(text):
            char = text[cursor]
            if char == "\\":
                cursor += 2
                continue
            if char == "<":
                in_angle = True
            elif char == ">":
                in_angle = False
            elif char == "(" and not in_angle:
                depth += 1
            elif char == ")" and not in_angle:
                depth -= 1
                if depth == 0:
                    break
            cursor += 1
        if depth:
            return None
        value = text[dest_start:cursor].strip()
        match = re.fullmatch(r'(?:<([^<>]*)>|(\S+?))(?:\s+["\'](.*)["\'])?', value)
        if match is None:
            return None
        return cursor + 1, label, match.group(1) if match.group(1) is not None else match.group(2), match.group(3) or ""

    def heading(self, level: int, title: str) -> str:
        label = plain(title)
        anchor = re.sub(r"[^\w-]+", "-", label.lower(), flags=re.UNICODE).strip("-") or "section"
        unique = anchor
        suffix = 2
        while unique in self.anchors:
            unique = anchor + "-" + str(suffix)
            suffix += 1
        self.anchors.add(unique)
        self.headings.append((level, unique, label))
        if level <= 2:
            self.section = label
        return f'<h{level} id="{escape(unique)}">{self.inline(title)}</h{level}>'

    @staticmethod
    def score(value: str) -> tuple[str | None, list[str]]:
        value = plain(value)
        match = re.fullmatch(r"([1-5])(?:\s*\(([^()]*)\))?", value)
        # Preserve the report's qualifier wording, including translated uncertainty.
        qualifier = re.search(r"\(([^()]*)\)\s*$", value)
        qualifiers = [qualifier.group(1)] if qualifier and qualifier.group(1) else []
        if not qualifiers:
            qualifiers = [item for item in QUALIFIERS if item in value.lower()]
        return (match.group(1) if match else None), qualifiers

    def scorecard(self, header: list[str], rows: list[list[str]]) -> bool:
        if self.profile != "naming" or len(header) < 3 or label_key(header[0]) not in SCORECARD_LABELS["criterion"] or label_key(header[1]) not in SCORECARD_LABELS["weight"]:
            return False
        if len(rows) < 2 or label_key(rows[-1][0]) not in SCORECARD_LABELS["overall"]:
            return False
        if len(rows[-1]) != len(header) or any(re.fullmatch(r"(?:[1-4](?:\.\d+)?|5(?:\.0+)?)(?:\s*\([^()]*\))?", plain(cell)) is None and unscored_label(cell) is None for cell in rows[-1][2:]):
            return False
        for row in rows[:-1]:
            if len(row) != len(header) or label_key(row[0]) in SCORECARD_LABELS["overall"]:
                return False
            weight = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", plain(row[1]))
            if weight is None or float(weight.group(1)) > 100:
                return False
            if any(self.score(cell)[0] is None and unscored_label(cell) is None for cell in row[2:]):
                return False
        return len(rows[-1]) == len(header)

    def table(self, header: list[str], rows: list[list[str]]) -> str:
        self.table_number += 1
        number = self.table_number
        naming = self.scorecard(header, rows)
        if naming:
            self.scorecard_number += 1
        label = f"{self.section}, table {number}"
        unscored = next((unscored_label(cell) for row in rows for cell in row[2:] if unscored_label(cell) is not None), "not scored")
        out = [f'<div class="table-block"' + (' data-scorecard="true" data-unscored="' + escape(unscored) + '"' if naming else "") + ">"]
        out.append(f'<div class="table-controls" hidden><label for="filter-{number}">Filter rows <input id="filter-{number}" type="search" aria-label="Filter {escape(label)}"></label><output for="filter-{number}" role="status"></output></div>')
        if naming:
            out.append('<div class="score-controls" hidden><button type="button">Reset weights</button><p role="status" aria-live="polite">Explore weights locally. Original recommendation and evidence remain unchanged.</p></div>')
        out.append(f'<div class="table-scroll" role="region" aria-label="{escape(label)}" tabindex="0"><table><thead><tr>')
        for cell in header:
            out.append('<th scope="col">' + self.inline(cell) + "</th>")
        out.append("</tr></thead><tbody>")
        for index, row in enumerate(rows):
            overall = naming and index == len(rows) - 1
            out.append("<tr" + (" data-overall-row" if overall else " data-score-row" if naming else "") + ">")
            for column, cell in enumerate(row):
                attr = ""
                content = self.inline(cell)
                if naming and column >= 2:
                    score, qualifiers = self.score(cell)
                    attr += ' data-qualifiers="' + escape(json.dumps(qualifiers, ensure_ascii=False)) + '"'
                    if overall:
                        attr += f' data-overall="{column - 2}"'
                    elif score is not None:
                        attr += ' data-score="' + score + '"'
                if naming and column == 1 and not overall:
                    value = re.match(r"\d+(?:\.\d+)?", plain(cell)).group(0)
                    content = '<span class="original-weight">' + content + '</span><label class="weight-editor" hidden>Explore <input type="number" min="0" max="100" step="any" data-weight value="' + value + '" aria-label="Weight for ' + escape(plain(row[0])) + '"> %</label>'
                out.append("<td" + attr + ">" + content + "</td>")
            out.append("</tr>")
        out.append("</tbody></table></div></div>")
        return "".join(out)

    def list_block(self, lines: list[str], start: int) -> tuple[str, int]:
        initial = LIST.match(lines[start])
        indent = len(initial.group(1))
        ordered = initial.group(2)[0].isdigit()
        tag = "ol" if ordered else "ul"
        start_attr = f' start="{int(initial.group(2)[:-1])}"' if ordered else ""
        out = ["<" + tag + start_attr + ">"]
        index = start
        while index < len(lines):
            match = LIST.match(lines[index])
            if match is None or len(match.group(1)) != indent or match.group(2)[0].isdigit() != ordered:
                break
            first = match.group(3)
            index += 1
            continuation: list[str] = []
            while index < len(lines):
                line = lines[index]
                if not line.strip():
                    look = index + 1
                    while look < len(lines) and not lines[look].strip():
                        look += 1
                    if look < len(lines) and (len(lines[look]) - len(lines[look].lstrip(" ")) > indent or (LIST.match(lines[look]) is not None and len(LIST.match(lines[look]).group(1)) == indent)):
                        continuation.append("")
                        index += 1
                        continue
                    break
                leading = len(line) - len(line.lstrip(" "))
                if leading <= indent:
                    break
                continuation.append(line)
                index += 1
            amount = min((len(line) - len(line.lstrip(" ")) for line in continuation if line.strip()), default=indent + 2)
            children = [line[amount:] if line.strip() else "" for line in continuation]
            task = re.match(r"^\[([ xX])\]\s*(.*)$", first)
            if task:
                checked = " checked" if task.group(1).lower() == "x" else ""
                out.append('<li class="task-item"><label><input type="checkbox"' + checked + ">" + self.inline(task.group(2)) + "</label>" + self.blocks(children) + "</li>")
            else:
                out.append("<li>" + self.blocks([first, *children]) + "</li>")
        out.append("</" + tag + ">")
        return "".join(out), index

    @staticmethod
    def block_start(lines: list[str], index: int) -> bool:
        line = lines[index]
        if not line.strip() or HEADING.match(line) or FENCE.match(line) or LIST.match(line) or re.match(r"^ {0,3}>", line) or re.fullmatch(r" {0,3}(?:\*\s*){3,}| {0,3}(?:-\s*){3,}| {0,3}(?:_\s*){3,}", line):
            return True
        return index + 1 < len(lines) and (separator(lines[index + 1]) or re.fullmatch(r" {0,3}(?:=+|-+)\s*", lines[index + 1]) is not None)

    def blocks(self, lines: list[str], *, top: bool = False) -> str:
        out: list[str] = []
        index = 0
        name_open = False
        while index < len(lines):
            line = lines[index]
            if not line.strip():
                index += 1
                continue
            heading = HEADING.match(line)
            if heading:
                level = len(heading.group(1))
                if top and name_open and level <= 3:
                    out.append("</details>")
                    name_open = False
                name_section = self.profile == "naming" and ("top 3" in self.section.lower() or "runners" in self.section.lower())
                # Only ATX headings have closing markers. Setext title text is literal.
                title = re.sub(r"\s+#+\s*$", "", heading.group(2))
                rendered = self.heading(level, title)
                if top and name_section and level == 3:
                    out.append('<details class="name-block" open><summary>' + rendered + "</summary>")
                    name_open = True
                else:
                    out.append(rendered)
                index += 1
                continue
            fence = FENCE.match(line)
            if fence:
                marker = fence.group(1)
                info = fence.group(2).strip()
                index += 1
                code: list[str] = []
                while index < len(lines) and re.fullmatch(r" {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}\s*", lines[index]) is None:
                    code.append(lines[index])
                    index += 1
                if index < len(lines):
                    index += 1
                language = info.split()[0] if info else ""
                caption = '<p class="code-language">' + escape(info) + (' (source)' if language.lower() == "mermaid" else "") + "</p>" if info else ""
                out.append(caption + '<pre><code' + (' class="language-' + escape(language) + '"' if language else "") + ">" + escape("\n".join(code)) + "</code></pre>")
                continue
            if index + 1 < len(lines) and separator(lines[index + 1]):
                header = table_cells(line)
                if len(header) == len(table_cells(lines[index + 1])):
                    index += 2
                    rows: list[list[str]] = []
                    while index < len(lines) and lines[index].strip() and "|" in lines[index]:
                        row = table_cells(lines[index])
                        # Keep malformed extra cells, rather than truncating evidence.
                        rows.append(row)
                        index += 1
                    out.append(self.table(header, rows))
                    continue
            if index + 1 < len(lines) and re.fullmatch(r" {0,3}(?:=+|-+)\s*", lines[index + 1]):
                out.append(self.heading(1 if lines[index + 1].lstrip().startswith("=") else 2, line.strip()))
                index += 2
                continue
            if re.fullmatch(r" {0,3}(?:\*\s*){3,}| {0,3}(?:-\s*){3,}| {0,3}(?:_\s*){3,}", line):
                out.append("<hr>")
                index += 1
                continue
            if LIST.match(line):
                rendered, index = self.list_block(lines, index)
                out.append(rendered)
                continue
            if re.match(r"^ {0,3}>", line):
                quote_lines: list[str] = []
                while index < len(lines) and re.match(r"^ {0,3}>", lines[index]):
                    quote_lines.append(re.sub(r"^ {0,3}> ?", "", lines[index]))
                    index += 1
                out.append("<blockquote>" + self.blocks(quote_lines) + "</blockquote>")
                continue
            paragraph = [line]
            index += 1
            while index < len(lines) and not self.block_start(lines, index):
                paragraph.append(lines[index])
                index += 1
            out.append("<p>" + "<br>\n".join(self.inline(item) for item in paragraph) + "</p>")
        if name_open:
            out.append("</details>")
        return "\n".join(out)


def _render(markdown: str, profile: str, source_name: str, source_dir: Path | None = None, output_dir: Path | None = None) -> str:
    if profile not in PROFILES:
        raise ValueError("unknown report profile: " + profile)
    source = markdown.encode("utf-8")
    encoded = base64.b64encode(source).decode("ascii")
    digest = hashlib.sha256(source).hexdigest()
    css = (ASSETS / "report.css").read_text(encoding="utf-8")
    javascript = (ASSETS / "report.js").read_text(encoding="utf-8")
    style_hash = base64.b64encode(hashlib.sha256(css.encode("utf-8")).digest()).decode("ascii")
    script_hash = base64.b64encode(hashlib.sha256(javascript.encode("utf-8")).digest()).decode("ascii")
    renderer = MarkdownRenderer(profile, source_dir, output_dir)
    content = renderer.blocks(markdown.removeprefix("\ufeff").expandtabs(4).splitlines(), top=True)
    if profile == "naming" and not renderer.scorecard_number:
        content += '\n<p class="render-note" role="status">Weight exploration is unavailable: no supported canonical Scorecard was identified. The complete original report remains visible.</p>'
    title = next((heading[2] for heading in renderer.headings if heading[0] == 1), source_name)
    contents = "".join(f'<li class="level-{level}"><a href="#{escape(anchor)}">{escape(label)}</a></li>' for level, anchor, label in renderer.headings)
    policy = f"default-src 'none'; script-src 'sha256-{script_hash}'; style-src 'sha256-{style_hash}'; img-src 'self' https: http:; base-uri 'none'; form-action 'none'"
    return f'''<!doctype html>
<html lang="und"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="{escape(policy)}"><title>{escape(title)}</title><style>{css}</style></head>
<body data-profile="{profile}"><a class="skip-link" href="#report">Skip to report</a><div class="page">
<header class="masthead"><p class="wordmark">Daodan · report view</p><p>{escape(source_name)}</p></header>
<div class="layout"><nav aria-label="Report contents"><details open><summary>Contents</summary><ul>{contents}</ul></details></nav>
<main id="report">{content}
<details class="source-panel"><summary>Markdown source</summary><p>Source: {escape(source_name)}<br>SHA-256: <code>{digest}</code></p><p><a id="download-source" download="{escape(Path(source_name).name)}" href="data:text/plain;charset=utf-8;base64,{encoded}">Download original Markdown</a></p><pre><code>{escape(markdown)}</code></pre></details>
</main></div></div><script id="report-source" type="text/plain" data-encoding="base64">{encoded}</script><script>{javascript}</script></body></html>
'''


def render_report(markdown: str, profile: str = "report", source_name: str = "report.md") -> str:
    """Render a report without filesystem writes or remote reads."""
    return _render(markdown, profile, source_name)


def checked_path(path: Path, *, allow_missing: bool = True) -> Path:
    """Reject links/reparse points, including ancestry above the explicit root."""
    if ".." in path.parts:
        raise ValueError("path traversal is not allowed: " + str(path))
    candidate = path.absolute()
    if os.name == "nt" and any(":" in part for part in candidate.parts[1:]):
        raise ValueError("alternate data streams are not allowed: " + str(path))
    for item in (candidate, *candidate.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            if item == candidate and not allow_missing:
                raise ValueError("path does not exist: " + str(path))
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise ValueError("symlink or reparse point is not allowed: " + str(item))
    return candidate


def publish(input_path: Path, output_path: Path, root_path: Path, profile: str, *, force: bool = False) -> Path:
    source = checked_path(input_path, allow_missing=False)
    root = checked_path(root_path)
    output = checked_path(output_path)
    if not source.is_file():
        raise ValueError("input must be an ordinary file")
    if root.exists() and not root.is_dir():
        raise ValueError("output root must be a directory")
    if output == root or not output.is_relative_to(root):
        raise ValueError("output must stay inside the explicit root")
    if output == source or (output.exists() and os.path.samefile(output, source)):
        raise ValueError("output cannot overwrite the Markdown source")
    if output.exists() and not force:
        raise ValueError("output already exists; use --force to replace this rendered view")
    if output.exists() and not output.is_file():
        raise ValueError("output must be an ordinary file")
    markdown = source.read_bytes().decode("utf-8")
    document = _render(markdown, profile, str(source), source.parent, output.parent)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Repeat ancestry checks after directory creation and before publication.
    checked_path(root, allow_missing=False)
    checked_path(output)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=".report-render-", suffix=".tmp", dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(document.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        if output.exists() and not force:
            raise ValueError("output was created during rendering; replacement requires --force")
        checked_path(output)
        if output.exists() and os.path.samefile(output, source):
            raise ValueError("output cannot overwrite the Markdown source")
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="authoritative UTF-8 Markdown file")
    parser.add_argument("--output", required=True, type=Path, help="HTML file inside the owned output root")
    parser.add_argument("--root", required=True, type=Path, help="explicit dedicated output boundary")
    parser.add_argument("--profile", choices=PROFILES, default="report")
    parser.add_argument("--force", action="store_true", help="explicitly replace an existing rendered view")
    args = parser.parse_args(argv)
    try:
        output = publish(args.input, args.output, args.root, args.profile, force=args.force)
    except (OSError, UnicodeError, ValueError) as error:
        print("Report rendering failed: " + str(error), file=sys.stderr)
        return 1
    print("Rendered report: " + str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
