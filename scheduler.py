"""
GoGreen — Schedule Manager
Auto-starts and auto-stops the activity engine based on time-of-day
and day-of-week rules.  Zero external dependencies.
"""

import threading
import time
from datetime import datetime
from typing import Callable, Optional


class ScheduleManager:
    """
    Lightweight scheduler that checks the clock every 30 s and fires
    callbacks when the current time enters or exits the active window.

    Config attributes (set before calling start):
        enabled        – master on/off
        start_time_str – e.g. "09:00"
        stop_time_str  – e.g. "18:00"
        active_days    – list of ints, 0 = Monday … 6 = Sunday
    """

    def __init__(self):
        self.enabled: bool = False
        self.start_time_str: str = "09:00"
        self.stop_time_str: str = "18:00"
        self.active_days: list = [0, 1, 2, 3, 4]  # Mon–Fri

        # Callbacks
        self.on_enter_window: Optional[Callable] = None   # () → None
        self.on_exit_window:  Optional[Callable] = None   # () → None

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._was_inside: bool = False

    # ── Public API ───────────────────────────────────────────────

    def start(self) -> None:
        """Begin monitoring the schedule in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._was_inside = False
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop monitoring."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    def is_inside_window(self) -> bool:
        """Check whether *right now* falls inside the active schedule."""
        if not self.enabled:
            return False

        now = datetime.now()
        # Day-of-week check (Monday=0 in Python's weekday())
        if now.weekday() not in self.active_days:
            return False

        # Time-of-day check
        try:
            start_h, start_m = map(int, self.start_time_str.split(":"))
            stop_h, stop_m   = map(int, self.stop_time_str.split(":"))
        except (ValueError, AttributeError):
            return False

        start_minutes = start_h * 60 + start_m
        stop_minutes  = stop_h * 60 + stop_m
        now_minutes   = now.hour * 60 + now.minute

        if start_minutes <= stop_minutes:
            # Normal window  e.g. 09:00 – 18:00
            return start_minutes <= now_minutes < stop_minutes
        else:
            # Overnight window  e.g. 22:00 – 06:00
            return now_minutes >= start_minutes or now_minutes < stop_minutes

    # ── Internal ─────────────────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            if self.enabled:
                inside = self.is_inside_window()
                if inside and not self._was_inside:
                    # Just entered the active window
                    if self.on_enter_window:
                        try:
                            self.on_enter_window()
                        except Exception:
                            pass
                elif not inside and self._was_inside:
                    # Just left the active window
                    if self.on_exit_window:
                        try:
                            self.on_exit_window()
                        except Exception:
                            pass
                self._was_inside = inside

            self._stop_event.wait(timeout=30)
