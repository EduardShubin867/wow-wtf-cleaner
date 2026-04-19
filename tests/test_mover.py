"""Tests for wow_wtf_cleaner.core.mover."""

from __future__ import annotations

from pathlib import Path

from wow_wtf_cleaner.core.models import OrphanReport
from wow_wtf_cleaner.core.mover import apply_move


class TestApplyMove:
    def test_moves_files_and_preserves_structure(self, tmp_path: Path) -> None:
        wow = tmp_path / "_retail_"
        sv_dir = wow / "WTF" / "Account" / "Acc1" / "SavedVariables"
        sv_dir.mkdir(parents=True)
        (sv_dir / "Orphan.lua").write_text("data", encoding="utf-8")
        (sv_dir / "Orphan.lua.bak").write_text("data.bak", encoding="utf-8")

        report = OrphanReport(
            label="account:Acc1",
            src_dir=sv_dir,
            files=["Orphan.lua", "Orphan.lua.bak"],
            total_bytes=10,
        )

        logs: list[str] = []
        backup_root = apply_move(wow, [report], logs.append, lang="ru")

        # Source files must be gone from the original location
        assert not (sv_dir / "Orphan.lua").exists()
        assert not (sv_dir / "Orphan.lua.bak").exists()

        # Backup must mirror path structure relative to wow root
        expected = backup_root / "WTF" / "Account" / "Acc1" / "SavedVariables"
        assert (expected / "Orphan.lua").exists()
        assert (expected / "Orphan.lua.bak").exists()
        assert (expected / "Orphan.lua").read_text(encoding="utf-8") == "data"

        # Backup folder lives inside _retail_
        assert backup_root.parent == wow
        assert backup_root.name.startswith("WTF-orphans-")

    def test_logs_progress(self, tmp_path: Path) -> None:
        wow = tmp_path / "_retail_"
        sv_dir = wow / "WTF" / "Account" / "Acc1" / "SavedVariables"
        sv_dir.mkdir(parents=True)
        (sv_dir / "X.lua").write_text("x")

        report = OrphanReport("account:Acc1", sv_dir, ["X.lua"], 1)

        logs: list[str] = []
        apply_move(wow, [report], logs.append, lang="ru")

        assert any("account:Acc1" in line for line in logs)
        assert any("перемещено" in line.lower() for line in logs)

    def test_missing_source_file_logs_but_does_not_crash(self, tmp_path: Path) -> None:
        wow = tmp_path / "_retail_"
        sv_dir = wow / "WTF" / "Account" / "Acc1" / "SavedVariables"
        sv_dir.mkdir(parents=True)
        # File is listed in the report but missing on disk
        report = OrphanReport("account:Acc1", sv_dir, ["Ghost.lua"], 0)

        logs: list[str] = []
        backup_root = apply_move(wow, [report], logs.append, lang="ru")

        # Do not crash — log the failure instead
        assert any("не удалось переместить" in line for line in logs)
        # Backup folder is still created
        assert backup_root.exists()

    def test_empty_reports_does_not_crash(self, tmp_path: Path) -> None:
        wow = tmp_path / "_retail_"
        wow.mkdir()
        backup = apply_move(wow, [], lambda _: None)
        # No backup folder should appear when there is nothing to move — here
        # it is only created after the first report, so for an empty list we
        # just return a path that was never mkdir'd.
        assert backup.parent == wow
