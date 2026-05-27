"""
GoGreen — Premium Dark-Theme GUI
Beautiful tkinter interface that works on both macOS and Windows.
ZERO external dependencies — standard library only.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional

from engine import ActivityEngine
from scheduler import ScheduleManager
import settings

# ═══════════════════════════════════════════════════════════════════
#  COLOUR PALETTE
# ═══════════════════════════════════════════════════════════════════
_C = {
    "bg":           "#0f0f1a",
    "bg_card":      "#1a1a2e",
    "bg_input":     "#252540",
    "bg_hover":     "#2a2a4a",
    "fg":           "#e0e0e8",
    "fg_dim":       "#8888a0",
    "green":        "#00e676",
    "green_dark":   "#00a854",
    "green_glow":   "#00e67640",
    "amber":        "#ffab00",
    "red":          "#ff5252",
    "accent":       "#7c4dff",
    "border":       "#2e2e48",
}

# ═══════════════════════════════════════════════════════════════════
#  HELPER: Animated pulsing dot on a Canvas
# ═══════════════════════════════════════════════════════════════════

class StatusDot(tk.Canvas):
    """A small canvas that draws a pulsing coloured circle."""

    _COLOURS = {
        ActivityEngine.STATE_ACTIVE:  _C["green"],
        ActivityEngine.STATE_PAUSED:  _C["amber"],
        ActivityEngine.STATE_STOPPED: _C["fg_dim"],
    }

    def __init__(self, master, size: int = 18, **kw):
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
        # Glow ring
        if glow > 0:
            gr = r + 3 * glow
            self.create_oval(
                cx - gr, cy - gr, cx + gr, cy + gr,
                fill="", outline=self._colour,
                width=max(1, int(2 * glow)),
            )
        # Solid dot
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         fill=self._colour, outline="")

    def _animate(self) -> None:
        if not self._animating:
            return
        import math
        self._glow_phase += 0.12
        glow = (math.sin(self._glow_phase) + 1) / 2  # 0 → 1
        self._draw(glow)
        self.after(60, self._animate)


# ═══════════════════════════════════════════════════════════════════
#  MAIN APPLICATION WINDOW
# ═══════════════════════════════════════════════════════════════════

class GoGreenApp:
    """Premium dark-theme GUI for GoGreen."""

    DURATION_OPTIONS = {
        "2 hours":   2 * 3600,
        "4 hours":   4 * 3600,
        "8 hours":   8 * 3600,
        "12 hours": 12 * 3600,
        "Infinite":  None,
    }

    DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self):
        # ── Core objects ─────────────────────────────────────────
        self.engine = ActivityEngine()
        self.scheduler = ScheduleManager()
        self.cfg = settings.load()

        # Wire engine callbacks
        self.engine.on_state_change = self._on_state_change
        self.engine.on_activity     = self._on_activity
        self.engine.on_duration_end = self._on_duration_end

        # Wire scheduler callbacks
        self.scheduler.on_enter_window = self._schedule_start
        self.scheduler.on_exit_window  = self._schedule_stop

        # ── Root window ──────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("GoGreen")
        self.root.configure(bg=_C["bg"])
        self.root.minsize(480, 700)
        self.root.resizable(False, False)

        # Centre window on screen
        w, h = 480, 720
        sx = self.root.winfo_screenwidth()
        sy = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sx-w)//2}+{(sy-h)//2}")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Force window to front on launch ──────────────────────
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(1000, lambda: self.root.attributes("-topmost", False))

        # macOS: bring Python app to foreground in Dock
        if sys.platform == "darwin":
            try:
                import subprocess
                subprocess.Popen([
                    "osascript", "-e",
                    'tell application "System Events" to set frontmost '
                    'of the first process whose unix id is '
                    f'{os.getpid()} to true'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        # ── Build ttk styles ────────────────────────────────────
        self._build_styles()

        # ── Build UI ─────────────────────────────────────────────
        self._build_ui()

        # ── Apply saved settings ─────────────────────────────────
        self._apply_settings()

        # ── Start scheduler if enabled ───────────────────────────
        if self.cfg.get("schedule_enabled", False):
            self.scheduler.start()

        # ── Timer update loop ────────────────────────────────────
        self._tick()

    # ═════════════════════════════════════════════════════════════
    #  STYLES
    # ═════════════════════════════════════════════════════════════

    def _build_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        # Frames
        style.configure("Card.TFrame", background=_C["bg_card"])
        style.configure("BG.TFrame", background=_C["bg"])

        # Labels
        style.configure("Title.TLabel", background=_C["bg"],
                         foreground=_C["green"], font=("Helvetica Neue", 22, "bold"))
        style.configure("Status.TLabel", background=_C["bg_card"],
                         foreground=_C["fg"], font=("Helvetica Neue", 14, "bold"))
        style.configure("Timer.TLabel", background=_C["bg_card"],
                         foreground=_C["green"], font=("Menlo", 28, "bold"))
        style.configure("Card.TLabel", background=_C["bg_card"],
                         foreground=_C["fg"], font=("Helvetica Neue", 12))
        style.configure("CardDim.TLabel", background=_C["bg_card"],
                         foreground=_C["fg_dim"], font=("Helvetica Neue", 11))
        style.configure("Section.TLabel", background=_C["bg_card"],
                         foreground=_C["accent"], font=("Helvetica Neue", 11, "bold"))

        # Buttons
        style.configure("Start.TButton", font=("Helvetica Neue", 13, "bold"),
                         foreground=_C["bg"], background=_C["green"],
                         borderwidth=0, padding=(20, 10))
        style.map("Start.TButton",
                  background=[("active", _C["green_dark"])])

        style.configure("Pause.TButton", font=("Helvetica Neue", 13, "bold"),
                         foreground=_C["bg"], background=_C["amber"],
                         borderwidth=0, padding=(20, 10))
        style.map("Pause.TButton",
                  background=[("active", "#e69500")])

        style.configure("Stop.TButton", font=("Helvetica Neue", 13, "bold"),
                         foreground="#fff", background=_C["red"],
                         borderwidth=0, padding=(20, 10))
        style.map("Stop.TButton",
                  background=[("active", "#d32f2f")])

        # Scale / Slider
        style.configure("Green.Horizontal.TScale", background=_C["bg_card"],
                         troughcolor=_C["bg_input"])

        # Radiobutton
        style.configure("Card.TRadiobutton", background=_C["bg_card"],
                         foreground=_C["fg"], font=("Helvetica Neue", 12))

        # Checkbutton
        style.configure("Card.TCheckbutton", background=_C["bg_card"],
                         foreground=_C["fg"], font=("Helvetica Neue", 12))

    # ═════════════════════════════════════════════════════════════
    #  BUILD UI
    # ═════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        root = self.root

        # ── Title Bar ────────────────────────────────────────────
        title_frame = ttk.Frame(root, style="BG.TFrame")
        title_frame.pack(fill="x", padx=20, pady=(18, 0))

        ttk.Label(title_frame, text="🟢 GoGreen", style="Title.TLabel").pack(side="left")
        platform_text = "macOS" if sys.platform == "darwin" else "Windows"
        ttk.Label(title_frame, text=platform_text,
                  style="CardDim.TLabel").pack(side="right", pady=(6, 0))

        # ── Status Card ──────────────────────────────────────────
        status_card = ttk.Frame(root, style="Card.TFrame")
        status_card.pack(fill="x", padx=20, pady=(14, 0), ipady=14)

        status_row = ttk.Frame(status_card, style="Card.TFrame")
        status_row.pack(fill="x", padx=18, pady=(8, 0))

        self.status_dot = StatusDot(status_row, size=18)
        self.status_dot.pack(side="left", padx=(0, 8))

        self.status_label = ttk.Label(status_row, text="STOPPED", style="Status.TLabel")
        self.status_label.pack(side="left")

        self.timer_label = ttk.Label(status_card, text="00:00:00", style="Timer.TLabel")
        self.timer_label.pack(pady=(8, 8))

        # ── Duration Card ────────────────────────────────────────
        dur_card = ttk.Frame(root, style="Card.TFrame")
        dur_card.pack(fill="x", padx=20, pady=(10, 0), ipady=10)

        ttk.Label(dur_card, text="⏱  DURATION", style="Section.TLabel").pack(
            anchor="w", padx=18, pady=(8, 4))

        self.duration_var = tk.StringVar(value="Infinite")

        dur_grid = ttk.Frame(dur_card, style="Card.TFrame")
        dur_grid.pack(fill="x", padx=18)

        for i, label in enumerate(self.DURATION_OPTIONS.keys()):
            r, c = divmod(i, 3)
            rb = ttk.Radiobutton(dur_grid, text=label, value=label,
                                 variable=self.duration_var,
                                 style="Card.TRadiobutton",
                                 command=self._on_duration_change)
            rb.grid(row=r, column=c, sticky="w", padx=(0, 16), pady=2)

        # Custom entry row
        custom_row = ttk.Frame(dur_card, style="Card.TFrame")
        custom_row.pack(fill="x", padx=18, pady=(4, 0))
        ttk.Radiobutton(custom_row, text="Custom:", value="Custom",
                        variable=self.duration_var,
                        style="Card.TRadiobutton",
                        command=self._on_duration_change).pack(side="left")
        self.custom_hours = tk.StringVar(value="1")
        self.custom_entry = tk.Entry(custom_row, textvariable=self.custom_hours,
                                     width=5, bg=_C["bg_input"], fg=_C["fg"],
                                     insertbackground=_C["fg"],
                                     font=("Helvetica Neue", 12),
                                     relief="flat", bd=4)
        self.custom_entry.pack(side="left", padx=(6, 4))
        ttk.Label(custom_row, text="hours", style="CardDim.TLabel").pack(side="left")

        # ── Interval Card ────────────────────────────────────────
        int_card = ttk.Frame(root, style="Card.TFrame")
        int_card.pack(fill="x", padx=20, pady=(10, 0), ipady=10)

        ttk.Label(int_card, text="🔄  ACTIVITY INTERVAL", style="Section.TLabel").pack(
            anchor="w", padx=18, pady=(8, 4))

        slider_row = ttk.Frame(int_card, style="Card.TFrame")
        slider_row.pack(fill="x", padx=18)

        ttk.Label(slider_row, text="30s", style="CardDim.TLabel").pack(side="left")

        self.interval_var = tk.IntVar(value=60)
        self.interval_scale = ttk.Scale(
            slider_row, from_=30, to=300,
            variable=self.interval_var,
            orient="horizontal",
            style="Green.Horizontal.TScale",
            command=self._on_interval_change,
        )
        self.interval_scale.pack(side="left", fill="x", expand=True, padx=6)

        ttk.Label(slider_row, text="5m", style="CardDim.TLabel").pack(side="left")

        self.interval_display = ttk.Label(int_card, text="Every 60 seconds",
                                          style="Card.TLabel")
        self.interval_display.pack(padx=18, pady=(2, 0), anchor="w")

        # ── Schedule Card ────────────────────────────────────────
        sched_card = ttk.Frame(root, style="Card.TFrame")
        sched_card.pack(fill="x", padx=20, pady=(10, 0), ipady=10)

        ttk.Label(sched_card, text="📅  SCHEDULE", style="Section.TLabel").pack(
            anchor="w", padx=18, pady=(8, 4))

        self.schedule_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(sched_card, text="Enable auto-schedule",
                        variable=self.schedule_enabled_var,
                        style="Card.TCheckbutton",
                        command=self._on_schedule_toggle).pack(
            anchor="w", padx=18)

        time_row = ttk.Frame(sched_card, style="Card.TFrame")
        time_row.pack(fill="x", padx=18, pady=(4, 0))

        ttk.Label(time_row, text="Start:", style="Card.TLabel").pack(side="left")
        self.sched_start_var = tk.StringVar(value="09:00")
        self.sched_start_entry = tk.Entry(
            time_row, textvariable=self.sched_start_var, width=6,
            bg=_C["bg_input"], fg=_C["fg"], insertbackground=_C["fg"],
            font=("Menlo", 12), relief="flat", bd=4, justify="center")
        self.sched_start_entry.pack(side="left", padx=(4, 16))

        ttk.Label(time_row, text="Stop:", style="Card.TLabel").pack(side="left")
        self.sched_stop_var = tk.StringVar(value="18:00")
        self.sched_stop_entry = tk.Entry(
            time_row, textvariable=self.sched_stop_var, width=6,
            bg=_C["bg_input"], fg=_C["fg"], insertbackground=_C["fg"],
            font=("Menlo", 12), relief="flat", bd=4, justify="center")
        self.sched_stop_entry.pack(side="left", padx=(4, 0))

        # Day checkboxes
        day_row = ttk.Frame(sched_card, style="Card.TFrame")
        day_row.pack(fill="x", padx=18, pady=(6, 0))

        self.day_vars = []
        for i, label in enumerate(self.DAY_LABELS):
            var = tk.BooleanVar(value=(i < 5))  # Mon–Fri default
            cb = ttk.Checkbutton(day_row, text=label, variable=var,
                                 style="Card.TCheckbutton",
                                 command=self._on_schedule_change)
            cb.pack(side="left", padx=(0, 4))
            self.day_vars.append(var)

        # ── Control Buttons ──────────────────────────────────────
        btn_frame = ttk.Frame(root, style="BG.TFrame")
        btn_frame.pack(fill="x", padx=20, pady=(16, 0))

        self.btn_start = ttk.Button(btn_frame, text="▶  START",
                                    style="Start.TButton", command=self._cmd_start)
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_pause = ttk.Button(btn_frame, text="⏸  PAUSE",
                                    style="Pause.TButton", command=self._cmd_pause)
        self.btn_pause.pack(side="left", expand=True, fill="x", padx=4)

        self.btn_stop = ttk.Button(btn_frame, text="⏹  STOP",
                                   style="Stop.TButton", command=self._cmd_stop)
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # ── Activity Log ─────────────────────────────────────────
        log_card = ttk.Frame(root, style="Card.TFrame")
        log_card.pack(fill="both", expand=True, padx=20, pady=(12, 18))

        ttk.Label(log_card, text="📋  ACTIVITY LOG", style="Section.TLabel").pack(
            anchor="w", padx=18, pady=(8, 4))

        self.log_text = tk.Text(
            log_card, height=6, wrap="word",
            bg=_C["bg_input"], fg=_C["fg_dim"],
            font=("Menlo", 10), relief="flat", bd=8,
            insertbackground=_C["fg"], highlightthickness=0,
            state="disabled",
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initial button state
        self._update_buttons()

    # ═════════════════════════════════════════════════════════════
    #  SETTINGS ↔ UI
    # ═════════════════════════════════════════════════════════════

    def _apply_settings(self) -> None:
        """Load saved settings into the UI widgets."""
        cfg = self.cfg

        # Duration
        mode = cfg.get("duration_mode", "infinite")
        hours = cfg.get("duration_hours", 8)
        if mode == "infinite":
            self.duration_var.set("Infinite")
        elif mode == "custom":
            self.duration_var.set("Custom")
            self.custom_hours.set(str(hours))
        else:
            # Find matching preset
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

        # Interval
        self.interval_var.set(cfg.get("interval_seconds", 60))
        self._on_interval_change(None)

        # Schedule
        self.schedule_enabled_var.set(cfg.get("schedule_enabled", False))
        self.sched_start_var.set(cfg.get("schedule_start", "09:00"))
        self.sched_stop_var.set(cfg.get("schedule_stop", "18:00"))
        active_days = cfg.get("schedule_days", [0, 1, 2, 3, 4])
        for i, var in enumerate(self.day_vars):
            var.set(i in active_days)

        # Engine config
        self.engine.enable_mouse      = cfg.get("simulation_mouse", True)
        self.engine.enable_keyboard   = cfg.get("simulation_keyboard", True)
        self.engine.enable_caffeinate = cfg.get("simulation_caffeinate", True)

        # Sync scheduler config
        self._sync_scheduler_config()

    def _save_settings(self) -> None:
        """Gather current UI state into cfg dict and persist."""
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
            m = val // 60
            s = val % 60
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

    # ── Engine control buttons ───────────────────────────────────

    def _cmd_start(self) -> None:
        # Configure engine from UI
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

        if self.engine.state == ActivityEngine.STATE_PAUSED:
            self.engine.resume()
        else:
            self.engine.start()

    def _cmd_pause(self) -> None:
        self.engine.pause()

    def _cmd_stop(self) -> None:
        self.engine.stop()

    # ── Engine callbacks (called from engine thread) ─────────────

    def _on_state_change(self, state: str) -> None:
        # Schedule UI update on main thread
        self.root.after(0, self._update_status, state)

    def _on_activity(self, message: str) -> None:
        self.root.after(0, self._append_log, message)

    def _on_duration_end(self) -> None:
        self.root.after(0, self.engine.stop)

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
        self.status_label.configure(
            text=labels.get(state, "STOPPED"),
            foreground=colours.get(state, _C["fg_dim"]),
        )
        self.status_dot.set_state(state)
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
            self.btn_start.state(["!disabled"])  # acts as resume
            self.btn_pause.state(["disabled"])
            self.btn_stop.state(["!disabled"])

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("1.0", message + "\n")
        # Keep log from growing unbounded
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > 200:
            self.log_text.delete("200.0", "end")
        self.log_text.configure(state="disabled")

    def _format_time(self, seconds: float) -> str:
        s = int(seconds)
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # ── Periodic timer update ────────────────────────────────────

    def _tick(self) -> None:
        if self.engine.state in (ActivityEngine.STATE_ACTIVE,
                                 ActivityEngine.STATE_PAUSED):
            remaining = self.engine.get_remaining_seconds()
            if remaining is not None:
                self.timer_label.configure(
                    text=self._format_time(remaining),
                    foreground=_C["amber"] if remaining < 300 else _C["green"],
                )
            else:
                elapsed = self.engine.get_elapsed_seconds()
                self.timer_label.configure(
                    text=self._format_time(elapsed),
                    foreground=_C["green"],
                )
        else:
            self.timer_label.configure(text="00:00:00", foreground=_C["fg_dim"])

        self.root.after(1000, self._tick)

    # ── Window close ─────────────────────────────────────────────

    def _on_close(self) -> None:
        self.engine.stop()
        self.scheduler.stop()
        self._save_settings()
        self.root.destroy()

    # ── Run ──────────────────────────────────────────────────────

    def run(self) -> None:
        self.root.mainloop()
