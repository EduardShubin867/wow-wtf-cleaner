"""Tests for wow_wtf_cleaner.core.scanner."""

from __future__ import annotations

from pathlib import Path

from wow_wtf_cleaner.core.scanner import (
    build_known_names,
    collect_installed_addons,
    dir_size,
    scan,
    scan_sv_dir,
)


# ---------- fixtures helpers ------------------------------------------------


def _make_addon(
    addons_dir: Path,
    folder: str,
    *,
    sv: list[str] | None = None,
    svpc: list[str] | None = None,
) -> None:
    """Create a minimal addon with a .toc under addons_dir/<folder>/."""
    addon_dir = addons_dir / folder
    addon_dir.mkdir(parents=True)
    toc_lines = [f"## Title: {folder}", "## Interface: 110000"]
    if sv:
        toc_lines.append(f"## SavedVariables: {', '.join(sv)}")
    if svpc:
        toc_lines.append(f"## SavedVariablesPerCharacter: {', '.join(svpc)}")
    (addon_dir / f"{folder}.toc").write_text("\n".join(toc_lines) + "\n", encoding="utf-8")


def _make_sv_file(sv_dir: Path, name: str, content: str = "{}") -> None:
    sv_dir.mkdir(parents=True, exist_ok=True)
    (sv_dir / name).write_text(content, encoding="utf-8")


# ---------- collect_installed_addons ---------------------------------------


class TestCollectInstalledAddons:
    def test_empty_dir(self, tmp_path: Path) -> None:
        assert collect_installed_addons(tmp_path) == []

    def test_missing_dir(self, tmp_path: Path) -> None:
        assert collect_installed_addons(tmp_path / "nope") == []

    def test_collects_declarations(self, tmp_path: Path) -> None:
        _make_addon(tmp_path, "Bartender4", sv=["BT4Data"])
        _make_addon(tmp_path, "Details", sv=["Details_Global"], svpc=["Details_Char"])

        addons = {a.folder: a for a in collect_installed_addons(tmp_path)}

        assert set(addons.keys()) == {"Bartender4", "Details"}
        assert addons["Bartender4"].saved_vars == {"BT4Data"}
        assert addons["Details"].saved_vars == {"Details_Global"}
        assert addons["Details"].saved_vars_per_char == {"Details_Char"}

    def test_skips_blizzard_prefix(self, tmp_path: Path) -> None:
        _make_addon(tmp_path, "Bartender4", sv=["BT4"])
        _make_addon(tmp_path, "Blizzard_Communities")
        _make_addon(tmp_path, "Blizzard_AuctionHouseUI")

        addons = collect_installed_addons(tmp_path)
        assert [a.folder for a in addons] == ["Bartender4"]

    def test_merges_multiple_tocs_in_one_addon(self, tmp_path: Path) -> None:
        # Addon ships multiple .toc files for different clients (Mainline / Classic)
        folder = tmp_path / "MultiVer"
        folder.mkdir()
        (folder / "MultiVer-Mainline.toc").write_text(
            "## SavedVariables: RetailDB\n", encoding="utf-8"
        )
        (folder / "MultiVer-Cata.toc").write_text(
            "## SavedVariables: CataDB\n", encoding="utf-8"
        )

        addons = collect_installed_addons(tmp_path)
        assert len(addons) == 1
        assert addons[0].saved_vars == {"RetailDB", "CataDB"}

    def test_ignores_non_directories(self, tmp_path: Path) -> None:
        _make_addon(tmp_path, "Real", sv=["RealDB"])
        (tmp_path / "stray_file.txt").write_text("nothing")

        addons = collect_installed_addons(tmp_path)
        assert [a.folder for a in addons] == ["Real"]


# ---------- build_known_names ----------------------------------------------


class TestBuildKnownNames:
    def test_includes_folder_and_declarations_lowercased(self, tmp_path: Path) -> None:
        _make_addon(tmp_path, "Bartender4", sv=["BT4Profiles"], svpc=["BT4CharData"])
        addons = collect_installed_addons(tmp_path)

        known = build_known_names(addons)
        assert known == {"bartender4", "bt4profiles", "bt4chardata"}

    def test_empty_list(self) -> None:
        assert build_known_names([]) == set()


# ---------- scan_sv_dir -----------------------------------------------------


