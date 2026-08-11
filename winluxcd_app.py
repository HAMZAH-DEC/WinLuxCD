"""WinLuxCD Windows desktop application."""

import json
import os
import sys
import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
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
CLOSE_HOVER = "#c42b1c"

MAX_HISTORY = 12
MIN_WINDOW_WIDTH = 1000
HISTORY_DISPLAY_MAX = 56


def resource_path(relative_path: str) -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", BASE))
    return bundle_root / relative_path


def shorten_path(path: str, max_chars: int = HISTORY_DISPLAY_MAX) -> str:
    """Shorten a path for a narrow list while keeping its back end visible.

    Short paths are returned unchanged.  Long paths have their leading
    components elided with a horizontal ellipsis so the tail of the address
    (folder chain, file name, extension) stays readable, for example::

        C:\\Users\\you\\repo\\backend\\app\\settings.py
        -> …\\repo\\backend\\app\\settings.py
    """
    if len(path) <= max_chars:
        return path
    separator = "\\" if "\\" in path else "/"
    parts = path.replace(separator, "/").split("/")
    tail_parts = []
    used = 1  # room for the leading ellipsis
    for part in reversed(parts):
        need = len(part) + (1 if tail_parts else 0)
        if tail_parts and used + need > max_chars:
            break
        tail_parts.insert(0, part)
        used += need
    tail = separator.join(tail_parts)
    if len(tail) > max_chars:
        # One component alone exceeds the limit: cut from the front so the
        # file name / extension stays visible.
        return "…" + tail[-(max_chars - 1):]
    if len(parts) > len(tail_parts):
        return "…" + separator + tail
    return tail


def history_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "WinLuxCD" / "history.json"
    return Path.home() / ".winluxcd_history.json"


