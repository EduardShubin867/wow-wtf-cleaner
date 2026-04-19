# WoW WTF Cleaner

A small desktop utility (Tkinter GUI) that finds **orphaned** World of Warcraft addon settings in your `WTF` folder — leftover `SavedVariables` from addons you no longer have — and moves them into a **timestamped backup** folder instead of deleting them. This can noticeably speed up character login, especially on long-lived accounts with years of addon churn.

The window text and buttons are **Russian** for now; the steps below give English glosses in parentheses.

## Why this exists

Every time you install an addon, it may create a `.lua` file under:

- `WTF/Account/<account>/SavedVariables/` (account-wide settings), and/or  
- `WTF/Account/<account>/<realm>/<character>/SavedVariables/` (per-character settings).

When you remove the addon, those files often stay behind. Over time you can end up with **thousands** of orphaned files. On each login the client still reads them, which slows loading.

## For users: download the `.exe`

1. Open **[Releases](https://github.com/EduardShubin867/wow-wtf-cleaner/releases)** and download the latest `WoW-WTF-Cleaner.exe`.
2. Run it.
3. Click **Обзор…** (Browse…) and select your `_retail_` folder inside the WoW installation (for example `C:\Program Files (x86)\World of Warcraft\_retail_`). The path field is under **Папка WoW (_retail_ или _classic_)** — WoW folder (Retail or Classic).
4. Click **1. Сканировать (ничего не удаляет)** — Scan (nothing is deleted); you only get a list of likely orphans.
5. If the list looks reasonable, **fully exit WoW and the Battle.net app** (the app reminds you: close before **Переместить**), then click **2. Переместить найденное в бэкап** (Move findings to backup). Files are relocated to `WTF-orphans-<timestamp>/` inside `_retail_`.
6. Launch the game. If everything works, you can delete the backup folder after a week or so. If something breaks, copy the files back from the backup (the folder layout mirrors the original).

### First run on Windows

Windows SmartScreen may warn about an **unsigned** executable. That is normal for a fresh PyInstaller build without a code-signing certificate. Choose **More info → Run anyway**.

### macOS / Linux

Release binaries are built for **Windows** only. On macOS or Linux, run from source (see **For developers**).

## How orphans are detected

A file `SavedVariables/<Name>.lua` is treated as orphaned only if:

1. There is **no** folder named `<Name>` under `Interface/AddOns/`, **and**
2. `<Name>` does **not** appear in `## SavedVariables:` or `## SavedVariablesPerCharacter:` in any installed addon’s `.toc` (this covers rare cases where an addon writes a SavedVariables file whose basename differs from its folder name).

The logic is **conservative**: if a case is ambiguous, the file is **not** marked as an orphan. Files are **moved to backup**, not deleted, so you can always roll back.

## What this tool does **not** do

- It does not touch `.lua` files **inside** addon folders — only under `WTF/`.
- It does not remove empty folders left from deleted characters.
- It does not clean `Cache/ADB/*/DBCache.bin`, `Data/`, or other caches — those are separate, manual cleanups.
- It does not contact Blizzard servers or change server-side data (macros, bindings, and some addon-related data also sync with your account on Blizzard’s side).

## For developers

### Run from source

Python **3.10+** is required. Tkinter must be available (on some Linux distributions you may need a `python3-tk` package).

```bash
git clone https://github.com/EduardShubin867/wow-wtf-cleaner.git
cd wow-wtf-cleaner
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

python -m wow_wtf_cleaner
```

### Tests

```bash
pytest
```

### Build the `.exe` manually (Windows)

```powershell
pip install -e ".[dev]"
pyinstaller --onefile --windowed `
    --name "WoW-WTF-Cleaner" `
    --collect-submodules wow_wtf_cleaner `
    wow_wtf_cleaner/__main__.py
```

Output: `dist\WoW-WTF-Cleaner.exe`.

### Project layout

```
wow_wtf_cleaner/
├── __main__.py        # entry point
├── config.py          # settings persistence, WoW path autodetect
├── gui.py             # Tkinter UI
└── core/              # logic without Tk dependencies
    ├── models.py      # dataclasses (AddonMeta, ScanResult, …)
    ├── toc.py         # .toc parser
    ├── formatting.py  # string helpers
    ├── scanner.py     # WTF scanning
    └── mover.py       # move files into backup
```

The GUI layer is thin; the interesting logic lives in `core/` and is covered by tests.

## Contributing

Bug reports and feature ideas: **[Issues](https://github.com/EduardShubin867/wow-wtf-cleaner/issues)**. Pull requests are welcome. Especially useful:

- Classic flavour support (`_classic_`, `_classic_era_`, `_ptr_`, etc.)
- Optional cleanup of `DBCache.bin` and related caches
- An icon for the Windows `.exe`
- UI translations (English baseline in code; other locales)
- macOS builds in GitHub Actions (`.app` via `pyinstaller --windowed`)

## License

MIT — see [LICENSE](LICENSE).

---

## Русская версия

Ниже — перевод того же содержания.

### WoW WTF Cleaner

Небольшая GUI-утилита на Tkinter, которая находит в папке `WTF` World of Warcraft **осиротевшие** настройки аддонов — оставшиеся файлы `SavedVariables` от аддонов, которых у вас больше нет, — и **переносит** их в папку бэкапа с меткой времени, не удаляя насовсем. Это может заметно ускорить загрузку персонажа, особенно на старых аккаунтах с долгой историей смены аддонов.

### Зачем это нужно

При установке аддон может создавать `.lua` в:

- `WTF/Account/<аккаунт>/SavedVariables/` (общие настройки), и/или  
- `WTF/Account/<аккаунт>/<реалм>/<персонаж>/SavedVariables/` (на персонажа).

После удаления аддона эти файлы часто остаются. За годы их может набраться **тысячи**; клиент всё равно читает их при входе, что замедляет загрузку.

### Для пользователей: скачайте `.exe`

1. Откройте **[Releases](https://github.com/EduardShubin867/wow-wtf-cleaner/releases)** и скачайте последний `WoW-WTF-Cleaner.exe`.
2. Запустите программу.
3. Нажмите **Обзор…** и укажите папку `_retail_` внутри установки WoW (например `C:\Program Files (x86)\World of Warcraft\_retail_`).
4. Нажмите **1. Сканировать** — ничего не переносится, только список вероятных «сирот».
5. Если список устраивает, **полностью закройте WoW и Battle.net**, затем нажмите **2. Переместить**. Файлы попадут в `WTF-orphans-<метка-времени>/` внутри `_retail_`.
6. Запустите игру. Если всё в порядке, бэкап можно удалить примерно через неделю. Если что-то пошло не так — верните файлы из бэкапа (структура папок совпадает с исходной).

#### Первый запуск в Windows

SmartScreen может предупредить об **неподписанном** exe — это нормально для свежей сборки PyInstaller без сертификата подписи. Выберите **Подробнее → Выполнить в любом случае**.

#### macOS / Linux

Готовые релизы — для **Windows**. На Mac/Linux запускайте из исходников (раздел **Для разработчиков**).

### Как определяются «сироты»

Файл `SavedVariables/<Имя>.lua` считается осиротевшим, только если:

1. В `Interface/AddOns/` **нет** папки с именем `<Имя>`, **и**
2. `<Имя>` **не** указано в `## SavedVariables:` или `## SavedVariablesPerCharacter:` ни в одном `.toc` установленных аддонов (редкие случаи, когда имя файла SV не совпадает с именем папки аддона).

Логика **осторожная**: при сомнении файл **не** помечается орфаном. Файлы **переносятся в бэкап**, а не удаляются — откат всегда возможен.

### Чего утилита не делает

- Не трогает `.lua` **внутри** папок аддонов — только `WTF/`.
- Не удаляет пустые папки от давно удалённых персонажей.
- Не чистит `Cache/ADB/*/DBCache.bin`, `Data/` и прочие кэши — это отдельные ручные задачи.
- Не обращается к серверам Blizzard и не меняет серверные данные (макросы, бинды и часть данных аддонов тоже синхронизируются с аккаунтом на стороне Blizzard).

### Для разработчиков

Нужен **Python 3.10+** и Tkinter (на части дистрибутивов Linux — пакет вроде `python3-tk`).

```bash
git clone https://github.com/EduardShubin867/wow-wtf-cleaner.git
cd wow-wtf-cleaner
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

python -m wow_wtf_cleaner
```

Тесты: `pytest`. Сборка `.exe` на Windows — команда `pyinstaller` как в английском разделе выше.

Структура проекта та же: `wow_wtf_cleaner/` с `__main__.py`, `config.py`, `gui.py` и пакетом `core/` (модели, парсер `.toc`, сканер, перенос). GUI тонкий; логика в `core/` покрыта тестами.

### Участие в проекте

Ошибки и идеи — в **[Issues](https://github.com/EduardShubin867/wow-wtf-cleaner/issues)**. Pull request’ы приветствуются: Classic-флаворы, очистка кэшей, иконка exe, переводы UI, macOS-сборка в CI.

### Лицензия

MIT — см. [LICENSE](LICENSE).
