"""
GoGreen — Cross-Platform Activity Simulation Engine
Keeps MS Teams status green by simulating subtle user activity.

ZERO external dependencies:
  macOS  → osascript (CoreGraphics / System Events) + caffeinate
  Windows → ctypes (user32.dll / kernel32.dll)
  Both   → Python standard library only
"""

import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Callable, Optional

# ── Platform-specific imports (all standard library) ─────────────
_IS_MAC = sys.platform == "darwin"
_IS_WIN = sys.platform == "win32"

if _IS_WIN:
    import ctypes  # standard library — talks to Windows DLLs directly

    class _POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class ActivityEngine:
    """
    Background engine that periodically simulates user activity
    to prevent MS Teams from setting status to 'Away'.

    100 % zero-install on both macOS and Windows:
      macOS  : osascript (JXA / AppleScript) + caffeinate
      Windows: ctypes → user32.dll + kernel32.dll
    """

    # ── State constants ──────────────────────────────────────────
    STATE_STOPPED = "stopped"
    STATE_ACTIVE  = "active"
    STATE_PAUSED  = "paused"

    def __init__(self):
        self.state: str = self.STATE_STOPPED
        self._thread: Optional[threading.Thread] = None
        self._stop_event  = threading.Event()
        self._pause_event = threading.Event()

        # macOS-only: caffeinate subprocess handle
        self._caffeinate_proc: Optional[subprocess.Popen] = None

        # Configuration (set before calling start)
        self.interval_seconds: int   = 60
        self.enable_mouse: bool      = True
        self.enable_keyboard: bool   = True
        self.enable_caffeinate: bool = True
        self.duration_seconds: Optional[float] = None  # None = infinite

        # Callbacks — the GUI hooks into these
        self.on_state_change: Optional[Callable] = None  # (state: str)
        self.on_activity:     Optional[Callable] = None  # (message: str)
        self.on_duration_end: Optional[Callable] = None  # ()

        self._start_time: float = 0.0

    # ── Public API ───────────────────────────────────────────────

    def start(self) -> None:
        """Start the activity simulation engine."""
        if self.state == self.STATE_ACTIVE:
            return

        self._stop_event.clear()
        self._pause_event.clear()
        self._start_time = time.time()

        # Prevent system / display sleep
        if self.enable_caffeinate:
            self._prevent_sleep_start()

        # Launch simulation thread
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        self.state = self.STATE_ACTIVE
        self._emit_state_change()
        self._emit_activity("🟢 Engine started")

    def pause(self) -> None:
        """Pause activity simulation."""
        if self.state != self.STATE_ACTIVE:
            return
        self._pause_event.set()
        self.state = self.STATE_PAUSED
        self._emit_state_change()
        self._emit_activity("⏸ Engine paused")

    def resume(self) -> None:
        """Resume from paused state."""
        if self.state != self.STATE_PAUSED:
            return
        self._pause_event.clear()
        self.state = self.STATE_ACTIVE
        self._emit_state_change()
        self._emit_activity("▶ Engine resumed")

    def stop(self) -> None:
        """Stop the engine completely."""
        if self.state == self.STATE_STOPPED:
            return
        self._stop_event.set()
        self._pause_event.clear()
        self._prevent_sleep_stop()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

        self.state = self.STATE_STOPPED
        self._emit_state_change()
        self._emit_activity("⏹ Engine stopped")

    def get_elapsed_seconds(self) -> float:
        if self.state == self.STATE_STOPPED:
            return 0.0
        return time.time() - self._start_time

    def get_remaining_seconds(self) -> Optional[float]:
        if self.duration_seconds is None:
            return None
        remaining = self.duration_seconds - self.get_elapsed_seconds()
        return max(0.0, remaining)

    # ── Simulation Loop ──────────────────────────────────────────

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            # Honour pause
            while self._pause_event.is_set() and not self._stop_event.is_set():
                time.sleep(0.5)
            if self._stop_event.is_set():
                break

            # Check duration limit
            if self.duration_seconds is not None:
                if self.get_elapsed_seconds() >= self.duration_seconds:
                    self._emit_activity("⏰ Duration reached — auto-stopping")
                    if self.on_duration_end:
                        self.on_duration_end()
                    break

            # Perform one simulation cycle
            self._simulate_activity()

            # Interruptible sleep until next cycle
            self._stop_event.wait(timeout=self.interval_seconds)

    def _simulate_activity(self) -> None:
        actions = []
        if self.enable_mouse:
            if self._wiggle_mouse():
                actions.append("mouse wiggle")
        if self.enable_keyboard:
            if self._press_shift():
                actions.append("Shift key")
        if actions:
            ts = datetime.now().strftime("%H:%M:%S")
            self._emit_activity(f"✅ {ts} — {' + '.join(actions)}")

    # ══════════════════════════════════════════════════════════════
    #  PLATFORM-SPECIFIC SIMULATION  (zero external dependencies)
    # ══════════════════════════════════════════════════════════════

    # ── Mouse Wiggle ─────────────────────────────────────────────

    @staticmethod
    def _wiggle_mouse() -> bool:
        if _IS_MAC:
            return ActivityEngine._wiggle_mouse_mac()
        elif _IS_WIN:
            return ActivityEngine._wiggle_mouse_win()
        return False

    @staticmethod
    def _wiggle_mouse_mac() -> bool:
        """Move mouse 1 px right then back using macOS CoreGraphics via JXA."""
        script = """
        ObjC.import('CoreGraphics');
        var event = $.CGEventCreate($());
        var loc   = $.CGEventGetLocation(event);
        var x = loc.x, y = loc.y;

        var m1 = $.CGEventCreateMouseEvent($(), $.kCGEventMouseMoved,
                     $.CGPointMake(x + 1, y), 0);
        $.CGEventPost($.kCGHIDEventTap, m1);
        delay(0.05);

        var m2 = $.CGEventCreateMouseEvent($(), $.kCGEventMouseMoved,
                     $.CGPointMake(x, y), 0);
        $.CGEventPost($.kCGHIDEventTap, m2);
        """
        try:
            r = subprocess.run(
                ["osascript", "-l", "JavaScript", "-e", script],
                capture_output=True, timeout=5,
            )
            return r.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    @staticmethod
    def _wiggle_mouse_win() -> bool:
        """Move mouse 1 px right then back using Windows user32.dll via ctypes."""
        try:
            pt = _POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            ctypes.windll.user32.SetCursorPos(pt.x + 1, pt.y)
            time.sleep(0.05)
            ctypes.windll.user32.SetCursorPos(pt.x, pt.y)
            return True
        except Exception:
            return False

    # ── Keyboard (Shift key) ─────────────────────────────────────

    @staticmethod
    def _press_shift() -> bool:
        if _IS_MAC:
            return ActivityEngine._press_shift_mac()
        elif _IS_WIN:
            return ActivityEngine._press_shift_win()
        return False

    @staticmethod
    def _press_shift_mac() -> bool:
        """Press Shift via macOS System Events — harmless, no visible output."""
        try:
            r = subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to key code 56'],
                capture_output=True, timeout=5,
            )
            return r.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    @staticmethod
    def _press_shift_win() -> bool:
        """Press and release Shift via Windows user32.dll keybd_event."""
        try:
            VK_SHIFT = 0x10
            KEYEVENTF_KEYUP = 0x0002
            ctypes.windll.user32.keybd_event(VK_SHIFT, 0, 0, 0)
            time.sleep(0.02)
            ctypes.windll.user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            return False

    # ── Prevent Sleep ────────────────────────────────────────────

    def _prevent_sleep_start(self) -> None:
        if _IS_MAC:
            self._start_caffeinate()
        elif _IS_WIN:
            self._set_win_execution_state(prevent=True)

    def _prevent_sleep_stop(self) -> None:
        if _IS_MAC:
            self._stop_caffeinate()
        elif _IS_WIN:
            self._set_win_execution_state(prevent=False)

    # macOS: caffeinate ------------------------------------------------

    def _start_caffeinate(self) -> None:
        self._stop_caffeinate()
        try:
            self._caffeinate_proc = subprocess.Popen(
                ["caffeinate", "-di"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._emit_activity("☕ caffeinate active (preventing sleep)")
        except OSError:
            self._emit_activity("⚠ Could not start caffeinate")

    def _stop_caffeinate(self) -> None:
        if self._caffeinate_proc and self._caffeinate_proc.poll() is None:
            self._caffeinate_proc.terminate()
            try:
                self._caffeinate_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._caffeinate_proc.kill()
        self._caffeinate_proc = None

    # Windows: SetThreadExecutionState ----------------------------------

    @staticmethod
    def _set_win_execution_state(prevent: bool) -> None:
        """
        Prevent or allow system/display sleep on Windows.
        Uses kernel32.SetThreadExecutionState — built-in, no install needed.
        """
        ES_CONTINUOUS        = 0x80000000
        ES_SYSTEM_REQUIRED   = 0x00000001
        ES_DISPLAY_REQUIRED  = 0x00000002
        try:
            if prevent:
                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                )
            else:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        except Exception:
            pass

    # ── Callback Helpers ─────────────────────────────────────────

    def _emit_state_change(self) -> None:
        if self.on_state_change:
            try:
                self.on_state_change(self.state)
            except Exception:
                pass

    def _emit_activity(self, message: str) -> None:
        if self.on_activity:
            try:
                self.on_activity(message)
            except Exception:
                pass
