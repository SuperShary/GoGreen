"""
GoGreen v2 — Premium Futuristic Dark GUI
Zero external dependencies — standard library tkinter only.
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional

from engine import ActivityEngine
from scheduler import ScheduleManager
import settings

# ═══════════════════════════════════════════════════════════════════
#  COLOUR PALETTE — Futuristic dark theme
# ═══════════════════════════════════════════════════════════════════
_C = {
    "bg":           "#08080f",    # near-black base
    "bg_card":      "#101020",    # dark navy cards
    "bg_card_alt":  "#141428",    # slightly lighter card
    "bg_input":     "#1a1a30",    # input fields
    "bg_hover":     "#1e1e3a",    # hover state
    "fg":           "#e4e4f0",    # primary text
    "fg_dim":       "#555570",    # muted text
    "fg_mid":       "#9090a8",    # medium text
    "green":        "#00ff88",    # neon green
    "green_dark":   "#00cc6a",    # pressed green
    "green_glow":   "#00ff8830",  # green with alpha
    "amber":        "#ffab00",    # pause/warning
    "amber_dark":   "#cc8800",    # pressed amber
    "red":          "#ff4757",    # stop/error
    "red_dark":     "#cc3040",    # pressed red
    "accent":       "#7c4dff",    # section headers
    "accent_dim":   "#5a3acc",    # dimmer accent
    "border":       "#1e1e38",    # card borders
    "border_glow":  "#00ff8840",  # active border glow
    "warn_bg":      "#2a1800",    # warning banner bg
    "warn_border":  "#ff8800",    # warning border
    "warn_text":    "#ffcc00",    # warning text
    "log_bg":       "#0a0a14",    # log background (darkest)
    "log_time":     "#00ff88",    # timestamp color in log
    "log_ok":       "#00cc6a",    # success entries
    "log_warn":     "#ff8800",    # warning entries
    "log_fail":     "#ff4757",    # failure entries
}

_FONT      = ("SF Mono", 11) if sys.platform == "darwin" else ("Consolas", 10)
_FONT_SM   = ("SF Mono", 10) if sys.platform == "darwin" else ("Consolas", 9)
_FONT_SANS = ("SF Pro Display", 12) if sys.platform == "darwin" else ("Segoe UI", 11)
_FONT_SANS_BOLD = (_FONT_SANS[0], _FONT_SANS[1], "bold")
_FONT_TITLE = (_FONT_SANS[0], 24, "bold")
_FONT_TIMER = ("SF Mono", 36, "bold") if sys.platform == "darwin" else ("Consolas", 32, "bold")
_FONT_STATUS = (_FONT_SANS[0], 15, "bold")
_FONT_SECTION = (_FONT_SANS[0], 11, "bold")
_FONT_BTN = (_FONT_SANS[0], 13, "bold")
_FONT_LOG = ("SF Mono", 11) if sys.platform == "darwin" else ("Consolas", 10)


# ═══════════════════════════════════════════════════════════════════
#  Animated Pulsing Status Dot
# ═══════════════════════════════════════════════════════════════════

class StatusDot(tk.Canvas):
    _COLOURS = {
        ActivityEngine.STATE_ACTIVE:  _C["green"],
        ActivityEngine.STATE_PAUSED:  _C["amber"],
        ActivityEngine.STATE_STOPPED: _C["fg_dim"],
    }

    def __init__(self, master, size: int = 20, **kw):
        super().__init__(master, width=size, height=size,
                         bg=_C["bg_card"], highlightthickness=0, **kw)
        self._size = size
        self._colour = _C["fg_dim"]
        self._glow_phase = 0.0
        self._animating = False
        self._draw()

    def set_state(self, state: str) -> None:
        self._colour = self._COLOURS.get(state, _C["fg_dim"])
        if state == ActivityEngine.STATE_ACTIVE:
            if not self._animating:
                self._animating = True
                self._animate()
        else:
            self._animating = False
            self._draw()

    def _draw(self, glow: float = 0.0) -> None:
        self.delete("all")
        cx, cy = self._size / 2, self._size / 2
        r = self._size / 2 - 2
        if glow > 0:
            gr = r + 4 * glow
            self.create_oval(cx - gr, cy - gr, cx + gr, cy + gr,
                             fill="", outline=self._colour,
                             width=max(1, int(2.5 * glow)))
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         fill=self._colour, outline="")

    def _animate(self) -> None:
        if not self._animating:
            return
        import math
        self._glow_phase += 0.1
        glow = (math.sin(self._glow_phase) + 1) / 2
        self._draw(glow)
        self.after(50, self._animate)


# ═══════════════════════════════════════════════════════════════════
#  MAIN APPLICATION WINDOW
# ═══════════════════════════════════════════════════════════════════

class GoGreenApp:
    DURATION_OPTIONS = {
        "2 hours":  2 * 3600,
        "4 hours":  4 * 3600,
        "8 hours":  8 * 3600,
        "12 hours": 12 * 3600,
        "Infinite": None,
    }
    DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self):
        self.engine = ActivityEngine()
        self.scheduler = ScheduleManager()
        self.cfg = settings.load()

        self.engine.on_state_change   = self._on_state_change
        self.engine.on_activity       = self._on_activity
        self.engine.on_duration_end   = self._on_duration_end
        self.engine.on_permission_issue = self._on_permission_issue

        self.scheduler.on_enter_window = self._schedule_start
        self.scheduler.on_exit_window  = self._schedule_stop

        # ── Root window ──────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("GoGreen")
        self.root.configure(bg=_C["bg"])
        self.root.minsize(520, 860)
        self.root.resizable(False, False)

        w, h = 520, 880
        sx = self.root.winfo_screenwidth()
        sy = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sx-w)//2}+{(sy-h)//2}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Force to front
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(1500, lambda: self.root.attributes("-topmost", False))

        if sys.platform == "darwin":
            try:
                subprocess.Popen(
                    ["osascript", "-e",
                     'tell application "System Events" to set frontmost '
                     f'of the first process whose unix id is {os.getpid()} to true'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        self._build_styles()
        self._build_ui()
        self._apply_settings()

        if self.cfg.get("schedule_enabled", False):
            self.scheduler.start()

        self._tick()

    # ═════════════════════════════════════════════════════════════
    #  STYLES
    # ═════════════════════════════════════════════════════════════

    def _build_styles(self) -> None:
        s = ttk.Style()
        s.theme_use("clam")

        s.configure("BG.TFrame", background=_C["bg"])
        s.configure("Card.TFrame", background=_C["bg_card"])
        s.configure("CardAlt.TFrame", background=_C["bg_card_alt"])
        s.configure("Warn.TFrame", background=_C["warn_bg"])

        s.configure("Title.TLabel", background=_C["bg"],
                     foreground=_C["green"], font=_FONT_TITLE)
        s.configure("Status.TLabel", background=_C["bg_card"],
                     foreground=_C["fg"], font=_FONT_STATUS)
        s.configure("Timer.TLabel", background=_C["bg_card"],
                     foreground=_C["green"], font=_FONT_TIMER)
        s.configure("Card.TLabel", background=_C["bg_card"],
                     foreground=_C["fg"], font=_FONT_SANS)
        s.configure("CardAlt.TLabel", background=_C["bg_card_alt"],
                     foreground=_C["fg"], font=_FONT_SANS)
        s.configure("Dim.TLabel", background=_C["bg_card"],
                     foreground=_C["fg_dim"], font=_FONT_SM)
        s.configure("DimBG.TLabel", background=_C["bg"],
                     foreground=_C["fg_dim"], font=_FONT_SM)
        s.configure("Section.TLabel", background=_C["bg_card"],
                     foreground=_C["accent"], font=_FONT_SECTION)
        s.configure("SectionAlt.TLabel", background=_C["bg_card_alt"],
                     foreground=_C["accent"], font=_FONT_SECTION)
        s.configure("Warn.TLabel", background=_C["warn_bg"],
                     foreground=_C["warn_text"], font=_FONT_SANS)
        s.configure("WarnBold.TLabel", background=_C["warn_bg"],
                     foreground=_C["warn_text"], font=_FONT_SANS_BOLD)

        # Buttons
        for name, bg, bg_active, fg in [
            ("Start",  _C["green"],  _C["green_dark"], _C["bg"]),
            ("Pause",  _C["amber"],  _C["amber_dark"], _C["bg"]),
            ("Stop",   _C["red"],    _C["red_dark"],   "#fff"),
        ]:
            s.configure(f"{name}.TButton", font=_FONT_BTN,
                         foreground=fg, background=bg,
                         borderwidth=0, padding=(20, 12))
            s.map(f"{name}.TButton",
                  background=[("active", bg_active), ("disabled", _C["bg_input"])])

        s.configure("Fix.TButton", font=_FONT_SANS_BOLD,
                     foreground=_C["bg"], background=_C["warn_text"],
                     borderwidth=0, padding=(10, 6))
        s.map("Fix.TButton",
              background=[("active", _C["amber"])])

        s.configure("Green.Horizontal.TScale",
                     background=_C["bg_card"], troughcolor=_C["bg_input"])

        s.configure("Card.TRadiobutton", background=_C["bg_card"],
                     foreground=_C["fg"], font=_FONT_SANS)
        s.configure("Card.TCheckbutton", background=_C["bg_card"],
                     foreground=_C["fg"], font=_FONT_SANS)

    # ═════════════════════════════════════════════════════════════
    #  BUILD UI
    # ═════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        root = self.root

        # ── Title Bar ────────────────────────────────────────────
        title_frame = ttk.Frame(root, style="BG.TFrame")
        title_frame.pack(fill="x", padx=24, pady=(16, 0))

        ttk.Label(title_frame, text="🟢 GoGreen",
                  style="Title.TLabel").pack(side="left")

        right_info = ttk.Frame(title_frame, style="BG.TFrame")
        right_info.pack(side="right")
        platform_text = "macOS" if sys.platform == "darwin" else "Windows"
        ttk.Label(right_info, text="v2", style="DimBG.TLabel").pack(anchor="e")
        ttk.Label(right_info, text=platform_text,
                  style="DimBG.TLabel").pack(anchor="e")

        # ── Permission Warning Banner (hidden by default) ────────
        self.warn_frame = ttk.Frame(root, style="Warn.TFrame")
        # NOT packed initially — shown only if permission check fails

        self.warn_inner = ttk.Frame(self.warn_frame, style="Warn.TFrame")
        self.warn_inner.pack(fill="x", padx=14, pady=10)

        ttk.Label(self.warn_inner, text="⚠️ ACCESSIBILITY PERMISSION REQUIRED",
                  style="WarnBold.TLabel").pack(anchor="w")
        self.warn_msg_label = ttk.Label(
            self.warn_inner,
            text="System Settings → Privacy & Security → Accessibility → Enable your Terminal",
            style="Warn.TLabel", wraplength=440)
        self.warn_msg_label.pack(anchor="w", pady=(4, 6))

        if sys.platform == "darwin":
            ttk.Button(self.warn_inner, text="🔐  Open Accessibility Settings",
                       style="Fix.TButton",
                       command=self._open_accessibility_settings).pack(anchor="w")

        # ── Status Card ──────────────────────────────────────────
        status_card = tk.Frame(root, bg=_C["bg_card"],
                               highlightbackground=_C["border"],
                               highlightthickness=1)
        status_card.pack(fill="x", padx=24, pady=(12, 0))
        self._status_card = status_card

        status_row = ttk.Frame(status_card, style="Card.TFrame")
        status_row.pack(fill="x", padx=20, pady=(14, 0))

        self.status_dot = StatusDot(status_row, size=20)
        self.status_dot.pack(side="left", padx=(0, 10))

        self.status_label = ttk.Label(status_row, text="STOPPED",
                                      style="Status.TLabel")
        self.status_label.pack(side="left")

        # Cycle counter
        self._cycle_count = 0
        self.cycle_label = ttk.Label(status_row, text="0 cycles",
                                     style="Dim.TLabel")
        self.cycle_label.pack(side="right", padx=(0, 4))

        self.timer_label = ttk.Label(status_card, text="00:00:00",
                                     style="Timer.TLabel")
        self.timer_label.pack(pady=(6, 14))

        # ── Duration Card ────────────────────────────────────────
        dur_card = tk.Frame(root, bg=_C["bg_card"],
                            highlightbackground=_C["border"],
                            highlightthickness=1)
        dur_card.pack(fill="x", padx=24, pady=(8, 0))

        ttk.Label(dur_card, text="⏱  DURATION",
                  style="Section.TLabel").pack(anchor="w", padx=20, pady=(10, 4))

        self.duration_var = tk.StringVar(value="Infinite")

        dur_grid = ttk.Frame(dur_card, style="Card.TFrame")
        dur_grid.pack(fill="x", padx=20)

        for i, label in enumerate(self.DURATION_OPTIONS.keys()):
            r, c = divmod(i, 3)
            rb = ttk.Radiobutton(dur_grid, text=label, value=label,
                                 variable=self.duration_var,
                                 style="Card.TRadiobutton",
                                 command=self._on_duration_change)
            rb.grid(row=r, column=c, sticky="w", padx=(0, 16), pady=2)

        custom_row = ttk.Frame(dur_card, style="Card.TFrame")
        custom_row.pack(fill="x", padx=20, pady=(4, 10))

        ttk.Radiobutton(custom_row, text="Custom:", value="Custom",
                        variable=self.duration_var,
                        style="Card.TRadiobutton",
                        command=self._on_duration_change).pack(side="left")

        self.custom_hours = tk.StringVar(value="1")
        self.custom_entry = tk.Entry(custom_row, textvariable=self.custom_hours,
                                     width=5, bg=_C["bg_input"], fg=_C["fg"],
                                     insertbackground=_C["green"],
                                     font=_FONT, relief="flat", bd=4)
        self.custom_entry.pack(side="left", padx=(6, 4))
        ttk.Label(custom_row, text="hours", style="Dim.TLabel").pack(side="left")

        # ── Interval Card ────────────────────────────────────────
        int_card = tk.Frame(root, bg=_C["bg_card"],
                            highlightbackground=_C["border"],
                            highlightthickness=1)
        int_card.pack(fill="x", padx=24, pady=(8, 0))

        ttk.Label(int_card, text="🔄  ACTIVITY INTERVAL",
                  style="Section.TLabel").pack(anchor="w", padx=20, pady=(10, 4))

        slider_row = ttk.Frame(int_card, style="Card.TFrame")
        slider_row.pack(fill="x", padx=20)

        ttk.Label(slider_row, text="30s", style="Dim.TLabel").pack(side="left")

        self.interval_var = tk.IntVar(value=60)
        self.interval_scale = ttk.Scale(
            slider_row, from_=30, to=300,
            variable=self.interval_var, orient="horizontal",
            style="Green.Horizontal.TScale",
            command=self._on_interval_change)
        self.interval_scale.pack(side="left", fill="x", expand=True, padx=6)

        ttk.Label(slider_row, text="5m", style="Dim.TLabel").pack(side="left")

        self.interval_display = ttk.Label(int_card, text="Every 60 seconds",
                                          style="Card.TLabel")
        self.interval_display.pack(padx=20, pady=(2, 10), anchor="w")

        # ── Schedule Card ────────────────────────────────────────
        sched_card = tk.Frame(root, bg=_C["bg_card"],
                              highlightbackground=_C["border"],
                              highlightthickness=1)
        sched_card.pack(fill="x", padx=24, pady=(8, 0))

        ttk.Label(sched_card, text="📅  SCHEDULE",
                  style="Section.TLabel").pack(anchor="w", padx=20, pady=(10, 4))

        self.schedule_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(sched_card, text="Enable auto-schedule",
                        variable=self.schedule_enabled_var,
                        style="Card.TCheckbutton",
                        command=self._on_schedule_toggle).pack(anchor="w", padx=20)

        time_row = ttk.Frame(sched_card, style="Card.TFrame")
        time_row.pack(fill="x", padx=20, pady=(6, 0))

        ttk.Label(time_row, text="Start:", style="Card.TLabel").pack(side="left")
        self.sched_start_var = tk.StringVar(value="09:00")
        tk.Entry(time_row, textvariable=self.sched_start_var, width=6,
                 bg=_C["bg_input"], fg=_C["fg"], insertbackground=_C["green"],
                 font=_FONT, relief="flat", bd=4,
                 justify="center").pack(side="left", padx=(4, 16))

        ttk.Label(time_row, text="Stop:", style="Card.TLabel").pack(side="left")
        self.sched_stop_var = tk.StringVar(value="18:00")
        tk.Entry(time_row, textvariable=self.sched_stop_var, width=6,
                 bg=_C["bg_input"], fg=_C["fg"], insertbackground=_C["green"],
                 font=_FONT, relief="flat", bd=4,
                 justify="center").pack(side="left", padx=(4, 0))

        day_row = ttk.Frame(sched_card, style="Card.TFrame")
        day_row.pack(fill="x", padx=20, pady=(6, 10))

        self.day_vars = []
        for i, label in enumerate(self.DAY_LABELS):
            var = tk.BooleanVar(value=(i < 5))
            ttk.Checkbutton(day_row, text=label, variable=var,
                            style="Card.TCheckbutton",
                            command=self._on_schedule_change).pack(side="left", padx=(0, 4))
            self.day_vars.append(var)

        # ── Control Buttons ──────────────────────────────────────
        btn_frame = ttk.Frame(root, style="BG.TFrame")
        btn_frame.pack(fill="x", padx=24, pady=(14, 0))

        self.btn_start = ttk.Button(btn_frame, text="▶  START",
                                    style="Start.TButton", command=self._cmd_start)
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_pause = ttk.Button(btn_frame, text="⏸  PAUSE",
                                    style="Pause.TButton", command=self._cmd_pause)
        self.btn_pause.pack(side="left", expand=True, fill="x", padx=4)

        self.btn_stop = ttk.Button(btn_frame, text="⏹  STOP",
                                   style="Stop.TButton", command=self._cmd_stop)
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # ── Activity Log (MUCH BIGGER) ───────────────────────────
        log_card = tk.Frame(root, bg=_C["bg_card_alt"],
                            highlightbackground=_C["border"],
                            highlightthickness=1)
        log_card.pack(fill="both", expand=True, padx=24, pady=(12, 20))

        log_header = ttk.Frame(log_card, style="CardAlt.TFrame")
        log_header.pack(fill="x", padx=16, pady=(10, 4))

        ttk.Label(log_header, text="📋  ACTIVITY LOG",
                  style="SectionAlt.TLabel").pack(side="left")

        self.log_count_label = ttk.Label(log_header, text="0 entries",
                                         style="Dim.TLabel")
        self.log_count_label.configure(background=_C["bg_card_alt"])
        self.log_count_label.pack(side="right")

        # Log text with scrollbar
        log_container = tk.Frame(log_card, bg=_C["log_bg"])
        log_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log_scrollbar = tk.Scrollbar(log_container, orient="vertical",
                                          bg=_C["bg_card_alt"],
                                          troughcolor=_C["log_bg"],
                                          activebackground=_C["accent"])
        self.log_scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(
            log_container, wrap="word",
            bg=_C["log_bg"], fg=_C["fg_mid"],
            font=_FONT_LOG, relief="flat", bd=8,
            insertbackground=_C["green"], highlightthickness=0,
            state="disabled", cursor="arrow",
            yscrollcommand=self.log_scrollbar.set,
            spacing1=2, spacing3=2,
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_scrollbar.config(command=self.log_text.yview)

        # Configure log text tags for colored entries
        self.log_text.tag_configure("ok", foreground=_C["log_ok"])
        self.log_text.tag_configure("warn", foreground=_C["log_warn"])
        self.log_text.tag_configure("fail", foreground=_C["log_fail"])
        self.log_text.tag_configure("info", foreground=_C["fg_dim"])
        self.log_text.tag_configure("time", foreground=_C["log_time"])
        self.log_text.tag_configure("highlight", foreground=_C["green"])

        self._log_entry_count = 0

        self._update_buttons()

    # ═════════════════════════════════════════════════════════════
    #  PERMISSION WARNING
    # ═════════════════════════════════════════════════════════════

    def _show_permission_warning(self, msg: str = "") -> None:
        if msg:
            self.warn_msg_label.configure(text=msg)
        self.warn_frame.pack(fill="x", padx=24, pady=(10, 0),
                             after=self.root.winfo_children()[0])
        # Highlight the card border red
        self._status_card.configure(highlightbackground=_C["warn_border"])

    def _hide_permission_warning(self) -> None:
        self.warn_frame.pack_forget()
        self._status_card.configure(highlightbackground=_C["border"])

    @staticmethod
    def _open_accessibility_settings() -> None:
        try:
            subprocess.Popen([
                "open", "x-apple.systempreferences:"
                "com.apple.preference.security?Privacy_Accessibility"
            ])
        except OSError:
            pass

    # ═════════════════════════════════════════════════════════════
    #  SETTINGS ↔ UI
    # ═════════════════════════════════════════════════════════════

    def _apply_settings(self) -> None:
        cfg = self.cfg
        mode = cfg.get("duration_mode", "infinite")
        hours = cfg.get("duration_hours", 8)
        if mode == "infinite":
            self.duration_var.set("Infinite")
        elif mode == "custom":
            self.duration_var.set("Custom")
            self.custom_hours.set(str(hours))
        else:
            target = hours * 3600
            found = False
            for label, secs in self.DURATION_OPTIONS.items():
                if secs == target:
                    self.duration_var.set(label)
                    found = True
                    break
            if not found:
                self.duration_var.set("Custom")
                self.custom_hours.set(str(hours))

        self.interval_var.set(cfg.get("interval_seconds", 60))
        self._on_interval_change(None)

        self.schedule_enabled_var.set(cfg.get("schedule_enabled", False))
        self.sched_start_var.set(cfg.get("schedule_start", "09:00"))
        self.sched_stop_var.set(cfg.get("schedule_stop", "18:00"))
        active_days = cfg.get("schedule_days", [0, 1, 2, 3, 4])
        for i, var in enumerate(self.day_vars):
            var.set(i in active_days)

        self.engine.enable_mouse      = cfg.get("simulation_mouse", True)
        self.engine.enable_keyboard   = cfg.get("simulation_keyboard", True)
        self.engine.enable_caffeinate = cfg.get("simulation_caffeinate", True)
        self._sync_scheduler_config()

    def _save_settings(self) -> None:
        cfg = self.cfg
        dur = self.duration_var.get()
        if dur == "Infinite":
            cfg["duration_mode"] = "infinite"
        elif dur == "Custom":
            cfg["duration_mode"] = "custom"
            try:
                cfg["duration_hours"] = float(self.custom_hours.get())
            except ValueError:
                cfg["duration_hours"] = 1
        else:
            cfg["duration_mode"] = "preset"
            cfg["duration_hours"] = self.DURATION_OPTIONS[dur] / 3600

        cfg["interval_seconds"]   = self.interval_var.get()
        cfg["schedule_enabled"]   = self.schedule_enabled_var.get()
        cfg["schedule_start"]     = self.sched_start_var.get()
        cfg["schedule_stop"]      = self.sched_stop_var.get()
        cfg["schedule_days"]      = [i for i, v in enumerate(self.day_vars) if v.get()]
        settings.save(cfg)

    # ═════════════════════════════════════════════════════════════
    #  UI CALLBACKS
    # ═════════════════════════════════════════════════════════════

    def _on_duration_change(self) -> None:
        self._save_settings()

    def _on_interval_change(self, _) -> None:
        val = self.interval_var.get()
        if val < 60:
            txt = f"Every {val} seconds"
        else:
            m, s = divmod(val, 60)
            txt = f"Every {m}m {s}s" if s else f"Every {m} minute{'s' if m > 1 else ''}"
        self.interval_display.configure(text=txt)
        self._save_settings()

    def _on_schedule_toggle(self) -> None:
        self._sync_scheduler_config()
        if self.schedule_enabled_var.get():
            self.scheduler.start()
        else:
            self.scheduler.stop()
        self._save_settings()

    def _on_schedule_change(self) -> None:
        self._sync_scheduler_config()
        self._save_settings()

    def _sync_scheduler_config(self) -> None:
        self.scheduler.enabled        = self.schedule_enabled_var.get()
        self.scheduler.start_time_str = self.sched_start_var.get()
        self.scheduler.stop_time_str  = self.sched_stop_var.get()
        self.scheduler.active_days    = [i for i, v in enumerate(self.day_vars) if v.get()]

    # ── Engine controls ──────────────────────────────────────────

    def _cmd_start(self) -> None:
        dur = self.duration_var.get()
        if dur == "Infinite":
            self.engine.duration_seconds = None
        elif dur == "Custom":
            try:
                hrs = float(self.custom_hours.get())
            except ValueError:
                hrs = 1
            self.engine.duration_seconds = hrs * 3600
        else:
            self.engine.duration_seconds = self.DURATION_OPTIONS[dur]

        self.engine.interval_seconds = self.interval_var.get()
        self._save_settings()
        self._cycle_count = 0

        if self.engine.state == ActivityEngine.STATE_PAUSED:
            self.engine.resume()
        else:
            self.engine.start()

    def _cmd_pause(self) -> None:
        self.engine.pause()

    def _cmd_stop(self) -> None:
        self.engine.stop()

    # ── Engine callbacks (from engine thread → main thread) ──────

    def _on_state_change(self, state: str) -> None:
        self.root.after(0, self._update_status, state)

    def _on_activity(self, message: str) -> None:
        self.root.after(0, self._append_log, message)

    def _on_duration_end(self) -> None:
        self.root.after(0, self.engine.stop)

    def _on_permission_issue(self, msg: str) -> None:
        self.root.after(0, self._show_permission_warning, msg)

    # ── Schedule callbacks ───────────────────────────────────────

    def _schedule_start(self) -> None:
        self.root.after(0, self._cmd_start)
        self.root.after(0, self._append_log,
                        "📅 Schedule auto-started the engine")

    def _schedule_stop(self) -> None:
        self.root.after(0, self._cmd_stop)
        self.root.after(0, self._append_log,
                        "📅 Schedule auto-stopped the engine")

    # ═════════════════════════════════════════════════════════════
    #  UI UPDATES
    # ═════════════════════════════════════════════════════════════

    def _update_status(self, state: str) -> None:
        labels = {
            ActivityEngine.STATE_ACTIVE:  "ACTIVE",
            ActivityEngine.STATE_PAUSED:  "PAUSED",
            ActivityEngine.STATE_STOPPED: "STOPPED",
        }
        colours = {
            ActivityEngine.STATE_ACTIVE:  _C["green"],
            ActivityEngine.STATE_PAUSED:  _C["amber"],
            ActivityEngine.STATE_STOPPED: _C["fg_dim"],
        }
        border_colours = {
            ActivityEngine.STATE_ACTIVE:  _C["green"],
            ActivityEngine.STATE_PAUSED:  _C["amber"],
            ActivityEngine.STATE_STOPPED: _C["border"],
        }
        self.status_label.configure(
            text=labels.get(state, "STOPPED"),
            foreground=colours.get(state, _C["fg_dim"]))
        self.status_dot.set_state(state)
        self._status_card.configure(
            highlightbackground=border_colours.get(state, _C["border"]))
        self._update_buttons()

    def _update_buttons(self) -> None:
        state = self.engine.state
        if state == ActivityEngine.STATE_STOPPED:
            self.btn_start.state(["!disabled"])
            self.btn_pause.state(["disabled"])
            self.btn_stop.state(["disabled"])
        elif state == ActivityEngine.STATE_ACTIVE:
            self.btn_start.state(["disabled"])
            self.btn_pause.state(["!disabled"])
            self.btn_stop.state(["!disabled"])
        elif state == ActivityEngine.STATE_PAUSED:
            self.btn_start.state(["!disabled"])
            self.btn_pause.state(["disabled"])
            self.btn_stop.state(["!disabled"])

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")

        # Determine tag based on message content
        tag = "info"
        if "✅" in message:
            tag = "ok"
            self._cycle_count += 1
            self.cycle_label.configure(text=f"{self._cycle_count} cycles")
        elif "⚠" in message:
            tag = "warn"
        elif "❌" in message or "FAILED" in message:
            tag = "fail"
        elif "🟢" in message or "▶" in message:
            tag = "highlight"

        self.log_text.insert("1.0", message + "\n", tag)

        # Cap log size
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > 500:
            self.log_text.delete("400.0", "end")

        self.log_text.configure(state="disabled")

        self._log_entry_count += 1
        self.log_count_label.configure(text=f"{self._log_entry_count} entries")

    def _format_time(self, seconds: float) -> str:
        s = int(seconds)
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _tick(self) -> None:
        if self.engine.state in (ActivityEngine.STATE_ACTIVE,
                                 ActivityEngine.STATE_PAUSED):
            remaining = self.engine.get_remaining_seconds()
            if remaining is not None:
                colour = _C["red"] if remaining < 60 else (
                    _C["amber"] if remaining < 300 else _C["green"])
                self.timer_label.configure(
                    text=self._format_time(remaining),
                    foreground=colour)
            else:
                elapsed = self.engine.get_elapsed_seconds()
                self.timer_label.configure(
                    text=self._format_time(elapsed),
                    foreground=_C["green"])
        else:
            self.timer_label.configure(text="00:00:00",
                                       foreground=_C["fg_dim"])
        self.root.after(1000, self._tick)

    # ── Window close ─────────────────────────────────────────────

    def _on_close(self) -> None:
        self.engine.stop()
        self.scheduler.stop()
        self._save_settings()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