class TestScanSvDir:
    def test_flags_orphans(self, tmp_path: Path) -> None:
        sv_dir = tmp_path / "SavedVariables"
        _make_sv_file(sv_dir, "Bartender4.lua")
        _make_sv_file(sv_dir, "Bartender4.lua.bak")
        _make_sv_file(sv_dir, "OldAddon.lua")
        _make_sv_file(sv_dir, "OldAddon.lua.bak")

        orphans = scan_sv_dir(sv_dir, known={"bartender4"})
        assert set(orphans) == {"OldAddon.lua", "OldAddon.lua.bak"}

    def test_case_insensitive_match(self, tmp_path: Path) -> None:
        # Filename casing differs from entries in known
        sv_dir = tmp_path / "SavedVariables"
        _make_sv_file(sv_dir, "ElvUI.lua")

        assert scan_sv_dir(sv_dir, known={"elvui"}) == []

    def test_ignores_non_lua_files(self, tmp_path: Path) -> None:
        sv_dir = tmp_path / "SavedVariables"
        _make_sv_file(sv_dir, "AddOns.txt")  # game writes this file; not SV
        _make_sv_file(sv_dir, "config.wtf")
        _make_sv_file(sv_dir, "Real.lua")

        orphans = scan_sv_dir(sv_dir, known=set())
        # Only .lua / .lua.bak are considered; everything else is ignored
        assert orphans == ["Real.lua"]

    def test_missing_dir(self, tmp_path: Path) -> None:
        assert scan_sv_dir(tmp_path / "nope", known=set()) == []


# ---------- dir_size --------------------------------------------------------


class TestDirSize:
    def test_sums_sizes(self, tmp_path: Path) -> None:
        (tmp_path / "a.lua").write_text("x" * 100, encoding="utf-8")
        (tmp_path / "b.lua").write_text("y" * 250, encoding="utf-8")
        assert dir_size(tmp_path, ["a.lua", "b.lua"]) == 350

    def test_missing_files_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "a.lua").write_text("x" * 10, encoding="utf-8")
        # b.lua is missing — do not raise
        assert dir_size(tmp_path, ["a.lua", "b.lua"]) == 10


# ---------- scan (end-to-end) ----------------------------------------------


class TestScan:
    def _setup_wow_root(self, tmp_path: Path) -> Path:
        """Build a minimal valid WoW install layout with orphan SV files."""
        wow = tmp_path / "_retail_"
        addons = wow / "Interface" / "AddOns"
        wtf_acc = wow / "WTF" / "Account"
        addons.mkdir(parents=True)
        wtf_acc.mkdir(parents=True)

        # Installed addon
        _make_addon(addons, "ElvUI", sv=["ElvDB"], svpc=["ElvPrivateDB"])

        # Account-level SavedVariables: ElvUI.lua (valid) + DeadAddon.lua (orphan)
        acc = wtf_acc / "1234567890#1"
        acc_sv = acc / "SavedVariables"
        _make_sv_file(acc_sv, "ElvUI.lua")
        _make_sv_file(acc_sv, "ElvDB.lua")  # declared SV name — not an orphan
        _make_sv_file(acc_sv, "DeadAddon.lua")
        _make_sv_file(acc_sv, "DeadAddon.lua.bak")

        # Character-level SavedVariables
        char_sv = acc / "Gul'dan" / "Thrallmar" / "SavedVariables"
        _make_sv_file(char_sv, "ElvUI.lua")  # not an orphan
        _make_sv_file(char_sv, "SomeOldAddon.lua")  # orphan
        return wow

    def test_raises_on_invalid_wow_root(self, tmp_path: Path) -> None:
        logs: list[str] = []
        try:
            scan(tmp_path, logs.append)
        except FileNotFoundError as e:
            assert "Interface" in str(e) or "WTF" in str(e)
        else:
            raise AssertionError("expected FileNotFoundError")

    def test_finds_orphans_at_both_levels(self, tmp_path: Path) -> None:
        wow = self._setup_wow_root(tmp_path)

        logs: list[str] = []
        result = scan(wow, logs.append)

        assert result.addons_count == 1
        # account- and char-level SV combined
        assert result.total_files == 3  # DeadAddon.lua, DeadAddon.lua.bak, SomeOldAddon.lua

        # Reports must use the correct label prefixes
        labels = {r.label for r in result.reports}
        assert any(lbl.startswith("account:") for lbl in labels)
        assert any(lbl.startswith("char:") for lbl in labels)

    def test_reports_clean_if_no_orphans(self, tmp_path: Path) -> None:
        wow = tmp_path / "_retail_"
        (wow / "Interface" / "AddOns").mkdir(parents=True)
        (wow / "WTF" / "Account").mkdir(parents=True)

        result = scan(wow, lambda _: None)
        assert result.total_files == 0
        assert result.reports == []
