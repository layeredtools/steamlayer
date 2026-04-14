from __future__ import annotations

import logging
import pathlib
import struct
from dataclasses import dataclass

log = logging.getLogger("steamlayer.steamstub.inspector")

_MZ_MAGIC = b"MZ"
_PE_MAGIC = b"PE\x00\x00"

# Offset of the PE header pointer inside the DOS stub
_PE_POINTER_OFFSET = 0x3C

# COFF header layout (relative to start of COFF header, i.e. PE sig + 4)
_COFF_NUM_SECTIONS_OFFSET = 2  # WORD
_COFF_OPT_HEADER_SIZE_OFFSET = 16  # WORD

# Each section entry is exactly 40 bytes
_SECTION_ENTRY_SIZE = 40

# ── Variant signatures ────────────────────────────────────────────────────────
# Magic word written at the start of the SteamStub v3.x header inside .bind.
# Little-endian 0xCAFEDEAD.
_STUB_MAGIC_V3 = b"\xad\xde\xfe\xca"

# Import DLL name that only appears in SteamStub v1.x titles.
_STEAMDRMP_IMPORT = b"SteamDRMP.dll"

# How many bytes to read from the start of .bind when checking signatures.
_BIND_SCAN_WINDOW = 256


@dataclass(frozen=True)
class SteamStubResult:
    """Result of a single-file SteamStub scan."""

    detected: bool
    """``True`` when at least one SteamStub indicator was found."""

    variant: str | None = None
    """
    Human-readable variant string when *detected* is ``True``:
    ``"v1.x"``, ``"v3.x"``, or ``"unknown"``.
    ``None`` when no DRM was detected.
    """

    reason: str = ""

    def __str__(self) -> str:
        if not self.detected:
            return f"SteamStub: not detected ({self.reason})"
        return f"SteamStub {self.variant} detected — {self.reason}"


class SteamStubScanner:
    def scan(self, path: pathlib.Path) -> SteamStubResult:
        try:
            data = path.read_bytes()
        except OSError as exc:
            log.debug("Could not read '%s': %s", path, exc)
            return SteamStubResult(detected=False, reason=f"read error: {exc}")

        result = self._scan_bytes(data)
        if result.detected:
            log.warning("'%s': %s", path.name, result)
        else:
            log.debug("'%s': %s", path.name, result)
        return result

    def scan_directory(self, directory: pathlib.Path) -> dict[pathlib.Path, SteamStubResult]:
        results: dict[pathlib.Path, SteamStubResult] = {}
        for exe in directory.glob("**/*.exe"):
            result = self.scan(exe)
            if result.detected:
                results[exe] = result
        return results

    def _scan_bytes(self, data: bytes) -> SteamStubResult:
        # Validate MZ header
        if len(data) < 64 or data[:2] != _MZ_MAGIC:
            return SteamStubResult(detected=False, reason="not a valid PE (missing MZ magic)")

        # Locate PE signature
        pe_offset = struct.unpack_from("<I", data, _PE_POINTER_OFFSET)[0]
        if pe_offset + 4 > len(data):
            return SteamStubResult(detected=False, reason="PE pointer out of bounds")
        if data[pe_offset : pe_offset + 4] != _PE_MAGIC:
            return SteamStubResult(detected=False, reason="invalid PE signature")

        # Parse COFF header
        coff_offset = pe_offset + 4
        if coff_offset + 20 > len(data):
            return SteamStubResult(detected=False, reason="truncated COFF header")

        num_sections: int = struct.unpack_from("<H", data, coff_offset + _COFF_NUM_SECTIONS_OFFSET)[0]
        opt_header_size: int = struct.unpack_from("<H", data, coff_offset + _COFF_OPT_HEADER_SIZE_OFFSET)[0]

        # Walk the section table
        sections_start = coff_offset + 20 + opt_header_size
        bind_raw_offset: int | None = None
        bind_raw_size: int | None = None

        for i in range(num_sections):
            sec_start = sections_start + i * _SECTION_ENTRY_SIZE
            if sec_start + _SECTION_ENTRY_SIZE > len(data):
                break

            # Section name: 8 bytes, null-padded
            name = data[sec_start : sec_start + 8].rstrip(b"\x00")

            if name == b".bind":
                # VirtualSize at +8, SizeOfRawData at +16, PointerToRawData at +20
                bind_raw_size = struct.unpack_from("<I", data, sec_start + 16)[0]
                bind_raw_offset = struct.unpack_from("<I", data, sec_start + 20)[0]
                break

        if bind_raw_offset is None:
            return SteamStubResult(detected=False, reason="no .bind section found")

        # Inspect .bind contents for variant signatures
        scan_size = min(bind_raw_size, _BIND_SCAN_WINDOW) if bind_raw_size and bind_raw_size > 0 else 0
        bind_window = data[bind_raw_offset : bind_raw_offset + scan_size]

        if _STUB_MAGIC_V3 in bind_window:
            return SteamStubResult(
                detected=True,
                variant="v3.x",
                reason=".bind section present with 0xCAFEDEAD stub header magic",
            )

        # v1.x: SteamDRMP.dll lives in the import table, not in .bind — scan whole binary
        if _STEAMDRMP_IMPORT in data:
            return SteamStubResult(
                detected=True,
                variant="v1.x",
                reason=".bind section present with SteamDRMP.dll import",
            )

        return SteamStubResult(
            detected=True,
            variant="unknown",
            reason=".bind section present (variant could not be determined)",
        )
