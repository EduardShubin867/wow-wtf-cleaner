"""Small formatting helpers and shared regexes."""

from __future__ import annotations

import re


SV_EXT_RE = re.compile(r"\.lua(\.bak)?$", re.IGNORECASE)
"""Matches `.lua` and `.lua.bak` at the end of a filename."""


def strip_sv_ext(name: str) -> str:
    """`Bartender4.lua.bak` -> `Bartender4`. Returns unchanged if no extension."""
    return SV_EXT_RE.sub("", name)


def fmt_bytes(n: int) -> str:
    """Human-readable size: B / KB / MB."""
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 / 1024:.2f} MB"
