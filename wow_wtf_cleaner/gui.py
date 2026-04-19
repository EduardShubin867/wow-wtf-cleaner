"""Application Tkinter UI."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import StringVar, Tk, filedialog, messagebox, scrolledtext, ttk
from typing import Callable

from wow_wtf_cleaner.config import (
    auto_detect_wow,
    load_ui_language,
    save_last_path,
    save_ui_language,
)
from wow_wtf_cleaner.core import ScanResult, apply_move, fmt_bytes, scan
from wow_wtf_cleaner.i18n import Lang, UiPreference, effective_lang, tr


_LANG_ORDER: tuple[UiPreference, ...] = ("auto", "ru", "en")


class CleanupApp:
    """Two-step UI: scan first (dry-run), then move."""

    def __init__(self) -> None:
        self._lang_pref: UiPreference = load_ui_language()
        self._effective_lang: Lang = effective_lang(self._lang_pref)
        self._syncing_lang_combo = False

        self.root = Tk()
        self.root.geometry("820x620")
        self.root.minsize(640, 480)

        self.wow_path = StringVar(value=auto_detect_wow())
        self.status_text = StringVar()

        self.scan_result: ScanResult | None = None

        self._build_ui()
        self._refresh_all_texts()

    def _app_title(self) -> str:
        return tr(self._effective_lang, "app.title")

    # ----- layout -----------------------------------------------------------

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        lang_row = ttk.Frame(self.root)
        lang_row.pack(fill="x", **pad)
        self._lang_label = ttk.Label(lang_row)
        self._lang_label.pack(side="left", padx=(0, 8))
        self._lang_combo = ttk.Combobox(
            lang_row,
            state="readonly",
            width=28,
        )
        self._lang_combo.pack(side="left")
        self._lang_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

        self._intro = ttk.Label(
            self.root,
            wraplength=780,
            justify="left",
        )
        self._intro.pack(fill="x", **pad)

        self._path_frame = ttk.LabelFrame(self.root)
        self._path_frame.pack(fill="x", **pad)

        row = ttk.Frame(self._path_frame)
        row.pack(fill="x", padx=8, pady=8)
        ttk.Entry(row, textvariable=self.wow_path).pack(side="left", fill="x", expand=True)
        self._browse_btn = ttk.Button(row, command=self._browse)
        self._browse_btn.pack(side="left", padx=(6, 0))

        btns = ttk.Frame(self.root)
        btns.pack(fill="x", **pad)
        self.scan_btn = ttk.Button(btns, command=self._on_scan)
        self.scan_btn.pack(side="left")
        self.apply_btn = ttk.Button(
            btns,
            command=self._on_apply,
            state="disabled",
        )
        self.apply_btn.pack(side="left", padx=(8, 0))

        ttk.Separator(self.root).pack(fill="x", padx=10)

        self.log_widget = scrolledtext.ScrolledText(
            self.root, wrap="word", state="disabled", font=("Consolas", 10)
        )
        self.log_widget.pack(fill="both", expand=True, **pad)

        ttk.Label(
            self.root, textvariable=self.status_text, relief="sunken", anchor="w"
        ).pack(fill="x", side="bottom")

    def _refresh_all_texts(self) -> None:
        self._effective_lang = effective_lang(self._lang_pref)
        L = self._effective_lang
        self.root.title(self._app_title())
        self._lang_label.configure(text=tr(L, "lang.label"))
        self._intro.configure(text=tr(L, "intro"))
        self._path_frame.configure(text=tr(L, "path_frame"))
        self._browse_btn.configure(text=tr(L, "browse"))
        self.scan_btn.configure(text=tr(L, "scan_btn"))
        self.apply_btn.configure(text=tr(L, "apply_btn"))
        self.status_text.set(tr(L, "status.ready"))

        self._syncing_lang_combo = True
        try:
            labels = [tr(L, f"lang_option.{p}") for p in _LANG_ORDER]
            self._lang_combo.configure(values=labels)
            idx = _LANG_ORDER.index(self._lang_pref)
            self._lang_combo.current(idx)
        finally:
            self._syncing_lang_combo = False

    def _on_language_selected(self, _event: object | None = None) -> None:
        if self._syncing_lang_combo:
            return
        idx = self._lang_combo.current()
        if idx < 0:
            return
        self._lang_pref = _LANG_ORDER[idx]
        save_ui_language(self._lang_pref)
        self._refresh_all_texts()

    # ----- helpers ----------------------------------------------------------

    def _browse(self) -> None:
        initial = self.wow_path.get() or str(Path.home())
        chosen = filedialog.askdirectory(
            title=tr(self._effective_lang, "browse_dialog_title"),
            initialdir=initial,
        )
        if chosen:
            self.wow_path.set(chosen)

    def _log(self, message: str) -> None:
        """Thread-safe: safe to call from a worker thread."""

        def append() -> None:
            self.log_widget.configure(state="normal")
            self.log_widget.insert("end", message + "\n")
            self.log_widget.see("end")
            self.log_widget.configure(state="disabled")

        self.root.after(0, append)

    def _clear_log(self) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.delete("1.0", "end")
        self.log_widget.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self.scan_btn.configure(state="disabled" if busy else "normal")
        can_apply = (
            not busy
            and self.scan_result is not None
            and self.scan_result.total_files > 0
        )
        self.apply_btn.configure(state="normal" if can_apply else "disabled")

    @staticmethod
    def _run_in_thread(target: Callable[[], None]) -> None:
        threading.Thread(target=target, daemon=True).start()

    # ----- actions ----------------------------------------------------------

    def _on_scan(self) -> None:
        wow = Path(self.wow_path.get().strip())
        L = self._effective_lang
        title = self._app_title()
        if not wow.is_dir():
            messagebox.showerror(title, tr(L, "err.path_not_exist"))
            return

        self._clear_log()
        self.scan_result = None
        self._set_busy(True)
        self.status_text.set(tr(L, "status.scanning"))
        save_last_path(str(wow))
        scan_lang = L

        def work() -> None:
            try:
                result = scan(wow, self._log, lang=scan_lang)
                self.scan_result = result
                self._log("")
                self._log(
                    tr(
                        scan_lang,
                        "log.total",
                        files=result.total_files,
                        size=fmt_bytes(result.total_bytes),
                    )
                )
                if result.total_files > 0:
                    self._log(tr(scan_lang, "log.move_hint"))
                    status = tr(
                        scan_lang,
                        "status.found",
                        files=result.total_files,
                        size=fmt_bytes(result.total_bytes),
                    )
                else:
                    status = tr(scan_lang, "status.clean")
                self.root.after(0, lambda: self.status_text.set(status))
            except Exception as e:
                err = str(e)
                self._log("\n" + tr(scan_lang, "log.error", err=err))
                self.root.after(0, lambda: messagebox.showerror(title, err))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        self._run_in_thread(work)

    def _on_apply(self) -> None:
        if self.scan_result is None or self.scan_result.total_files == 0:
            return

        wow = Path(self.wow_path.get().strip())
        total_files = self.scan_result.total_files
        total_bytes = self.scan_result.total_bytes
        reports = self.scan_result.reports
        L = self._effective_lang
        title = self._app_title()

        confirmed = messagebox.askyesno(
            title,
            tr(
                L,
                "confirm.move",
                files=total_files,
                size=fmt_bytes(total_bytes),
            ),
        )
        if not confirmed:
            return

        self._set_busy(True)
        self.status_text.set(tr(L, "status.moving"))
        move_lang = L

        def work() -> None:
            try:
                backup = apply_move(wow, reports, self._log, lang=move_lang)
                self._log(
                    tr(move_lang, "done.backup_line", path=backup),
                )
                self.scan_result = None
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        title,
                        tr(
                            move_lang,
                            "done.msg",
                            files=total_files,
                            path=backup,
                        ),
                    ),
                )
                self.root.after(
                    0, lambda: self.status_text.set(tr(move_lang, "status.done"))
                )
            except Exception as e:
                err = str(e)
                self._log("\n" + tr(move_lang, "log.error", err=err))
                self.root.after(0, lambda: messagebox.showerror(title, err))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        self._run_in_thread(work)

    def run(self) -> None:
        self.root.mainloop()
