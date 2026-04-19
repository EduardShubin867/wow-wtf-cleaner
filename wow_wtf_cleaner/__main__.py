"""Entry point for `python -m wow_wtf_cleaner` and the PyInstaller binary."""

from __future__ import annotations

from wow_wtf_cleaner.gui import CleanupApp


def main() -> None:
    CleanupApp().run()


if __name__ == "__main__":
    main()
