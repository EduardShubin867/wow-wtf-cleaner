"""Application CustomTkinter UI — modern dark theme."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from wow_wtf_cleaner.config import (
    auto_detect_wow,
    load_ui_language,
    save_last_path,
    save_ui_language,
)
from wow_wtf_cleaner.core import ScanResult, apply_move, fmt_bytes, scan
from wow_wtf_cleaner.i18n import Lang, UiPreference, effective_lang, tr


_LANG_ORDER: tuple[UiPreference, ...] = ("auto", "ru", "en")

# ── Theme ──────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":         "#0D0D1A",
    "surface":    "#13132A",
    "card":       "#1A1A35",
    "input":      "#0A0A18",
    "blue":       "#4A7FFF",
    "blue_hover": "#3060DD",
    "gold":       "#F0B429",
    "gold_hover": "#D09A1A",
    "green":      "#2ECC71",
    "green_hover":"#27AE60",
    "text":       "#E8E8F8",
    "muted":      "#8888AA",
    "dim":        "#555575",
    "border":     "#2A2A55",
}


class CleanupApp:
    """Two-step UI: scan first (dry-run), then move."""

    def __init__(self) -> None:
        self._lang_pref: UiPreference = load_ui_language()
        self._effective_lang: Lang = effective_lang(self._lang_pref)
        self._syncing_lang_combo = False
        self._scanning = False
        self._progress_value = 0.0
        self._progress_dir = 1

        self.root = ctk.CTk()
        self.root.geometry("920x700")
        self.root.minsize(720, 540)
        self.root.configure(fg_color=C["bg"])

        self.wow_path = ctk.StringVar(value=auto_detect_wow())
        self.status_text = ctk.StringVar()
        self.scan_result: ScanResult | None = None

        self._build_ui()
        self._refresh_all_texts()

    def _app_title(self) -> str:
        return tr(self._effective_lang, "app.title")

    # ── Layout ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_header()

        self._main = ctk.CTkFrame(self.root, fg_color="transparent")
        self._main.pack(fill="both", expand=True, padx=18, pady=(14, 0))

        self._build_intro_card()
        self._build_path_card()
        self._build_action_buttons()
        self._build_progress_area()
        self._build_log_area()
        self._build_status_bar()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(
            self.root,
            fg_color=C["surface"],
            corner_radius=0,
            height=58,
            border_width=1,
            border_color=C["border"],
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # WoW sword icon + title
        ctk.CTkLabel(
            header,
            text="⚔  WoW WTF Cleaner",
            font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"),
            text_color=C["gold"],
        ).pack(side="left", padx=22, pady=14)

        # Version badge
        ctk.CTkLabel(
            header,
            text="v0.1",
            font=ctk.CTkFont(size=11),
            text_color=C["dim"],
        ).pack(side="left", pady=20)

        # Language selector on the right
        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.pack(side="right", padx=18, pady=12)

        self._lang_label = ctk.CTkLabel(
            lang_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=C["muted"],
        )
        self._lang_label.pack(side="left", padx=(0, 8))

        self._lang_combo = ctk.CTkOptionMenu(
            lang_frame,
            values=[""],
            command=self._on_language_selected_option,
            width=170,
            height=32,
            fg_color=C["card"],
            button_color=C["blue"],
            button_hover_color=C["blue_hover"],
            dropdown_fg_color=C["card"],
            dropdown_hover_color=C["surface"],
            text_color=C["text"],
            font=ctk.CTkFont(size=13),
            corner_radius=8,
        )
        self._lang_combo.pack(side="left")

    def _card(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        """Helper: returns a styled card frame."""
        return ctk.CTkFrame(
            parent,
            fg_color=C["card"],
            corner_radius=12,
            border_width=1,
            border_color=C["border"],
        )

    def _build_intro_card(self) -> None:
        card = self._card(self._main)
        card.pack(fill="x", pady=(0, 10))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            inner,
            text=" ℹ ",
            font=ctk.CTkFont(size=16),
            text_color=C["blue"],
            width=30,
        ).pack(side="left", anchor="n", pady=2)

        self._intro = ctk.CTkLabel(
            inner,
            text="",
            wraplength=800,
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color=C["muted"],
            anchor="w",
        )
        self._intro.pack(side="left", padx=(6, 0), fill="x", expand=True)

    def _build_path_card(self) -> None:
        card = self._card(self._main)
        card.pack(fill="x", pady=(0, 10))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        self._path_label = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C["muted"],
            anchor="w",
        )
        self._path_label.pack(anchor="w", pady=(0, 8))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")

        self._path_entry = ctk.CTkEntry(
            row,
            textvariable=self.wow_path,
            font=ctk.CTkFont(size=13, family="Consolas"),
            fg_color=C["input"],
            border_color=C["border"],
            text_color=C["text"],
            placeholder_text="C:\\Program Files (x86)\\World of Warcraft\\_retail_",
            placeholder_text_color=C["dim"],
            corner_radius=8,
            height=38,
        )
        self._path_entry.pack(side="left", fill="x", expand=True)

        self._browse_btn = ctk.CTkButton(
            row,
            text="",
            command=self._browse,
            width=100,
            height=38,
            fg_color=C["surface"],
            hover_color=C["border"],
            text_color=C["text"],
            border_color=C["border"],
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        )
        self._browse_btn.pack(side="left", padx=(8, 0))

    def _build_action_buttons(self) -> None:
        btn_frame = ctk.CTkFrame(self._main, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 8))

        self.scan_btn = ctk.CTkButton(
            btn_frame,
            text="",
            command=self._on_scan,
            height=44,
            fg_color=C["blue"],
            hover_color=C["blue_hover"],
            text_color="white",
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.scan_btn.pack(side="left", fill="x", expand=True)

        self.apply_btn = ctk.CTkButton(
            btn_frame,
            text="",
            command=self._on_apply,
            state="disabled",
            height=44,
            fg_color=C["green"],
            hover_color=C["green_hover"],
            text_color="white",
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.apply_btn.pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _build_progress_area(self) -> None:
        # Fixed-height container — keeps layout stable
        self._progress_frame = ctk.CTkFrame(
            self._main, fg_color="transparent", height=10
        )
        self._progress_frame.pack(fill="x", pady=(0, 6))
        self._progress_frame.pack_propagate(False)

        self._progress = ctk.CTkProgressBar(
            self._progress_frame,
            fg_color=C["card"],
            progress_color=C["blue"],
            corner_radius=4,
            height=6,
        )
        self._progress.set(0)
        # Will be packed/unpacked in _set_busy

    def _build_log_area(self) -> None:
        log_header = ctk.CTkFrame(self._main, fg_color="transparent")
        log_header.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            log_header,
            text="📋  Log",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C["muted"],
        ).pack(side="left")

        self.log_widget = ctk.CTkTextbox(
            self._main,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=C["card"],
            text_color=C["text"],
            border_color=C["border"],
            border_width=1,
            corner_radius=12,
            state="disabled",
            wrap="word",
        )
        self.log_widget.pack(fill="both", expand=True, pady=(0, 0))

    def _build_status_bar(self) -> None:
        bar = ctk.CTkFrame(
            self.root,
            fg_color=C["surface"],
            corner_radius=0,
            height=30,
            border_width=1,
            border_color=C["border"],
        )
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status_label = ctk.CTkLabel(
            bar,
            textvariable=self.status_text,
            font=ctk.CTkFont(size=12),
            text_color=C["dim"],
            anchor="w",
        )
        self._status_label.pack(side="left", padx=16, pady=6)

        # Right side: "Ready" dot indicator
        self._status_dot = ctk.CTkLabel(
            bar,
            text="●",
            font=ctk.CTkFont(size=11),
            text_color=C["green"],
        )
        self._status_dot.pack(side="right", padx=16)

    # ── Text refresh ──────────────────────────────────────────────────────

    def _refresh_all_texts(self) -> None:
        self._effective_lang = effective_lang(self._lang_pref)
        L = self._effective_lang

        self.root.title(self._app_title())
        self._lang_label.configure(text=tr(L, "lang.label"))
        self._intro.configure(text=tr(L, "intro"))
        self._path_label.configure(text=tr(L, "path_frame").upper())
        self._browse_btn.configure(text=tr(L, "browse"))
        self.scan_btn.configure(text=tr(L, "scan_btn"))
        self.apply_btn.configure(text=tr(L, "apply_btn"))
        self.status_text.set(tr(L, "status.ready"))

        self._syncing_lang_combo = True
        try:
            labels = [tr(L, f"lang_option.{p}") for p in _LANG_ORDER]
            self._lang_combo.configure(values=labels)
            idx = _LANG_ORDER.index(self._lang_pref)
            self._lang_combo.set(labels[idx])
        finally:
            self._syncing_lang_combo = False

    def _on_language_selected_option(self, value: str) -> None:
        if self._syncing_lang_combo:
            return
        L = self._effective_lang
        labels = [tr(L, f"lang_option.{p}") for p in _LANG_ORDER]
        try:
            idx = labels.index(value)
        except ValueError:
            return
        self._lang_pref = _LANG_ORDER[idx]
        save_ui_language(self._lang_pref)
        self._refresh_all_texts()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _browse(self) -> None:
        initial = self.wow_path.get() or str(Path.home())
        chosen = filedialog.askdirectory(
            title=tr(self._effective_lang, "browse_dialog_title"),
            initialdir=initial,
        )
        if chosen:
            self.wow_path.set(chosen)

    def _log(self, message: str) -> None:
        """Thread-safe append to log widget."""
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

        if busy:
            self._scanning = True
            self._progress_value = 0.0
            self._progress_dir = 1
            self._progress.pack(fill="x")
            self._status_dot.configure(text_color=C["gold"])
            self._animate_progress()
        else:
            self._scanning = False
            self._progress.pack_forget()
            self._progress.set(0)
            self._status_dot.configure(
                text_color=C["green"] if not can_apply else C["gold"]
            )

    def _animate_progress(self) -> None:
        """Bounce the progress bar while scanning."""
        if not self._scanning:
            return
        v = self._progress_value + 0.018 * self._progress_dir
        if v >= 1.0:
            v = 1.0
            self._progress_dir = -1
        elif v <= 0.0:
            v = 0.0
            self._progress_dir = 1
        self._progress_value = v
        self._progress.set(v)
        self.root.after(20, self._animate_progress)

    @staticmethod
    def _run_in_thread(target: Callable[[], None]) -> None:
        threading.Thread(target=target, daemon=True).start()

    # ── Actions ───────────────────────────────────────────────────────────

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
                self._log(tr(move_lang, "done.backup_line", path=backup))
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
                    0,
                    lambda: self.status_text.set(tr(move_lang, "status.done")),
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
