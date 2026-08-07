"""WinLuxCD Windows desktop application."""

import sys
import tkinter as tk
from pathlib import Path

from winluxcd_core import PathConversionError, convert_to_wsl, run_wslpath


BASE = Path(__file__).resolve().parent

BG = "#0b1220"
HEADER = "#145bd2"
HEADER_DARK = "#0f4db7"
SURFACE = "#111d32"
SURFACE_ALT = "#172640"
BORDER = "#28405f"
ACCENT = "#4aa3ff"
ACCENT_HOVER = "#6db8ff"
TEXT = "#f6f9ff"
MUTED = "#a7b6ca"
ERROR = "#ff9b9b"


def resource_path(relative_path: str) -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", BASE))
    return bundle_root / relative_path


class WinLuxCDApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WinLuxCD")
        self.geometry("760x430")
        self.minsize(620, 370)
        self.configure(bg=BG)

        self.input_var = tk.StringVar()
        self.wsl_var = tk.StringVar()
        self.cd_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Enter a path, then convert it to a WSL path.")
        self._header_image = None
        self._footer_image = None

        self._set_icon()
        self._build_ui()
        self.bind("<Return>", lambda _event: self.convert())
        self.input_entry.focus_set()

    def _set_icon(self) -> None:
        try:
            self.iconbitmap(default=str(resource_path("icons/winluxcd.ico")))
        except tk.TclError:
            pass

    @staticmethod
    def _load_image(relative_path: str):
        try:
            return tk.PhotoImage(file=str(resource_path(relative_path)))
        except (tk.TclError, OSError):
            return None

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=HEADER, padx=18, pady=12)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        self._header_image = self._load_image("icons/winluxcd-32.png")
        if self._header_image is not None:
            tk.Label(header, image=self._header_image, bg=HEADER).grid(
                row=0, column=0, rowspan=2, padx=(0, 12)
            )
        tk.Label(
            header,
            text="WinLuxCD",
            bg=HEADER,
            fg=TEXT,
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")
        tk.Label(
            header,
            text="Windows paths to WSL",
            bg=HEADER,
            fg="#dceaff",
            font=("Segoe UI", 9),
            anchor="w",
        ).grid(row=1, column=1, sticky="ew")

        content = tk.Frame(self, bg=BG, padx=20, pady=18)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(7, weight=1)

        self._label(content, "Windows or WSL path", 0)
        input_frame = tk.Frame(content, bg=BG)
        input_frame.grid(row=1, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)
        self.input_entry = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            bg=SURFACE_ALT,
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground=HEADER,
            selectforeground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            font=("Segoe UI", 10),
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=7)
        self._button(input_frame, "Paste", self.paste).grid(row=0, column=1, ipady=5)

        self._button(content, "Convert to WSL", self.convert, primary=True).grid(
            row=2, column=0, sticky="w", pady=(14, 20), ipady=5
        )

        self._output_row(content, 3, "WSL path", self.wsl_var, self.copy_wsl)
        self._output_row(content, 5, "Copy-ready cd command", self.cd_var, self.copy_cd)

        self.status_label = tk.Label(
            content,
            textvariable=self.status_var,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="nw",
            justify="left",
        )
        self.status_label.grid(row=7, column=0, sticky="new", pady=(14, 0))

        footer = tk.Frame(self, bg=BG)
        footer.grid(row=2, column=0, sticky="e", padx=20, pady=(0, 10))
        self._footer_image = self._load_image("icons/winluxcd-16.png")
        if self._footer_image is not None:
            tk.Label(footer, image=self._footer_image, bg=BG).pack(side="left", padx=(0, 5))
        tk.Label(
            footer,
            text="Copyright (c) Denville Energy Consulting Ltd",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 8),
        ).pack(side="left")

    @staticmethod
    def _label(parent, text: str, row: int) -> None:
        tk.Label(
            parent,
            text=text,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=(0, 5))

    @staticmethod
    def _button(parent, text: str, command, primary: bool = False) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=ACCENT if primary else SURFACE_ALT,
            fg=TEXT,
            activebackground=ACCENT_HOVER if primary else BORDER,
            activeforeground=TEXT,
            disabledforeground=MUTED,
            relief="flat",
            borderwidth=0,
            padx=16 if primary else 13,
            pady=2,
            cursor="hand2",
            font=("Segoe UI", 9, "bold" if primary else "normal"),
        )

    def _output_row(self, parent, label_row: int, label: str, variable: tk.StringVar, command) -> None:
        self._label(parent, label, label_row)
        frame = tk.Frame(parent, bg=BG)
        frame.grid(row=label_row + 1, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        tk.Entry(
            frame,
            textvariable=variable,
            state="readonly",
            readonlybackground=SURFACE,
            fg=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=7)
        self._button(frame, "Copy", command).grid(row=0, column=1, ipady=5)

    def set_status(self, message: str, error: bool = False) -> None:
        self.status_var.set(message)
        self.status_label.configure(fg=ERROR if error else MUTED)

    def paste(self) -> None:
        try:
            value = self.clipboard_get()
        except tk.TclError:
            self.set_status("The clipboard is empty or unavailable.", True)
            return
        if not value.strip():
            self.set_status("The clipboard is empty.", True)
            return
        self.input_var.set(value.strip())
        self.input_entry.select_range(0, tk.END)
        self.convert()

    def convert(self) -> None:
        try:
            wsl_path, cd_command = convert_to_wsl(self.input_var.get(), run_wslpath)
        except (PathConversionError, OSError) as exc:
            self.wsl_var.set("")
            self.cd_var.set("")
            self.set_status(str(exc), True)
            return

        self.wsl_var.set(wsl_path)
        self.cd_var.set(cd_command)
        self.set_status("Converted successfully.")

    def copy_value(self, value: str, success_message: str) -> None:
        if not value:
            return
        self.clipboard_clear()
        self.clipboard_append(value)
        self.update()
        self.set_status(success_message)

    def copy_wsl(self) -> None:
        self.copy_value(self.wsl_var.get(), "WSL path copied to the clipboard.")

    def copy_cd(self) -> None:
        self.copy_value(self.cd_var.get(), "cd command copied to the clipboard.")


def main() -> None:
    WinLuxCDApp().mainloop()


if __name__ == "__main__":
    main()
