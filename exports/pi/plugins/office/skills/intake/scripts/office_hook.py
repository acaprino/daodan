"""Prompt hook: point a Word, PowerPoint or Excel request at the Daodan Office entries."""

from __future__ import annotations

import json
import re
import sys

sys.dont_write_bytecode = True

OFFICE = re.compile(
    r"\b(?:pptx|potx|docx|dotx|xlsx|xlsm|xltx|power ?point|excel|spreadsheets?|workbooks?|"
    r"slides?|decks?|presentations?|presentazion[ei]|word document|documento word|file word|"
    r"foglio? di calcolo)\b",
    re.IGNORECASE,
)

CONTEXT = (
    "This prompt involves a Word, PowerPoint or Excel file. Use the Daodan Office entries "
    "(start, presentation, document, workbook, verify, fix, theme): they run the interview, the content "
    "and design proposals, the build and the independent review, and an existing file keeps its own look. "
    "Do not ask the user about tools: a missing engine is installed by the entry's own recovery. Do not build "
    "the file with a generic library or skill such as python-pptx, python-docx or openpyxl, and install no "
    "package to do it. If those entries are unavailable, report the missing provider instead of substituting."
)


def hook(payload: dict) -> dict | None:
    prompt = payload.get("prompt")
    if payload.get("hook_event_name") != "UserPromptSubmit" or not isinstance(prompt, str):
        return None
    if not OFFICE.search(prompt):
        return None
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": CONTEXT}}


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read(1_048_577))
    except ValueError:
        return 0
    result = hook(payload) if isinstance(payload, dict) else None
    if result:
        print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
