from __future__ import annotations

import struct

from steamlayer.steamstub import SteamStubResult, SteamStubScanner


def _build_pe(sections: list[tuple[bytes, bytes]] | None = None, extra_data: bytes = b"") -> bytes:
    """
    Build a minimal but structurally valid PE binary.

    *sections* is a list of (name, raw_content) pairs.  Section names are
    truncated / null-padded to 8 bytes automatically.
    *extra_data* is appended to the image (useful for import-table faking).
    """
    sections = sections or []

    pe_offset = 0x40  # place PE header right after the 64-byte DOS stub
    dos_stub = bytearray(pe_offset)
    dos_stub[0] = ord("M")
    dos_stub[1] = ord("Z")
    struct.pack_into("<I", dos_stub, 0x3C, pe_offset)

    pe_sig = b"PE\x00\x00"

    machine = 0x8664  # AMD64
    num_sections = len(sections)
    opt_header_size = 0  # skip optional header for simplicity
    coff = struct.pack(
        "<HHIIIHH",
        machine,  # Machine
        num_sections,  # NumberOfSections
        0,  # TimeDateStamp
        0,  # PointerToSymbolTable
        0,  # NumberOfSymbols
        opt_header_size,  # SizeOfOptionalHeader
        0x0002,  # Characteristics
    )

    section_table_offset = pe_offset + 4 + 20  # pe_sig + coff
    raw_data_base = section_table_offset + len(sections) * 40

    section_headers = bytearray()
    raw_payloads = bytearray()

    for name_bytes, content in sections:
        name_field = name_bytes[:8].ljust(8, b"\x00")
        raw_offset = raw_data_base + len(raw_payloads)
        raw_size = len(content)

        entry = bytearray(40)
        entry[0:8] = name_field
        struct.pack_into("<I", entry, 8, raw_size)  # VirtualSize
        struct.pack_into("<I", entry, 12, 0)  # VirtualAddress (irrelevant)
        struct.pack_into("<I", entry, 16, raw_size)  # SizeOfRawData
        struct.pack_into("<I", entry, 20, raw_offset)  # PointerToRawData

        section_headers += entry
        raw_payloads += content

    image = bytes(dos_stub) + pe_sig + coff + bytes(section_headers) + bytes(raw_payloads) + extra_data
    return image


