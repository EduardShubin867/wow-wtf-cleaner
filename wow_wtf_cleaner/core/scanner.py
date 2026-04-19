"""WTF scan: gather installed add-ons and find orphaned SV files."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from wow_wtf_cleaner.core.formatting import SV_EXT_RE, fmt_bytes, strip_sv_ext
from wow_wtf_cleaner.core.models import AddonMeta, OrphanReport, ScanResult
from wow_wtf_cleaner.core.toc import parse_toc
from wow_wtf_cleaner.i18n import Lang, detect_system_lang, tr


def collect_installed_addons(addons_dir: Path) -> list[AddonMeta]:
    """Reads `Interface/AddOns/` and collects metadata for each add-on.

    Skips built-in modules (`Blizzard_*`) — they do not write SavedVariables.
    """
    if not addons_dir.is_dir():
        return []

    result: list[AddonMeta] = []
    for entry in addons_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("Blizzard_"):
            continue

        meta = AddonMeta(folder=entry.name)
        # An add-on folder may contain several .toc files for different game
        # versions (Mainline, TBC, Wrath, etc.) — merge declarations from all.
        for f in entry.iterdir():
            if f.is_file() and f.suffix.lower() == ".toc":
                sv, svpc = parse_toc(f)
                meta.saved_vars.update(sv)
                meta.saved_vars_per_char.update(svpc)
        result.append(meta)
    return result


def build_known_names(addons: list[AddonMeta]) -> set[str]:
    """Builds the set of "current" names: folder names plus declared variables.

    Everything lowercased for case-insensitive comparison (Windows FS, YOLO).
    """
    known: set[str] = set()
    for addon in addons:
        known.add(addon.folder.lower())
        known.update(v.lower() for v in addon.saved_vars)
        known.update(v.lower() for v in addon.saved_vars_per_char)
    return known


def scan_sv_dir(directory: Path, known: set[str]) -> list[str]:
    """Returns basenames of `.lua`/`.lua.bak` files in `directory` not in `known`."""
    if not directory.is_dir():
        return []

    orphans: list[str] = []
    for entry in directory.iterdir():
        if not entry.is_file() or not SV_EXT_RE.search(entry.name):
            continue
        if strip_sv_ext(entry.name).lower() not in known:
            orphans.append(entry.name)
    return orphans


def dir_size(directory: Path, files: list[str]) -> int:
    """Total size of the listed files inside the directory."""
    total = 0
    for f in files:
        try:
            total += (directory / f).stat().st_size
        except OSError:
            pass
    return total


def scan(
    wow_root: Path,
    log: Callable[[str], None],
    *,
    lang: Lang | None = None,
) -> ScanResult:
    """Full pass over all SavedVariables: account-level and per-character.

    Layout we walk:
        <wow_root>/WTF/Account/<ACC>/SavedVariables/*.lua
        <wow_root>/WTF/Account/<ACC>/<Realm>/<Character>/SavedVariables/*.lua
    """
    resolved = lang if lang is not None else detect_system_lang()

    addons_dir = wow_root / "Interface" / "AddOns"
    wtf_account_dir = wow_root / "WTF" / "Account"

    if not addons_dir.is_dir() or not wtf_account_dir.is_dir():
        raise FileNotFoundError(
            tr(
                resolved,
                "scan.missing_dirs",
                addons_dir=addons_dir,
                wtf_dir=wtf_account_dir,
            )
        )

    addons = collect_installed_addons(addons_dir)
    known = build_known_names(addons)
    log(tr(resolved, "scan.installed_addons", count=len(addons)))
    log(tr(resolved, "scan.known_names", count=len(known)))
    log("")

    reports: list[OrphanReport] = []

    def _maybe_collect(label: str, directory: Path) -> None:
        orphans = scan_sv_dir(directory, known)
        if not orphans:
            return
        size = dir_size(directory, orphans)
        reports.append(OrphanReport(label, directory, orphans, size))
        log(
            tr(
                resolved,
                "scan.orphans_line",
                label=label,
                count=len(orphans),
                size=fmt_bytes(size),
            )
        )

    for acc in sorted(wtf_account_dir.iterdir()):
        if not acc.is_dir() or acc.name == "SavedVariables":
            continue

        # Account-level SV
        _maybe_collect(f"account:{acc.name}", acc / "SavedVariables")

        # Per-character SV
        for realm in sorted(acc.iterdir()):
            if not realm.is_dir() or realm.name == "SavedVariables":
                continue
            for char in sorted(realm.iterdir()):
                if not char.is_dir():
                    continue
                _maybe_collect(
                    f"char:{acc.name}/{realm.name}/{char.name}",
                    char / "SavedVariables",
                )

    return ScanResult(len(addons), len(known), reports)
