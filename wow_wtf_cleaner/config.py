"""Settings persistence and automatic WoW path detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wow_wtf_cleaner.i18n import UiPreference


SETTINGS_FILE = Path.home() / ".wow_wtf_cleaner.json"

DEFAULT_SETTINGS: dict[str, Any] = {
    "wow_path": "",
    "ui_language": "auto",
}

COMMON_WOW_PATHS: tuple[Path, ...] = (
    # Windows
    Path(r"C:\Program Files (x86)\World of Warcraft\_retail_"),
    Path(r"C:\Program Files\World of Warcraft\_retail_"),
    Path(r"D:\Games\World of Warcraft\_retail_"),
    Path(r"E:\Games\World of Warcraft\_retail_"),
    Path(r"C:\Games\World of Warcraft\_retail_"),
    # macOS
    Path("/Applications/World of Warcraft/_retail_"),
    Path.home() / "Applications" / "World of Warcraft" / "_retail_",
)


def load_settings() -> dict[str, Any]:
    data = dict(DEFAULT_SETTINGS)
    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return data
    if isinstance(raw, dict):
        data.update(raw)
    return data


def save_settings(updates: dict[str, Any]) -> None:
    current = load_settings()
    current.update(updates)
    try:
        SETTINGS_FILE.write_text(
            json.dumps(current, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass


def load_last_path() -> str:
    """Reads the last used path from the settings file; empty if none."""
    value = load_settings().get("wow_path", "")
    return str(value) if isinstance(value, str) else ""


def save_last_path(path: str) -> None:
    """Saves the last used path. Silently ignores I/O errors."""
    save_settings({"wow_path": path})


def load_ui_language() -> UiPreference:
    v = load_settings().get("ui_language", "auto")
    if v in ("auto", "ru", "en"):
        return v  # type: ignore[return-value]
    return "auto"


def save_ui_language(pref: UiPreference) -> None:
    save_settings({"ui_language": pref})


def auto_detect_wow() -> str:
    """Returns the best-guessed path to the _retail_ folder, or an empty string."""
    saved = load_last_path()
    if saved and Path(saved).is_dir():
        return saved
    for candidate in COMMON_WOW_PATHS:
        if candidate.is_dir():
            return str(candidate)
    return ""
