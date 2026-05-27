"""
GoGreen — Settings Persistence
Saves and loads user preferences to ~/.gogreen/settings.json
Zero external dependencies — uses only Python standard library.
"""

import json
import os
from pathlib import Path

# Default configuration values
DEFAULTS = {
    "duration_mode": "infinite",     # "preset" | "custom" | "infinite"
    "duration_hours": 8,             # hours (used when mode is preset or custom)
    "interval_seconds": 60,          # seconds between activity pulses (30–300)
    "schedule_enabled": False,
    "schedule_start": "09:00",
    "schedule_stop": "18:00",
    "schedule_days": [0, 1, 2, 3, 4],  # 0=Mon … 6=Sun
    "minimize_on_close": False,
    "simulation_mouse": True,        # enable mouse wiggle
    "simulation_keyboard": True,     # enable shift key press
    "simulation_caffeinate": True,   # enable caffeinate
}

SETTINGS_DIR = Path.home() / ".gogreen"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


def load() -> dict:
    """Load settings from disk, returning defaults for any missing keys."""
    settings = dict(DEFAULTS)
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
            # Merge saved values into defaults (so new keys get defaults)
            for key in DEFAULTS:
                if key in saved:
                    settings[key] = saved[key]
    except (json.JSONDecodeError, OSError):
        # Corrupted or unreadable file — fall back to defaults
        pass
    return settings


def save(settings: dict) -> None:
    """Persist current settings to disk."""
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except OSError:
        # Can't write (e.g. read-only filesystem) — silently skip
        pass


def reset() -> dict:
    """Reset settings to defaults and save."""
    settings = dict(DEFAULTS)
    save(settings)
    return settings
