from __future__ import annotations

import logging
import subprocess

from steamlayer import state

log = logging.getLogger("steamlayer.bootstrap.defender")

MAX_WARNINGS = 3


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
    section = "defender"
    shown = state.get(section, "warning_count", 0)

    if shown >= MAX_WARNINGS:
        log.debug("Defender warning suppressed (shown %d times).", shown)
        return

    if not is_realtime_protection_on():
        return

    if check_defender_exclusion(vendors_path):
        return

    log.warning(
        "\n"
        "┌─ Windows Defender Warning ──────────────────────────────────────────┐\n"
        "│                                                                     │\n"
        "│  Real-time protection is ON. If you haven't already, add an         │\n"
        "│  exclusion for this folder to avoid a mid-install quarantine:       │\n"
        f"│  {vendors_path:<68}│\n"
        "│                                                                     │\n"
        "│  To fix: Windows Security → Virus & threat protection →             │\n"
        "│          Manage settings → Exclusions → Add an exclusion → Folder   │\n"
        "│                                                                     │\n"
        "└─────────────────────────────────────────────────────────────────────┘\n"
    )

    state.update_section(section, warning_count=shown + 1)