def load_history() -> list:
    try:
        data = json.loads(history_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    entries = [str(item) for item in data if isinstance(item, str) and item.strip()]
    return entries[:MAX_HISTORY]


def save_history(entries: list) -> None:
    try:
        path = history_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    except OSError:
        pass


def settings_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "WinLuxCD" / "settings.json"
    return Path.home() / ".winluxcd_settings.json"


def load_settings() -> dict:
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(settings: dict) -> None:
    try:
        path = settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        pass


def enable_dpi_awareness() -> None:
    """Keep the Tk layout crisp and correctly sized on scaled Windows displays."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # system DPI aware
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class HoverTooltip:
    """A small always-on-top label that shows text near the pointer."""

    def __init__(self, master: tk.Misc) -> None:
        self._master = master
        self._window = None
        self._label = None

    def show(self, text: str, x_root: int, y_root: int) -> None:
        if not text:
            self.hide()
            return
        if self._window is None:
            self._window = tk.Toplevel(self._master)
            self._window.overrideredirect(True)
            self._window.attributes("-topmost", True)
            self._label = tk.Label(
                self._window,
                text="",
                bg=SURFACE_ALT,
                fg=TEXT,
                relief="solid",
                borderwidth=1,
                highlightthickness=0,
                padx=8,
                pady=4,
                font=("Consolas", 9),
            )
            self._label.pack()
        self._label.configure(text=text)
        self._window.update_idletasks()
        width = self._window.winfo_reqwidth()
        height = self._window.winfo_reqheight()
        screen_w = self._window.winfo_screenwidth()
        screen_h = self._window.winfo_screenheight()
        x = x_root + 14
        y = y_root + 16
        if x + width > screen_w - 8:
            x = x_root - width - 14
        if y + height > screen_h - 8:
            y = y_root - height - 16
        self._window.geometry("+{}+{}".format(max(0, x), max(0, y)))
        self._window.deiconify()
        self._window.lift()

    def hide(self) -> None:
        if self._window is not None:
            self._window.withdraw()


class WinLuxCDApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WinLuxCD")
        self.configure(bg=BG)

        self.input_var = tk.StringVar()
        self.wsl_var = tk.StringVar()
        self.cd_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Enter a path, then convert it to a WSL path.")
        self.history = load_history()
        self._header_image = None
        self._footer_image = None
        self._drag_offset = None
        self._min_width = 400
        self._min_height = 300
        self._closing = False
        self._pre_minimize_geometry = None
        self._history_display = []
        self._popdown_open = False
        self.hover_tooltip = HoverTooltip(self)

        self._set_icon()
        self.overrideredirect(True)  # custom blue title bar with min/close buttons
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Return>", lambda _event: self.convert())
        self.bind("<Alt-F4>", lambda _event: self.close())
        self.bind("<Map>", self._on_map)
        self.input_entry.bind("<<Paste>>", self._on_paste)
        self._finalize_geometry()
        self.input_entry.focus_set()

    def _set_icon(self) -> None:
        try:
            self.iconbitmap(default=str(resource_path("icons/winluxcd.ico")))
        except tk.TclError:
            pass

    def _load_image(self, relative_path: str):
        try:
            # Bind the image to this window's Tcl interpreter explicitly;
            # without a master, tkinter uses the first root created, which
            # breaks when more than one Tk instance exists in a process.
            return tk.PhotoImage(master=self, file=str(resource_path(relative_path)))
        except (tk.TclError, OSError):
            return None

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_titlebar()

        content = tk.Frame(self, bg=BG, padx=20, pady=18)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(9, weight=1)

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
        entry_buttons = tk.Frame(input_frame, bg=BG)
        entry_buttons.grid(row=0, column=1, sticky="e")
        self._button(entry_buttons, "Paste", self.paste).grid(
            row=0, column=0, sticky="ew", ipady=5
        )
        self._button(entry_buttons, "Clear", self.clear_input).grid(
            row=1, column=0, sticky="ew", pady=(6, 0), ipady=5
        )

        self._button(content, "Convert to WSL", self.convert, primary=True).grid(
            row=2, column=0, sticky="w", pady=(14, 20), ipady=5
        )

        self._output_row(content, 3, "WSL path", self.wsl_var, self.copy_wsl)
        self._output_row(content, 5, "Copy-ready cd command", self.cd_var, self.copy_cd)

        self._build_history(content, 7)

        self.status_label = tk.Label(
            content,
            textvariable=self.status_var,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="nw",
            justify="left",
        )
        self.status_label.grid(row=9, column=0, sticky="new", pady=(14, 0))

        footer = tk.Frame(self, bg=BG)
        footer.grid(row=2, column=0, sticky="e", padx=(20, 0), pady=(0, 10))
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

        self._grip = tk.Canvas(
            self, width=16, height=16, bg=BG, highlightthickness=0,
            cursor="bottom_right_corner",
        )
        self._grip.create_line(15, 5, 5, 15, fill=MUTED)
        self._grip.create_line(15, 10, 10, 15, fill=MUTED)
        self._grip.grid(row=2, column=1, sticky="se")
        self._grip.bind("<B1-Motion>", self._resize)
        self._grip.bind("<ButtonRelease-1>", self._save_size_now)

    def _build_titlebar(self) -> None:
        bar = tk.Frame(self, bg=HEADER)
        # Span both columns so the titlebar covers the resize-grip column and
        # the close button sits flush with the window's right edge.
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.columnconfigure(1, weight=1)
        self._bind_drag(bar)

        self._header_image = self._load_image("icons/winluxcd-32.png")
        if self._header_image is not None:
            icon = tk.Label(bar, image=self._header_image, bg=HEADER)
            icon.grid(row=0, column=0, rowspan=2, padx=(18, 12), pady=8)
            self._bind_drag(icon)

        title = tk.Label(
            bar,
            text="WinLuxCD",
            bg=HEADER,
            fg=TEXT,
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        )
        title.grid(row=0, column=1, sticky="ew", pady=(8, 0))
        self._bind_drag(title)

        subtitle = tk.Label(
            bar,
            text="Windows paths to WSL",
            bg=HEADER,
            fg="#dceaff",
            font=("Segoe UI", 9),
            anchor="w",
        )
        subtitle.grid(row=1, column=1, sticky="ew", pady=(0, 8))
        self._bind_drag(subtitle)

        buttons = tk.Frame(bar, bg=HEADER)
        buttons.grid(row=0, column=2, rowspan=2, sticky="ne")
        self._title_button(buttons, "\u2013", self.minimize, HEADER_DARK).pack(
            side="left"
        )
        self._title_button(buttons, "\u00d7", self.close, CLOSE_HOVER).pack(
            side="left"
        )

    @staticmethod
    def _title_button(parent, text: str, command, hover_bg: str) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=HEADER,
            fg=TEXT,
            activebackground=hover_bg,
            activeforeground=TEXT,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=16,
            pady=9,
            cursor="hand2",
            font=("Segoe UI", 11),
        )

    def _bind_drag(self, widget: tk.Widget) -> None:
        widget.bind("<Button-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._drag)

    def _start_drag(self, event) -> None:
        self._drag_offset = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def _drag(self, event) -> None:
        if self._drag_offset is None:
            return
        self.geometry(
            "+{}+{}".format(
                event.x_root - self._drag_offset[0],
                event.y_root - self._drag_offset[1],
            )
        )

    def _resize(self, event) -> None:
        width = max(event.x_root - self.winfo_x(), self._min_width)
        height = max(event.y_root - self.winfo_y(), self._min_height)
        self.geometry("{}x{}".format(width, height))

    def _save_size_now(self, _event) -> None:
        save_settings(self._current_settings())

    def minimize(self) -> None:
        # On Windows the window keeps its custom chrome and minimises straight
        # into the taskbar via ShowWindow; _ensure_taskbar_button gives it a
        # real taskbar entry, so no native-chrome detour is needed.  The
        # overrideredirect/iconify dance below is only a fallback for
        # platforms without ShowWindow.
        if sys.platform == "win32":
            try:
                import ctypes

                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                    return
            except Exception:
                pass
        if not self.overrideredirect():
            self.iconify()
            return
        self._pre_minimize_geometry = self.geometry()
        self.overrideredirect(False)
        self.after(10, self.iconify)

    def _ensure_taskbar_button(self) -> None:
        """Force a real taskbar button for the custom-chrome window.

        Tk marks overrideredirect windows as tool windows
        (WS_EX_TOOLWINDOW), so without this they have no taskbar entry and
        Windows minimises them to a floating title-bar strip on the desktop
        instead of the taskbar.  WS_EX_APPWINDOW overrides that.  The wrapper
        window is created when the window is first mapped, so this runs from
        the <Map> handler.
        """
        if sys.platform != "win32":
            return
        try:
            import ctypes

            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(self.winfo_id())
            if not hwnd:
                return
            get_style = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
            set_style = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
            ex_style = get_style(hwnd, -20)  # GWL_EXSTYLE
            set_style(hwnd, -20, ex_style | 0x00040000)  # WS_EX_APPWINDOW
        except Exception:
            pass

    def _on_map(self, _event) -> None:
        # The wrapper window (and its styles) is created when the window is
        # first mapped; re-apply the forced taskbar button there.
        self._ensure_taskbar_button()
        # Only scheduled while the window is mapped with native chrome after
        # the minimise dance, so normal startup never registers a timer.
        if not self.overrideredirect():
            self.after(30, self._reapply_titlebar)

    def _reapply_titlebar(self) -> None:
        try:
            if not self.overrideredirect():
                self.overrideredirect(True)
                # The native-chrome detour can shrink or misplace the window
                # on some Windows versions; restore the saved size/position.
                if self._pre_minimize_geometry:
                    self.geometry(self._pre_minimize_geometry)
                    self._pre_minimize_geometry = None
        except tk.TclError:
            pass

    def _on_paste(self, _event) -> None:
        # The widget binding fires before the Entry class binding inserts the
        # clipboard text, so convert once the paste has actually landed.
        self.after_idle(self.convert)

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

    def _build_history(self, content: tk.Frame, row: int) -> None:
        header_row = tk.Frame(content, bg=BG)
        header_row.grid(row=row, column=0, sticky="ew", pady=(2, 5))
        tk.Label(
            header_row,
            text="Recent",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(side="left")
        tk.Button(
            header_row,
            text="Clear",
            command=self.clear_history,
            bg=BG,
            fg=ACCENT,
            activebackground=BG,
            activeforeground=ACCENT_HOVER,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=("Segoe UI", 9),
            padx=6,
        ).pack(side="right")

        self.history_frame = tk.Frame(content, bg=BG)
        self.history_frame.grid(row=row + 1, column=0, sticky="ew")
        self.history_frame.columnconfigure(0, weight=1)

        # Dark styling for the drop-down list popup.
        self.option_add("*TCombobox*Listbox.background", SURFACE_ALT)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", HEADER)
        self.option_add("*TCombobox*Listbox.selectForeground", TEXT)
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Recent.TCombobox",
            fieldbackground=SURFACE_ALT,
            background=SURFACE_ALT,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=6,
        )
        style.map(
            "Recent.TCombobox",
            fieldbackground=[("readonly", SURFACE_ALT)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", HEADER)],
            selectforeground=[("readonly", TEXT)],
        )

        self.recent_combo = ttk.Combobox(
            self.history_frame,
            style="Recent.TCombobox",
            state="readonly",
            height=12,
            font=("Segoe UI", 10),
        )
        self.recent_combo.grid(row=0, column=0, sticky="ew", ipady=6)
        self.recent_combo.bind("<<ComboboxSelected>>", self._on_recent_selected)
        self._bind_popdown_tooltip()
        self._refresh_recent()

    def _bind_popdown_tooltip(self) -> None:
        # Show the full address for the hovered Recent entry.  The dropdown
        # popdown opens and closes with <Map>/<Unmap> (Tk's own bindings on
        # the ComboboxPopdown class), and while it is open a light poll
        # follows the pointer and shows the tooltip for the item underneath.
        # Polling is used instead of <Motion> bindings because real mouse
        # movement does not reliably reach the dropdown listbox on Windows
        # (the popdown grabs the pointer and Tk's win32 routing skips some
        # motion events); polling works identically on every platform.
        self._popdown_hook = "__winluxcd_popdown_hook"
        self.tk.createcommand(self._popdown_hook, self._on_popdown_event)
        self.tk.call(
            "bind", "ComboboxPopdown", "<Map>",
            "+{} %W map".format(self._popdown_hook),
        )
        self.tk.call(
            "bind", "ComboboxPopdown", "<Unmap>",
            "+{} %W unmap".format(self._popdown_hook),
        )

    def _on_popdown_event(self, widget, state, *extra) -> None:
        if state == "map":
            self._popdown_open = True
            self._poll_popdown_tooltip()
        elif state == "unmap":
            self._popdown_open = False
            self.hover_tooltip.hide()

    def _poll_popdown_tooltip(self) -> None:
        if not self._popdown_open:
            return
        try:
            popdown = self.recent_combo._w + ".popdown"
            listbox = popdown + ".f.l"
            if not self.tk.call("winfo", "exists", popdown) or not self.tk.call(
                "winfo", "viewable", listbox
            ):
                return
            px = int(self.tk.call("winfo", "pointerx", listbox))
            py = int(self.tk.call("winfo", "pointery", listbox))
            lx = px - int(self.tk.call("winfo", "rootx", listbox))
            ly = py - int(self.tk.call("winfo", "rooty", listbox))
            width = int(self.tk.call("winfo", "width", listbox))
            if lx < 0 or ly < 0 or lx >= width:
                self.hover_tooltip.hide()
                return
            index = int(self.tk.call(listbox, "index", "@%d,%d" % (lx, ly)))
            size = int(self.tk.call(listbox, "size"))
            bounding_box = self.tk.call(listbox, "bbox", index)
            if not 0 <= index < size or not bounding_box:
                self.hover_tooltip.hide()
                return
            if not (bounding_box[1] <= ly < bounding_box[1] + bounding_box[3]):
                self.hover_tooltip.hide()
                return
            self.hover_tooltip.show(self.history[index], px, py)
        except tk.TclError:
            pass
        finally:
            if self._popdown_open:
                self.after(100, self._poll_popdown_tooltip)

    def _on_recent_selected(self, _event) -> None:
        full_path = self._selected_history_path()
        if full_path:
            # The dropdown shows the shortened address; put the real one back
            # in the closed field once a choice has been made.
            self.recent_combo.set(full_path)
            self.use_history(full_path)

    def _selected_history_path(self) -> str:
        value = self.recent_combo.get()
        index = self._popdown_curselection()
        if index is not None and 0 <= index < len(self.history):
            return self.history[index]
        try:
            return self.history[self._history_display.index(value)]
        except ValueError:
            return value

    def _popdown_curselection(self):
        # The popdown listbox is created by Tcl (not through tkinter), so it
        # is reached through raw widget commands rather than nametowidget.
        try:
            selection = self.tk.call(
                self.recent_combo._w + ".popdown.f.l", "curselection"
            )
        except tk.TclError:
            return None
        return int(selection[0]) if selection else None

    def _refresh_recent(self) -> None:
        self._history_display = [shorten_path(entry) for entry in self.history]
        self.recent_combo["values"] = self._history_display
        if not self.history:
            self.recent_combo.set("")

    def use_history(self, path: str) -> None:
        self.input_var.set(path)
        self.input_entry.icursor(tk.END)
        self.input_entry.focus_set()
        self.convert()

    def record_history(self, raw_input: str) -> None:
        entry = raw_input.strip()
        if not entry:
            return
        entries = [entry] + [item for item in self.history if item != entry]
        self.history = entries[:MAX_HISTORY]
        save_history(self.history)
        self._refresh_recent()

    def clear_history(self) -> None:
        if not self.history:
            return
        if not messagebox.askyesno(
            "Clear recent history",
            "Remove all recent entries?",
            parent=self,
        ):
            return
        self.history = []
        save_history(self.history)
        self._refresh_recent()

    def _finalize_geometry(self) -> None:
        """Restore the saved window size/position, or auto-size and centre."""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        min_width = self.winfo_reqwidth()
        min_height = self.winfo_reqheight()
        self._min_width = min_width
        self._min_height = min_height

        saved = load_settings()
        width = height = x = y = None
        try:
            width = int(saved.get("width", 0))
            height = int(saved.get("height", 0))
            x = int(saved.get("x", -1))
            y = int(saved.get("y", -1))
        except (TypeError, ValueError):
            width = height = 0

        if width > 0 and height > 0:
            width = min(max(width, min_width), max(min_width, screen_width - 40))
            height = min(max(height, min_height), max(min_height, screen_height - 40))
            if x < 0 or y < 0 or x + width > screen_width or y + height > screen_height:
                x = max(0, (screen_width - width) // 2)
                y = max(0, (screen_height - height) // 3)
        else:
            width = max(min_width, min(MIN_WINDOW_WIDTH, screen_width - 40))
            height = min(min_height, max(200, screen_height - 40))
            x = max(0, (screen_width - width) // 2)
            y = max(0, (screen_height - height) // 3)

        self.geometry("{}x{}+{}+{}".format(width, height, x, y))
        self.resizable(False, False)
        self.minsize(min_width, min_height)

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        save_settings(self._current_settings())
        self.destroy()

    def _current_settings(self) -> dict:
        return {
            "width": self.winfo_width(),
            "height": self.winfo_height(),
            "x": self.winfo_x(),
            "y": self.winfo_y(),
        }

    def set_status(self, message: str, error: bool = False) -> None:
        self.status_var.set(message)
        self.status_label.configure(fg=ERROR if error else MUTED)

    def clear_input(self) -> None:
        self.input_var.set("")
        self.wsl_var.set("")
        self.cd_var.set("")
        self.set_status("Enter a path, then convert it to a WSL path.")
        self.input_entry.focus_set()

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
        self.record_history(self.input_var.get())

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
    enable_dpi_awareness()
    WinLuxCDApp().mainloop()


if __name__ == "__main__":
    main()
