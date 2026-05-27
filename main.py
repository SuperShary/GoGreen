#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║                         GoGreen  🟢                              ║
║       Keep your MS Teams status Available — always.              ║
║                                                                   ║
║  Zero install. Zero admin. Just run:  python3 main.py            ║
║  Works on macOS and Windows.                                     ║
╚═══════════════════════════════════════════════════════════════════╝
"""

import sys
import os

def main():
    # Ensure we can import sibling modules regardless of cwd
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # ── Pre-flight checks ────────────────────────────────────────
    _check_python_version()
    _check_tkinter()

    # Show accessibility guidance on macOS (first run)
    if sys.platform == "darwin":
        _show_mac_accessibility_hint()

    # ── Launch the app ───────────────────────────────────────────
    from app import GoGreenApp
    app = GoGreenApp()
    app.run()


def _check_python_version():
    if sys.version_info < (3, 7):
        print("❌ GoGreen requires Python 3.7 or later.")
        print(f"   You are running Python {sys.version}")
        sys.exit(1)


def _check_tkinter():
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("❌ tkinter is not available in your Python installation.")
        print()
        if sys.platform == "darwin":
            print("   Fix for macOS:")
            print("   • If using Homebrew Python:  brew install python-tk")
            print("   • Or download Python from https://python.org (includes tkinter)")
        elif sys.platform == "win32":
            print("   Fix for Windows:")
            print("   • Re-run the Python installer and check 'tcl/tk and IDLE'")
        else:
            print("   Install tkinter for your platform (e.g. apt install python3-tk)")
        sys.exit(1)


def _show_mac_accessibility_hint():
    """
    On macOS, mouse/keyboard simulation requires Accessibility permissions.
    Show a one-time hint in the terminal on first launch.
    """
    from pathlib import Path
    marker = Path.home() / ".gogreen" / ".accessibility_hint_shown"
    if marker.exists():
        return

    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  🔐  macOS Accessibility Permission Required               │")
    print("│                                                             │")
    print("│  GoGreen simulates mouse/keyboard to keep Teams green.     │")
    print("│  macOS requires you to grant permission for this.          │")
    print("│                                                             │")
    print("│  → System Settings → Privacy & Security → Accessibility   │")
    print("│  → Add and enable your Terminal app (or IDE).              │")
    print("│                                                             │")
    print("│  This message appears only once.                           │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()

    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
    except OSError:
        pass


if __name__ == "__main__":
    main()
