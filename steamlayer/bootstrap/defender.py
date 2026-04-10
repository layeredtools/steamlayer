from __future__ import annotations

import json
import logging
import pathlib
import subprocess

log = logging.getLogger("steamlayer.bootstrap.defender")

STATE_PATH = pathlib.Path.home() / ".steamlayer" / "state.json"
MAX_WARNINGS = 3


def _read_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(state: dict) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        log.debug("Could not write state file.")


def is_realtime_protection_on() -> bool:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-Command",
                "Get-MpPreference | Select-Object -ExpandProperty DisableRealtimeMonitoring",
            ],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip().lower() == "false"

    except Exception:
        return True  # assume on if we can't tell


def check_defender_exclusion(path: str) -> bool:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-Command",
                "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath",
            ],
            capture_output=True,
            text=True,
        )
        if "administrator" in result.stdout.lower():
            log.debug("Cannot read Defender exclusions without elevation, assuming no exclusion is set.")
            return False

        needle = path.lower().rstrip("\\/")
        for line in result.stdout.splitlines():
            if line.lower().rstrip("\\/") == needle:
                return True
        return False

    except Exception:
        return False


def warn_about_defender_if_needed(vendors_path: str) -> None:
    if not is_realtime_protection_on():
        return

    if check_defender_exclusion(vendors_path):
        return

    state = _read_state()
    shown = state.get("defender_warning_count", 0)
    if shown >= MAX_WARNINGS:
        log.debug("Defender warning suppressed (shown %d times).", shown)
        return

    log.warning(
        "\n"
        "┌─ Windows Defender Warning ──────────────────────────────────────────┐\n"
        "│                                                                     │\n"
        "│  Real-time protection is ON. If you haven't already, add an        │\n"
        "│  exclusion for this folder to avoid a mid-install quarantine:       │\n"
        f"│  {vendors_path:<68}│\n"
        "│                                                                     │\n"
        "│  To fix: Windows Security → Virus & threat protection →             │\n"
        "│          Manage settings → Exclusions → Add an exclusion → Folder   │\n"
        "│                                                                     │\n"
        "└─────────────────────────────────────────────────────────────────────┘\n"
    )

    state["defender_warning_count"] = shown + 1
    _write_state(state)
