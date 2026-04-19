"""Parser for add-on `.toc` files — extracts `## SavedVariables:` lines."""

from __future__ import annotations

import re
from pathlib import Path


TOC_KEY_RE = re.compile(r"^##\s*([^:]+):\s*(.*)$")


def parse_toc(toc_path: Path) -> tuple[set[str], set[str]]:
    """Returns (SavedVariables, SavedVariablesPerCharacter).

    If the file is unreadable or empty, returns two empty sets.
    Declarations may span multiple lines or list several comma-separated names:
    `## SavedVariables: Foo, Bar, Baz`.
    """
    sv: set[str] = set()
    svpc: set[str] = set()
    try:
        text = toc_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return sv, svpc

    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("##"):
            continue
        match = TOC_KEY_RE.match(line)
        if not match:
            continue
        key = match.group(1).strip().lower()
        values = [v.strip() for v in match.group(2).split(",") if v.strip()]
        if key == "savedvariables":
            sv.update(values)
        elif key == "savedvariablespercharacter":
            svpc.update(values)

    return sv, svpc
