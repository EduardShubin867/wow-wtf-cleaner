"""UI and log strings: Russian and English."""

from __future__ import annotations

import locale
import os
from typing import Literal

Lang = Literal["ru", "en"]
UiPreference = Literal["auto", "ru", "en"]

MESSAGES: dict[Lang, dict[str, str]] = {
    "ru": {
        "app.title": "WoW WTF Cleaner",
        "lang.label": "Язык:",
        "lang_option.auto": "Авто (как в системе)",
        "lang_option.ru": "Русский",
        "lang_option.en": "English",
        "status.ready": "Готов. Выбери папку _retail_ и нажми «Сканировать».",
        "intro": (
            "Утилита найдёт в папке WTF настройки от аддонов, которых у "
            "тебя больше нет, и перенесёт их в бэкап-папку.\n"
            "Важно: перед нажатием «Переместить» закрой World of Warcraft "
            "и Battle.net."
        ),
        "path_frame": "Папка WoW (_retail_ или _classic_)",
        "browse": "Обзор…",
        "scan_btn": "1. Сканировать (ничего не удаляет)",
        "apply_btn": "2. Переместить найденное в бэкап",
        "browse_dialog_title": "Выбери папку _retail_ внутри World of Warcraft",
        "err.path_not_exist": "Указанная папка не существует.",
        "status.scanning": "Сканирую…",
        "log.error": "Ошибка: {err}",
        "log.total": "Итого: {files} орфанов, {size}",
        "log.move_hint": (
            "Нажми «Переместить» чтобы перенести эти файлы в "
            "бэкап-папку рядом с _retail_."
        ),
        "status.found": "Найдено {files} орфанов ({size})",
        "status.clean": "Чисто! Орфанов не найдено.",
        "confirm.move": (
            "Переместить {files} файлов ({size}) в бэкап-папку?\n\n"
            "ВАЖНО: World of Warcraft и Battle.net должны быть полностью закрыты."
        ),
        "status.moving": "Перемещаю…",
        "done.backup_line": "Готово. Бэкап: {path}",
        "done.msg": (
            "Перемещено {files} файлов.\n\n"
            "Бэкап лежит здесь:\n{path}\n\n"
            "Если после запуска игры что-то пойдёт не так — "
            "файлы можно вернуть обратно из этой папки."
        ),
        "status.done": "Готово.",
        "scan.missing_dirs": (
            "Не найдены нужные папки внутри указанного пути:\n"
            "  {addons_dir}\n  {wtf_dir}\n\n"
            "Убедись что выбрана именно папка _retail_ (или _classic_), "
            "а не корневая World of Warcraft."
        ),
        "scan.installed_addons": "Установленных аддонов: {count}",
        "scan.known_names": "Известных имён SV (папки + декларации): {count}",
        "scan.orphans_line": "[{label}] орфанов: {count} ({size})",
        "mover.move_failed": "  ! не удалось переместить {src}: {err}",
        "mover.moved_to": "[{label}] перемещено в {dest}",
    },
    "en": {
        "app.title": "WoW WTF Cleaner",
        "lang.label": "Language:",
        "lang_option.auto": "Auto (system)",
        "lang_option.ru": "Russian",
        "lang_option.en": "English",
        "status.ready": (
            "Ready. Choose your _retail_ folder and click «Scan»."
        ),
        "intro": (
            "This tool finds SavedVariables in WTF for add-ons you no longer "
            "have and moves them to a backup folder.\n"
            "Important: before clicking «Move», quit World of Warcraft and "
            "the Battle.net app completely."
        ),
        "path_frame": "WoW folder (_retail_ or _classic_)",
        "browse": "Browse…",
        "scan_btn": "1. Scan (does not delete anything)",
        "apply_btn": "2. Move findings to backup",
        "browse_dialog_title": "Choose the _retail_ folder inside World of Warcraft",
        "err.path_not_exist": "The selected folder does not exist.",
        "status.scanning": "Scanning…",
        "log.error": "Error: {err}",
        "log.total": "Total: {files} orphan file(s), {size}",
        "log.move_hint": (
            "Click «Move» to move these files to a backup folder next to _retail_."
        ),
        "status.found": "Found {files} orphan file(s) ({size})",
        "status.clean": "All clean! No orphans found.",
        "confirm.move": (
            "Move {files} file(s) ({size}) to the backup folder?\n\n"
            "IMPORTANT: World of Warcraft and Battle.net must be fully closed."
        ),
        "status.moving": "Moving…",
        "done.backup_line": "Done. Backup: {path}",
        "done.msg": (
            "Moved {files} file(s).\n\n"
            "Backup location:\n{path}\n\n"
            "If something looks wrong after launching the game, you can "
            "restore files from this folder."
        ),
        "status.done": "Done.",
        "scan.missing_dirs": (
            "Required folders are missing under the selected path:\n"
            "  {addons_dir}\n  {wtf_dir}\n\n"
            "Make sure you selected the _retail_ (or _classic_) folder, "
            "not the top-level World of Warcraft directory."
        ),
        "scan.installed_addons": "Installed add-ons: {count}",
        "scan.known_names": "Known SV names (folders + declarations): {count}",
        "scan.orphans_line": "[{label}] orphans: {count} ({size})",
        "mover.move_failed": "  ! failed to move {src}: {err}",
        "mover.moved_to": "[{label}] moved to {dest}",
    },
}


def tr(lang: Lang, key: str, **kwargs: object) -> str:
    """Returns a localized string; substitutes kwargs into the template."""
    template = MESSAGES[lang][key]
    if not kwargs:
        return template
    return template.format(**kwargs)


def detect_system_lang() -> Lang:
    """Detects the OS UI language: ru or en."""
    tags: list[str] = []
    for env_key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(env_key, "")
        if val:
            tags.append(val.split(".")[0])

    try:
        locale.setlocale(locale.LC_MESSAGES, "")
    except (OSError, ValueError, locale.Error):
        pass
    try:
        loc = locale.getlocale(locale.LC_MESSAGES)
        if loc and loc[0]:
            tags.append(loc[0])
    except (OSError, ValueError, TypeError):
        pass

    for tag in tags:
        if tag.lower().startswith("ru"):
            return "ru"
    return "en"


def effective_lang(preference: UiPreference) -> Lang:
    if preference == "auto":
        return detect_system_lang()
    return preference
