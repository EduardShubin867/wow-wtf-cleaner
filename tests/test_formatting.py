"""Tests for wow_wtf_cleaner.core.formatting."""

from __future__ import annotations

from wow_wtf_cleaner.core.formatting import fmt_bytes, strip_sv_ext


class TestFmtBytes:
    def test_zero(self) -> None:
        assert fmt_bytes(0) == "0 B"

    def test_bytes(self) -> None:
        assert fmt_bytes(1) == "1 B"
        assert fmt_bytes(512) == "512 B"
        assert fmt_bytes(1023) == "1023 B"

    def test_kilobytes(self) -> None:
        assert fmt_bytes(1024) == "1.0 KB"
        assert fmt_bytes(2048) == "2.0 KB"
        assert fmt_bytes(1024 * 1024 - 1) == "1024.0 KB"

    def test_megabytes(self) -> None:
        assert fmt_bytes(1024 * 1024) == "1.00 MB"
        assert fmt_bytes(int(5.5 * 1024 * 1024)) == "5.50 MB"
        assert fmt_bytes(597 * 1024 * 1024) == "597.00 MB"


class TestStripSvExt:
    def test_strips_lua(self) -> None:
        assert strip_sv_ext("Bartender4.lua") == "Bartender4"

    def test_strips_lua_bak(self) -> None:
        assert strip_sv_ext("Bartender4.lua.bak") == "Bartender4"

    def test_case_insensitive(self) -> None:
        assert strip_sv_ext("Foo.LUA") == "Foo"
        assert strip_sv_ext("Foo.Lua.Bak") == "Foo"

    def test_no_extension(self) -> None:
        # If there is no extension or it is different — return the name unchanged
        assert strip_sv_ext("something.txt") == "something.txt"
        assert strip_sv_ext("README") == "README"

    def test_only_trailing_match(self) -> None:
        # Strip extension only at the end, not in the middle of the basename
        assert strip_sv_ext("my.lua.backup.lua") == "my.lua.backup"
