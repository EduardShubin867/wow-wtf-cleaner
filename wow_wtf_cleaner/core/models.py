"""Dataclasses passed between application layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AddonMeta:
    """Metadata for one installed add-on, extracted from its .toc files."""

    folder: str
    saved_vars: set[str] = field(default_factory=set)
    saved_vars_per_char: set[str] = field(default_factory=set)


@dataclass
class OrphanReport:
    """Orphan files found in a specific SavedVariables directory."""

    label: str
    src_dir: Path
    files: list[str]
    total_bytes: int


@dataclass
class ScanResult:
    """Result of one full WTF scan."""

    addons_count: int
    known_names_count: int
    reports: list[OrphanReport]

    @property
    def total_files(self) -> int:
        return sum(len(r.files) for r in self.reports)

    @property
    def total_bytes(self) -> int:
        return sum(r.total_bytes for r in self.reports)
