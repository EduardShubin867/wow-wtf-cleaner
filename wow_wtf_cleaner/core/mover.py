"""Move matched files into a timestamped backup folder."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

from wow_wtf_cleaner.core.models import OrphanReport
from wow_wtf_cleaner.i18n import Lang, detect_system_lang, tr


def apply_move(
    wow_root: Path,
    reports: Sequence[OrphanReport],
    log: Callable[[str], None],
    *,
    lang: Lang | None = None,
) -> Path:
    """Moves files from all reports into `<wow_root>/WTF-orphans-<timestamp>/`.

    Paths inside the backup folder mirror the originals relative to `wow_root`,
    so you can roll back by copying the backup tree back into `wow_root`.

    Returns the path to the created backup folder.
    """
    resolved = lang if lang is not None else detect_system_lang()
    timestamp = datetime.now().isoformat(timespec="seconds").replace(":", "-")
    backup_root = wow_root / f"WTF-orphans-{timestamp}"

    for report in reports:
        rel = report.src_dir.relative_to(wow_root)
        dest = backup_root / rel
        dest.mkdir(parents=True, exist_ok=True)
        for name in report.files:
            src = report.src_dir / name
            try:
                shutil.move(str(src), str(dest / name))
            except OSError as e:
                log(
                    tr(
                        resolved,
                        "mover.move_failed",
                        src=src,
                        err=e,
                    )
                )
        log(
            tr(
                resolved,
                "mover.moved_to",
                label=report.label,
                dest=dest,
            )
        )

    return backup_root
