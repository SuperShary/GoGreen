"""
GoGreen v2 — Cross-Platform Activity Simulation Engine
Keeps MS Teams status green by simulating user activity.

ZERO external dependencies:
  macOS  → osascript + caffeinate (built-in)
  Windows → ctypes (standard library) → user32.dll / kernel32.dll
"""

import subprocess
import sys
import threading
import time
from datetime import datetime
from typing import Callable, List, Optional, Tuple

_IS_MAC = sys.platform == "darwin"
_IS_WIN = sys.platform == "win32"

if _IS_WIN:
    import ctypes

    class _POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class ActivityEngine:
    """
    Background engine that simulates user activity to keep Teams green.
    Uses ONLY OS-native tools — zero pip installs.
    """

    STATE_STOPPED = "stopped"
    STATE_ACTIVE  = "active"
    STATE_PAUSED  = "paused"

    def __init__(self):
        self.state: str = self.STATE_STOPPED
        self._thread: Optional[threading.Thread] = None
        self._stop_event  = threading.Event()
        self._pause_event = threading.Event()
        self._caffeinate_proc: Optional[subprocess.Popen] = None

        # Configuration
        self.interval_seconds: int   = 60
        self.enable_mouse: bool      = True
        self.enable_keyboard: bool   = True
        self.enable_caffeinate: bool = True
        self.duration_seconds: Optional[float] = None

        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_activity:     Optional[Callable] = None
        self.on_duration_end: Optional[Callable] = None
        self.on_permission_issue: Optional[Callable] = None

        self._start_time: float = 0.0
        self._permissions_ok: Optional[bool] = None

    # ── Permission Check ─────────────────────────────────────────

    def check_permissions(self) -> Tuple[bool, str]:
        """
        Test if we can actually simulate input.
        Returns (ok, message).
        """
        if _IS_WIN:
            return True, "✅ Windows — no special permissions needed"

        if _IS_MAC:
            # Test keyboard simulation via System Events
            try:
                r = subprocess.run(
                    ["osascript", "-e",
                     'tell application "System Events" to key code 56'],
                    capture_output=True, timeout=5, text=True,
                )
                stderr = r.stderr.lower()
                if r.returncode != 0:
                    if ("assistive" in stderr or "access" in stderr
                            or "not authorized" in stderr
                            or "1002" in stderr):
                        self._permissions_ok = False
                        return False, (
                            "❌ Accessibility permission NOT granted.\n"
                            "Go to: System Settings → Privacy & Security "
                            "→ Accessibility → enable your Terminal / IDE."
                        )
                    self._permissions_ok = False
                    return False, f"❌ Key simulation failed: {r.stderr.strip()}"

                self._permissions_ok = True
                return True, "✅ Accessibility permission granted"
            except Exception as e:
                self._permissions_ok = False
                return False, f"❌ Permission check error: {e}"

        return False, "❌ Unsupported platform"

    # ── Public API ───────────────────────────────────────────────

    def start(self) -> None:
        if self.state == self.STATE_ACTIVE:
            return

        self._stop_event.clear()
        self._pause_event.clear()
        self._start_time = time.time()

        # Run permission check
        ok, msg = self.check_permissions()
        self._emit_activity(msg)
        if not ok and self.on_permission_issue:
            self.on_permission_issue(msg)

        if self.enable_caffeinate:
            self._prevent_sleep_start()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        self.state = self.STATE_ACTIVE
        self._emit_state_change()
        self._emit_activity("🟢 Engine started — simulation active")

    def pause(self) -> None:
        if self.state != self.STATE_ACTIVE:
            return
        self._pause_event.set()
        self.state = self.STATE_PAUSED
        self._emit_state_change()
        self._emit_activity("⏸ Engine paused")

    def resume(self) -> None:
        if self.state != self.STATE_PAUSED:
            return
        self._pause_event.clear()
        self.state = self.STATE_ACTIVE
        self._emit_state_change()
        self._emit_activity("▶ Engine resumed")

    def stop(self) -> None:
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
        return max(0.0, self.duration_seconds - self.get_elapsed_seconds())

    # ── Simulation Loop ──────────────────────────────────────────

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            while self._pause_event.is_set() and not self._stop_event.is_set():
                time.sleep(0.5)
            if self._stop_event.is_set():
                break

            if self.duration_seconds is not None:
                if self.get_elapsed_seconds() >= self.duration_seconds:
                    self._emit_activity("⏰ Duration reached — auto-stopping")
                    if self.on_duration_end:
                        self.on_duration_end()
                    break

            self._simulate_activity()
            self._stop_event.wait(timeout=self.interval_seconds)

    def _simulate_activity(self) -> None:
        actions: List[str] = []
        failures: List[str] = []

        # 1. Mouse wiggle
        if self.enable_mouse:
            ok = self._wiggle_mouse()
            if ok:
                actions.append("mouse wiggle")
            else:
                failures.append("mouse")

        # 2. Keyboard press
        if self.enable_keyboard:
            ok = self._press_key()
            if ok:
                actions.append("Shift key")
            else:
                failures.append("keyboard")

        # 3. Assert user activity at OS level (macOS: caffeinate -u)
        #    This is a FALLBACK that works even without Accessibility perms
        if _IS_MAC:
            self._assert_user_activity_mac()

        ts = datetime.now().strftime("%H:%M:%S")
        if actions:
            msg = f"✅ {ts} — {' + '.join(actions)}"
            if failures:
                msg += f"  (⚠ {', '.join(failures)} failed)"
            self._emit_activity(msg)
        elif failures:
            self._emit_activity(
                f"⚠ {ts} — ALL SIMULATIONS FAILED: {', '.join(failures)}. "
                f"Grant Accessibility permissions!"
            )

    # ══════════════════════════════════════════════════════════════
    #  MOUSE WIGGLE
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _wiggle_mouse() -> bool:
        if _IS_MAC:
            return ActivityEngine._wiggle_mouse_mac()
        elif _IS_WIN:
            return ActivityEngine._wiggle_mouse_win()
        return False

    @staticmethod
    def _wiggle_mouse_mac() -> bool:
        """Move mouse 5px right then back via CoreGraphics (JXA)."""
        script = """
        ObjC.import('CoreGraphics');
        var e = $.CGEventCreate($());
        var loc = $.CGEventGetLocation(e);
        var x = loc.x, y = loc.y;

        // Move 5px right
        var m1 = $.CGEventCreateMouseEvent(
            $(), $.kCGEventMouseMoved, $.CGPointMake(x + 5, y), 0);
        $.CGEventPost($.kCGHIDEventTap, m1);
        delay(0.08);

        // Move back
        var m2 = $.CGEventCreateMouseEvent(
            $(), $.kCGEventMouseMoved, $.CGPointMake(x, y), 0);
        $.CGEventPost($.kCGHIDEventTap, m2);
        """
        try:
            r = subprocess.run(
                ["osascript", "-l", "JavaScript", "-e", script],
                capture_output=True, timeout=10, text=True,
            )
            # osascript might return 0 even without perms, check stderr
            if r.stderr and "not permitted" in r.stderr.lower():
                return False
            return r.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    @staticmethod
    def _wiggle_mouse_win() -> bool:
        """Move mouse 5px right then back via user32.dll."""
        try:
            pt = _POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            ctypes.windll.user32.SetCursorPos(pt.x + 5, pt.y)
            time.sleep(0.05)
            ctypes.windll.user32.SetCursorPos(pt.x, pt.y)
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════
    #  KEYBOARD SIMULATION  (with fallbacks)
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _press_key() -> bool:
        if _IS_MAC:
            return ActivityEngine._press_key_mac()
        elif _IS_WIN:
            return ActivityEngine._press_key_win()
        return False

    @staticmethod
    def _press_key_mac() -> bool:
        """Try multiple key simulation methods on macOS."""
        methods = [
            # Method 1: Shift key via System Events
            ('tell application "System Events" to key code 56', "AppleScript"),
            # Method 2: F15 key (harmless, no visible effect)
            ('tell application "System Events" to key code 113', "AppleScript"),
            # Method 3: Press and release Shift via keystroke
            ('tell application "System Events" to keystroke ""', "AppleScript"),
        ]
        for script, _ in methods:
            try:
                r = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True, timeout=5, text=True,
                )
                if r.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, OSError):
                continue
        return False

    @staticmethod
    def _press_key_win() -> bool:
        """Press Shift via user32.dll keybd_event."""
        try:
            VK_SHIFT = 0x10
            KEYEVENTF_KEYUP = 0x0002
            ctypes.windll.user32.keybd_event(VK_SHIFT, 0, 0, 0)
            time.sleep(0.02)
            ctypes.windll.user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════
    #  USER ACTIVITY ASSERTION (fallback — no permissions needed)
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _assert_user_activity_mac() -> bool:
        """
        caffeinate -u -t 2 : assert user is active for 2 seconds.
        Built into macOS, requires NO special permissions.
        Resets the system idle timer which some apps check.
        """
        try:
            r = subprocess.run(
                ["caffeinate", "-u", "-t", "2"],
                capture_output=True, timeout=5,
            )
            return r.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    # ══════════════════════════════════════════════════════════════
    #  SLEEP PREVENTION
    # ══════════════════════════════════════════════════════════════

    def _prevent_sleep_start(self) -> None:
        if _IS_MAC:
            self._start_caffeinate()
        elif _IS_WIN:
            self._set_win_execution_state(True)

    def _prevent_sleep_stop(self) -> None:
        if _IS_MAC:
            self._stop_caffeinate()
        elif _IS_WIN:
            self._set_win_execution_state(False)

    def _start_caffeinate(self) -> None:
        self._stop_caffeinate()
        try:
            # -d = prevent display sleep, -i = prevent idle sleep
            # -u = assert user activity
            self._caffeinate_proc = subprocess.Popen(
                ["caffeinate", "-diu"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._emit_activity("☕ caffeinate active (preventing sleep + asserting user activity)")
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

    @staticmethod
    def _set_win_execution_state(prevent: bool) -> None:
        ES_CONTINUOUS       = 0x80000000
        ES_SYSTEM_REQUIRED  = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        try:
            if prevent:
                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
            else:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        except Exception:
            pass

    # ── Helpers ──────────────────────────────────────────────────

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
