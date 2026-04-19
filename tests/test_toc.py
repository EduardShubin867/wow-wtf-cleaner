"""Tests for wow_wtf_cleaner.core.toc."""

from __future__ import annotations

from pathlib import Path

from wow_wtf_cleaner.core.toc import parse_toc


def _write_toc(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


class TestParseToc:
    def test_basic_declarations(self, tmp_path: Path) -> None:
        toc = tmp_path / "TestAddon.toc"
        _write_toc(
            toc,
            "## Interface: 110000\n"
            "## Title: Test Addon\n"
            "## SavedVariables: TestAccountDB, SharedDB\n"
            "## SavedVariablesPerCharacter: TestCharDB\n"
            "\n"
            "main.lua\n",
        )
        sv, svpc = parse_toc(toc)
        assert sv == {"TestAccountDB", "SharedDB"}
        assert svpc == {"TestCharDB"}

    def test_no_declarations(self, tmp_path: Path) -> None:
        toc = tmp_path / "NoVars.toc"
        _write_toc(toc, "## Title: NoVars\n## Interface: 110000\nmain.lua\n")
        sv, svpc = parse_toc(toc)
        assert sv == set()
        assert svpc == set()

    def test_case_insensitive_keys(self, tmp_path: Path) -> None:
        toc = tmp_path / "Case.toc"
        _write_toc(
            toc,
            "## SAVEDVARIABLES: AccVar\n"
            "## SavedVariablesPerCharacter: CharVar\n",
        )
        sv, svpc = parse_toc(toc)
        assert sv == {"AccVar"}
        assert svpc == {"CharVar"}

    def test_whitespace_tolerance(self, tmp_path: Path) -> None:
        toc = tmp_path / "Whitespace.toc"
        _write_toc(
            toc,
            "##   SavedVariables  :   Foo ,  Bar   ,Baz\n",
        )
        sv, _ = parse_toc(toc)
        assert sv == {"Foo", "Bar", "Baz"}

    def test_empty_values_ignored(self, tmp_path: Path) -> None:
        toc = tmp_path / "Empty.toc"
        _write_toc(toc, "## SavedVariables: Foo, , Bar,\n")
        sv, _ = parse_toc(toc)
        assert sv == {"Foo", "Bar"}

    def test_ignores_non_directive_lines(self, tmp_path: Path) -> None:
        toc = tmp_path / "Mixed.toc"
        _write_toc(
            toc,
            "# Just a comment\n"
            "## Title: Mixed\n"
            "## SavedVariables: RealVar\n"
            "some file reference.lua\n"
            "## SavedVariables: Another\n",
        )
        sv, _ = parse_toc(toc)
        assert sv == {"RealVar", "Another"}

    def test_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        # OSError is not propagated — function returns empty sets
        sv, svpc = parse_toc(tmp_path / "does_not_exist.toc")
        assert sv == set()
        assert svpc == set()

    def test_encoding_errors_are_ignored(self, tmp_path: Path) -> None:
        # Some real-world .toc files contain non-UTF-8 bytes.
        # Parser must cope (read_text with errors="ignore").
        toc = tmp_path / "Bad.toc"
        toc.write_bytes(b"## SavedVariables: Foo\n## Title: \xff\xfe bad bytes\n")
        sv, _ = parse_toc(toc)
        assert sv == {"Foo"}