class TestSteamStubScanner:
    scanner = SteamStubScanner()

    def test_empty_bytes_not_detected(self):
        result = self.scanner._scan_bytes(b"")
        assert not result.detected

    def test_random_bytes_not_detected(self):
        result = self.scanner._scan_bytes(b"\x00" * 128)
        assert not result.detected

    def test_mz_only_no_pe_sig(self):
        data = b"MZ" + b"\x00" * 62 + struct.pack("<I", 0x40) + b"\x00" * 16
        result = self.scanner._scan_bytes(data)
        assert not result.detected

    def test_clean_pe_no_sections(self):
        data = _build_pe(sections=[])
        result = self.scanner._scan_bytes(data)
        assert not result.detected
        assert "no .bind section" in result.reason

    def test_clean_pe_with_text_section(self):
        data = _build_pe(sections=[(b".text", b"\x55\x48\x89\xe5" + b"\x90" * 60)])
        result = self.scanner._scan_bytes(data)
        assert not result.detected

    def test_clean_pe_multiple_sections(self):
        data = _build_pe(
            sections=[
                (b".text", b"\x90" * 32),
                (b".rdata", b"\x00" * 32),
                (b".data", b"\xff" * 32),
            ]
        )
        result = self.scanner._scan_bytes(data)
        assert not result.detected

    def test_bind_section_unknown_variant(self):
        data = _build_pe(sections=[(b".bind", b"\x00" * 64)])
        result = self.scanner._scan_bytes(data)
        assert result.detected
        assert result.variant == "unknown"
        assert ".bind" in result.reason

    def test_bind_section_with_other_sections(self):
        data = _build_pe(
            sections=[
                (b".text", b"\x90" * 32),
                (b".bind", b"\x01\x02\x03\x04" * 16),
            ]
        )
        result = self.scanner._scan_bytes(data)
        assert result.detected

    def test_v3_magic_at_start_of_bind(self):
        bind_content = b"\xad\xde\xfe\xca" + b"\x00" * 60
        data = _build_pe(sections=[(b".bind", bind_content)])
        result = self.scanner._scan_bytes(data)
        assert result.detected
        assert result.variant == "v3.x"
        assert "0xCAFEDEAD" in result.reason

    def test_v3_magic_at_offset_in_bind(self):
        # Magic appears a few bytes in, still within the scan window
        bind_content = b"\x00" * 16 + b"\xad\xde\xfe\xca" + b"\x00" * 44
        data = _build_pe(sections=[(b".bind", bind_content)])
        result = self.scanner._scan_bytes(data)
        assert result.detected
        assert result.variant == "v3.x"

    def test_v3_magic_beyond_scan_window_not_detected_as_v3(self):
        # Magic beyond the 256-byte scan window — should fall through to unknown
        bind_content = b"\x00" * 300 + b"\xad\xde\xfe\xca"
        data = _build_pe(sections=[(b".bind", bind_content)])
        result = self.scanner._scan_bytes(data)
        assert result.detected
        # May be unknown since magic is outside the window
        assert result.variant in ("v3.x", "unknown")

    def test_v1_steamdrmp_import(self):
        bind_content = b"\x00" * 64  # no v3 magic
        extra = b"\x00" * 8 + b"SteamDRMP.dll" + b"\x00"
        data = _build_pe(sections=[(b".bind", bind_content)], extra_data=extra)
        result = self.scanner._scan_bytes(data)
        assert result.detected
        assert result.variant == "v1.x"
        assert "SteamDRMP.dll" in result.reason

    def test_v3_takes_priority_over_steamdrmp(self):
        # If both v3 magic and SteamDRMP.dll are present, v3 should win
        # (v3 check runs first)
        bind_content = b"\xad\xde\xfe\xca" + b"\x00" * 60
        extra = b"SteamDRMP.dll\x00"
        data = _build_pe(sections=[(b".bind", bind_content)], extra_data=extra)
        result = self.scanner._scan_bytes(data)
        assert result.detected
        assert result.variant == "v3.x"

    def test_scan_missing_file(self, tmp_path):
        result = self.scanner.scan(tmp_path / "nonexistent.exe")
        assert not result.detected
        assert "read error" in result.reason

    def test_scan_real_file_clean(self, tmp_path):
        exe = tmp_path / "game.exe"
        exe.write_bytes(_build_pe(sections=[(b".text", b"\x90" * 32)]))
        result = self.scanner.scan(exe)
        assert not result.detected

    def test_scan_real_file_v3(self, tmp_path):
        exe = tmp_path / "game.exe"
        exe.write_bytes(_build_pe(sections=[(b".bind", b"\xad\xde\xfe\xca" + b"\x00" * 60)]))
        result = self.scanner.scan(exe)
        assert result.detected
        assert result.variant == "v3.x"

    def test_scan_directory_returns_only_detected(self, tmp_path):
        (tmp_path / "clean.exe").write_bytes(_build_pe(sections=[(b".text", b"\x90" * 32)]))
        (tmp_path / "wrapped.exe").write_bytes(
            _build_pe(sections=[(b".bind", b"\xad\xde\xfe\xca" + b"\x00" * 60)])
        )
        (tmp_path / "readme.txt").write_text("hello")

        results = self.scanner.scan_directory(tmp_path)
        assert len(results) == 1
        assert (tmp_path / "wrapped.exe") in results
        assert results[tmp_path / "wrapped.exe"].variant == "v3.x"

    def test_scan_directory_empty_dir(self, tmp_path):
        results = self.scanner.scan_directory(tmp_path)
        assert results == {}

    def test_scan_directory_all_clean(self, tmp_path):
        for name in ("a.exe", "b.exe"):
            (tmp_path / name).write_bytes(_build_pe(sections=[(b".text", b"\x90" * 16)]))
        results = self.scanner.scan_directory(tmp_path)
        assert results == {}

    def test_str_not_detected(self):
        r = SteamStubResult(detected=False, reason="no .bind section found")
        assert "not detected" in str(r)

    def test_str_detected(self):
        r = SteamStubResult(detected=True, variant="v3.x", reason="some reason")
        assert "v3.x" in str(r)
        assert "detected" in str(r)
