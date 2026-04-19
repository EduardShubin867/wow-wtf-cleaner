# WoW WTF Cleaner

A small desktop utility with a modern dark-themed GUI that finds **orphaned** World of Warcraft addon settings in your `WTF` folder — leftover `SavedVariables` from addons you no longer have — and moves them into a **timestamped backup** folder instead of deleting them. This can noticeably speed up character login, especially on long-lived accounts with years of addon churn.

The interface supports **Russian** and **English** (auto-detected from your OS, switchable in the header).

## Why this exists

Every time you install an addon, it may create a `.lua` file under:

- `WTF/Account/<account>/SavedVariables/` (account-wide settings), and/or  
- `WTF/Account/<account>/<realm>/<character>/SavedVariables/` (per-character settings).

When you remove the addon, those files often stay behind. Over time you can end up with **thousands** of orphaned files. On each login the client still reads them, which slows loading.

## For users: download the `.exe`

1. Open **[Releases](https://github.com/EduardShubin867/wow-wtf-cleaner/releases)** and download the latest `WoW-WTF-Cleaner.exe`.
2. Run it — no installation required.
3. Click **Browse…** and select your `_retail_` folder inside the WoW installation (e.g. `C:\Program Files (x86)\World of Warcraft\_retail_`). The path is usually auto-detected.
4. Click **1. Scan (does not delete anything)** — you only get a list of likely orphans.
5. If the list looks reasonable, **fully exit WoW and the Battle.net app**, then click **2. Move findings to backup**. Files are relocated to `WTF-orphans-<timestamp>/` inside `_retail_`.
6. Launch the game. If everything works, you can delete the backup folder after a week or so. If something breaks, copy the files back — the backup folder layout mirrors the original.

### First run on Windows

Windows SmartScreen may warn about an **unsigned** executable. That is normal for a fresh PyInstaller build without a code-signing certificate. Choose **More info → Run anyway**.

### macOS / Linux

Release binaries are built for **Windows** only. On macOS or Linux, run from source (see **For developers**).

## How orphans are detected

A file `SavedVariables/<Name>.lua` is treated as orphaned only if:

1. There is **no** folder named `<Name>` under `Interface/AddOns/`, **and**
2. `<Name>` does **not** appear in `## SavedVariables:` or `## SavedVariablesPerCharacter:` in any installed addon's `.toc` (this covers rare cases where an addon writes a SavedVariables file whose basename differs from its folder name).

The logic is **conservative**: if a case is ambiguous, the file is **not** marked as an orphan. Files are **moved to backup**, not deleted, so you can always roll back.

## What this tool does **not** do

- It does not touch `.lua` files **inside** addon folders — only under `WTF/`.
- It does not remove empty folders left from deleted characters.
- It does not clean `Cache/ADB/*/DBCache.bin`, `Data/`, or other caches — those are separate, manual cleanups.
- It does not contact Blizzard servers or change server-side data.

## For developers

### Requirements

- **Python 3.10+**
- Tkinter (bundled with standard Python on Windows/macOS; on some Linux distros: `sudo apt install python3-tk`)
- [`customtkinter`](https://github.com/TomSchimansky/CustomTkinter) — modern dark-themed Tkinter widgets (installed automatically as a dependency)

### Run from source

```bash
git clone https://github.com/EduardShubin867/wow-wtf-cleaner.git
cd wow-wtf-cleaner

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e ".[dev]"
python -m wow_wtf_cleaner
```

### Tests

```bash
pytest
```

### Build the `.exe` (Windows)

A `WoW-WTF-Cleaner.spec` file is committed to the repository. It encodes all required PyInstaller options, including bundling `customtkinter` assets (themes, icons). Use it for reproducible builds:

```powershell
# inside the activated venv
pip install -e ".[dev]"
pyinstaller WoW-WTF-Cleaner.spec
```

Output: `dist\WoW-WTF-Cleaner.exe`.

> **Why the `.spec` file?**  
> Building from the `.spec` ensures `customtkinter`'s themes and image assets are correctly collected via `--collect-all customtkinter`. Rebuilding from scratch with a plain CLI command would require:
> ```powershell
> pyinstaller --onefile --windowed `
>     --name "WoW-WTF-Cleaner" `
>     --collect-all customtkinter `
>     --collect-submodules wow_wtf_cleaner `
>     wow_wtf_cleaner/__main__.py
> ```

### Project layout

```
wow_wtf_cleaner/
├── __main__.py        # entry point
├── config.py          # settings persistence, WoW path autodetect
├── gui.py             # customtkinter UI (dark theme)
├── i18n.py            # Russian / English strings
└── core/              # logic without GUI dependencies
    ├── models.py      # dataclasses (AddonMeta, ScanResult, …)
    ├── toc.py         # .toc parser
    ├── formatting.py  # string helpers (fmt_bytes, …)
    ├── scanner.py     # WTF scanning
    └── mover.py       # move files into backup
```

The GUI layer is thin; the interesting logic lives in `core/` and is covered by tests.

## Contributing

Contributions are welcome! Bug reports and feature ideas: **[Issues](https://github.com/EduardShubin867/wow-wtf-cleaner/issues)**. Pull requests are appreciated.

## License

MIT — see [LICENSE](LICENSE).

---

## Русская версия

### WoW WTF Cleaner

Небольшая GUI-утилита с современным тёмным интерфейсом, которая находит в папке `WTF` World of Warcraft **осиротевшие** настройки аддонов — оставшиеся файлы `SavedVariables` от аддонов, которых у вас больше нет, — и **переносит** их в папку бэкапа с меткой времени, не удаляя насовсем. Это может заметно ускорить загрузку персонажа, особенно на старых аккаунтах с долгой историей смены аддонов.

Интерфейс поддерживает **русский** и **английский** языки (определяется автоматически по системе, переключается прямо в шапке приложения).

### Зачем это нужно

При установке аддон может создавать `.lua` в:

- `WTF/Account/<аккаунт>/SavedVariables/` (общие настройки), и/или  
- `WTF/Account/<аккаунт>/<реалм>/<персонаж>/SavedVariables/` (на персонажа).

После удаления аддона эти файлы часто остаются. За годы их может набраться **тысячи**; клиент всё равно читает их при входе, что замедляет загрузку.

### Для пользователей: скачайте `.exe`

1. Откройте **[Releases](https://github.com/EduardShubin867/wow-wtf-cleaner/releases)** и скачайте последний `WoW-WTF-Cleaner.exe`.
2. Запустите — установка не нужна.
3. Нажмите **Обзор…** и укажите папку `_retail_` внутри установки WoW (например `C:\Program Files (x86)\World of Warcraft\_retail_`). Путь обычно определяется автоматически.
4. Нажмите **1. Сканировать** — ничего не переносится, только список вероятных «сирот».
5. Если список устраивает, **полностью закройте WoW и Battle.net**, затем нажмите **2. Переместить**. Файлы попадут в `WTF-orphans-<метка-времени>/` внутри `_retail_`.
6. Запустите игру. Если всё в порядке, бэкап можно удалить примерно через неделю. Если что-то пошло не так — верните файлы из бэкапа (структура папок совпадает с исходной).

#### Первый запуск в Windows

SmartScreen может предупредить о **неподписанном** exe — это нормально для свежей сборки PyInstaller без сертификата подписи. Выберите **Подробнее → Выполнить в любом случае**.

#### macOS / Linux

Готовые релизы — для **Windows**. На Mac/Linux запускайте из исходников (раздел **Для разработчиков**).

### Как определяются «сироты»

Файл `SavedVariables/<Имя>.lua` считается осиротевшим, только если:

1. В `Interface/AddOns/` **нет** папки с именем `<Имя>`, **и**
2. `<Имя>` **не** указано в `## SavedVariables:` или `## SavedVariablesPerCharacter:` ни в одном `.toc` установленных аддонов.

Логика **осторожная**: при сомнении файл **не** помечается орфаном. Файлы **переносятся в бэкап**, а не удаляются — откат всегда возможен.

### Чего утилита не делает

- Не трогает `.lua` **внутри** папок аддонов — только `WTF/`.
- Не удаляет пустые папки от удалённых персонажей.
- Не чистит `Cache/ADB/*/DBCache.bin`, `Data/` и прочие кэши.
- Не обращается к серверам Blizzard и не меняет серверные данные.

### Для разработчиков

**Требования:** Python 3.10+, Tkinter, [`customtkinter`](https://github.com/TomSchimansky/CustomTkinter) (устанавливается автоматически как зависимость пакета).

```bash
git clone https://github.com/EduardShubin867/wow-wtf-cleaner.git
cd wow-wtf-cleaner

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e ".[dev]"
python -m wow_wtf_cleaner
```

Тесты: `pytest`.

#### Сборка `.exe` (Windows)

В репозитории закоммичен файл `WoW-WTF-Cleaner.spec` — используйте его для воспроизводимой сборки:

```powershell
pip install -e ".[dev]"
pyinstaller WoW-WTF-Cleaner.spec
```

Готовый файл: `dist\WoW-WTF-Cleaner.exe`.

Файл `.spec` содержит `--collect-all customtkinter`, который необходим для корректной упаковки тем и иконок customtkinter.

### Участие в проекте

Контрибьюты приветствуются! Ошибки и идеи — в **[Issues](https://github.com/EduardShubin867/wow-wtf-cleaner/issues)**. Pull request'ы будем рады рассмотреть.

### Лицензия

MIT — см. [LICENSE](LICENSE).
