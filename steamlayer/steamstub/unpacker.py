from __future__ import annotations

import logging
import pathlib
import shutil
import subprocess

from steamlayer import VENDORS_PATH

log = logging.getLogger("steamlayer.steamstub.unpacker")


class SteamlessCLI:
    def __init__(self, cli_path: pathlib.Path | None = None) -> None:
        self.cli_path = cli_path or self._find_cli()

    def _find_cli(self) -> pathlib.Path | None:
        vendor_path = VENDORS_PATH / "steamless" / "Steamless.CLI.exe"
        if vendor_path.exists():
            return vendor_path

        found = shutil.which("Steamless.CLI.exe")
        if found:
            return pathlib.Path(found)
        return None

    def is_available(self) -> bool:
        return self.cli_path is not None

    def unpack(self, target_exe: pathlib.Path) -> pathlib.Path:
        if not self.cli_path:
            raise RuntimeError("Steamless.CLI.exe not found.")

        log.debug(f"Running Steamless on {target_exe.name}...")
        cmd = [str(self.cli_path), "--quiet", "--keepattributes", str(target_exe)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0 or ("error" in (result.stdout or "").lower()):
            raise RuntimeError(f"Steamless failed to unpack {target_exe.name}:\n{result.stderr or result.stdout}")

        unpacked = target_exe.with_name(f"{target_exe.name}.unpacked.exe")
        if not unpacked.exists():
            raise FileNotFoundError(f"Steamless succeeded but output file is missing: {unpacked}")

        return unpacked
