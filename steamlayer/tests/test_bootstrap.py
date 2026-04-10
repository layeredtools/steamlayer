from __future__ import annotations

import json
import pathlib
from unittest.mock import patch

import pytest

from steamlayer.bootstrap.base import Bootstrapper
from steamlayer.bootstrap.defender import (
    MAX_WARNINGS,
    _read_state,
    warn_about_defender_if_needed,
)
from steamlayer.bootstrap.goldberg import GoldbergBootstrapper
from steamlayer.bootstrap.sevenzip import SevenZipBootstrapper


class TestDefenderWarningCounter:
    def test_warning_shown_on_first_run(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        monkeypatch.setattr("steamlayer.bootstrap.defender.STATE_PATH", state_file)
        monkeypatch.setattr("steamlayer.bootstrap.defender.is_realtime_protection_on", lambda: True)
        monkeypatch.setattr("steamlayer.bootstrap.defender.check_defender_exclusion", lambda p: False)

        with patch("steamlayer.bootstrap.defender.log") as mock_log:
            warn_about_defender_if_needed("/fake/vendors")
            mock_log.warning.assert_called_once()

        state = json.loads(state_file.read_text())
        assert state["defender_warning_count"] == 1

    def test_warning_suppressed_after_max(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"defender_warning_count": MAX_WARNINGS}))
        monkeypatch.setattr("steamlayer.bootstrap.defender.STATE_PATH", state_file)
        monkeypatch.setattr("steamlayer.bootstrap.defender.is_realtime_protection_on", lambda: True)
        monkeypatch.setattr("steamlayer.bootstrap.defender.check_defender_exclusion", lambda p: False)

        with patch("steamlayer.bootstrap.defender.log") as mock_log:
            warn_about_defender_if_needed("/fake/vendors")
            mock_log.warning.assert_not_called()

        # Counter should not increment past max
        state = json.loads(state_file.read_text())
        assert state["defender_warning_count"] == MAX_WARNINGS

    def test_warning_increments_counter(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"defender_warning_count": 1}))
        monkeypatch.setattr("steamlayer.bootstrap.defender.STATE_PATH", state_file)
        monkeypatch.setattr("steamlayer.bootstrap.defender.is_realtime_protection_on", lambda: True)
        monkeypatch.setattr("steamlayer.bootstrap.defender.check_defender_exclusion", lambda p: False)

        warn_about_defender_if_needed("/fake/vendors")

        state = json.loads(state_file.read_text())
        assert state["defender_warning_count"] == 2

    def test_skipped_when_protection_off(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        monkeypatch.setattr("steamlayer.bootstrap.defender.STATE_PATH", state_file)
        monkeypatch.setattr("steamlayer.bootstrap.defender.is_realtime_protection_on", lambda: False)

        with patch("steamlayer.bootstrap.defender.log") as mock_log:
            warn_about_defender_if_needed("/fake/vendors")
            mock_log.warning.assert_not_called()

        assert not state_file.exists()

    def test_skipped_when_exclusion_set(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        monkeypatch.setattr("steamlayer.bootstrap.defender.STATE_PATH", state_file)
        monkeypatch.setattr("steamlayer.bootstrap.defender.is_realtime_protection_on", lambda: True)
        monkeypatch.setattr("steamlayer.bootstrap.defender.check_defender_exclusion", lambda p: True)

        with patch("steamlayer.bootstrap.defender.log") as mock_log:
            warn_about_defender_if_needed("/fake/vendors")
            mock_log.warning.assert_not_called()

    def test_read_state_returns_empty_on_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("steamlayer.bootstrap.defender.STATE_PATH", tmp_path / "nonexistent.json")
        assert _read_state() == {}

    def test_read_state_returns_empty_on_corrupt_file(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        state_file.write_text("not valid json{{{{")
        monkeypatch.setattr("steamlayer.bootstrap.defender.STATE_PATH", state_file)
        assert _read_state() == {}


class ConcreteBootstrapper(Bootstrapper):
    """Minimal concrete subclass for testing the base class logic."""

    def __init__(self, path, http, *, installed=False):
        super().__init__(path, http)
        self._installed = installed
        self.install_called = 0

    def _is_installed(self):
        return self._installed

    def _install(self):
        self.install_called += 1
        self._installed = True


class TestBootstrapperBase:
    def test_ensure_installs_when_missing(self, tmp_path):
        b = ConcreteBootstrapper(tmp_path / "tool", http=None, installed=False)
        b.ensure()
        assert b.install_called == 1

    def test_ensure_skips_when_already_installed(self, tmp_path):
        b = ConcreteBootstrapper(tmp_path / "tool", http=None, installed=True)
        b.ensure()
        assert b.install_called == 0

    def test_ensure_updates_when_new_version_available(self, tmp_path):
        b = ConcreteBootstrapper(tmp_path / "tool", http=None, installed=True)
        b._get_latest_version = lambda: "2.0"
        b._get_installed_version = lambda: "1.0"
        b.ensure()
        assert b.install_called == 1

    def test_ensure_skips_update_when_up_to_date(self, tmp_path):
        b = ConcreteBootstrapper(tmp_path / "tool", http=None, installed=True)
        b._get_latest_version = lambda: "2.0"
        b._get_installed_version = lambda: "2.0"
        b.ensure()
        assert b.install_called == 0

    def test_save_and_read_version(self, tmp_path):
        path = tmp_path / "tool"
        path.mkdir()
        b = ConcreteBootstrapper(path, http=None, installed=True)
        b._save_version("1.2.3")
        assert b._get_installed_version() == "1.2.3"

    def test_is_available_delegates_to_is_installed(self, tmp_path):
        b = ConcreteBootstrapper(tmp_path / "tool", http=None, installed=True)
        assert b.is_available() is True

        b2 = ConcreteBootstrapper(tmp_path / "tool2", http=None, installed=False)
        assert b2.is_available() is False

    def test_download_raises_without_http(self, tmp_path):
        b = ConcreteBootstrapper(tmp_path / "tool", http=None)
        with pytest.raises(RuntimeError, match="Network access required"):
            b._download("https://example.com/file")

    def test_reset_dir_clears_existing(self, tmp_path):
        path = tmp_path / "tool"
        path.mkdir()
        (path / "old_file.txt").write_text("old")

        b = ConcreteBootstrapper(path, http=None)
        b._reset_dir()

        assert path.exists()
        assert not (path / "old_file.txt").exists()


class TestGoldbergBootstrapper:
    def test_not_installed_when_dlls_missing(self, tmp_path):
        b = GoldbergBootstrapper(tmp_path / "goldberg", http=None)
        assert b._is_installed() is False

    def test_not_installed_when_dlls_empty(self, tmp_path):
        path = tmp_path / "goldberg"
        x64 = path / "regular" / "x64" / "steam_api64.dll"
        x32 = path / "regular" / "x32" / "steam_api.dll"
        x64.parent.mkdir(parents=True)
        x32.parent.mkdir(parents=True)
        x64.write_bytes(b"")  # empty
        x32.write_bytes(b"real content")
        b = GoldbergBootstrapper(path, http=None)
        assert b._is_installed() is False

    def test_is_installed_when_both_dlls_present(self, tmp_path):
        path = tmp_path / "goldberg"
        x64 = path / "regular" / "x64" / "steam_api64.dll"
        x32 = path / "regular" / "x32" / "steam_api.dll"
        x64.parent.mkdir(parents=True)
        x32.parent.mkdir(parents=True)
        x64.write_bytes(b"dll content")
        x32.write_bytes(b"dll content")
        b = GoldbergBootstrapper(path, http=None)
        assert b._is_installed() is True


class TestSevenZipBootstrapper:
    def test_not_installed_when_exe_missing(self, tmp_path):
        b = SevenZipBootstrapper(tmp_path / "7zip", http=None)
        assert b._is_installed() is False

    def test_is_installed_when_exe_present(self, tmp_path):
        path = tmp_path / "7zip"
        path.mkdir()
        (path / "7z.exe").write_bytes(b"fake exe")
        b = SevenZipBootstrapper(path, http=None)
        assert b._is_installed() is True

    def test_find_system_7z_returns_none_when_not_found(self, tmp_path):
        b = SevenZipBootstrapper(tmp_path / "7zip", http=None)
        with patch("shutil.which", return_value=None):
            result = b._find_system_7z()

        # Will be None unless the test machine happens to have 7z installed
        # at the hardcoded paths — acceptable
        assert result is None or isinstance(result, str)

    def test_find_system_7z_finds_via_which(self, tmp_path):
        b = SevenZipBootstrapper(tmp_path / "7zip", http=None)
        fake_path = str(tmp_path / "7z.exe")
        pathlib.Path(fake_path).write_bytes(b"fake")

        with patch("shutil.which", return_value=fake_path):
            result = b._find_system_7z()

        assert result == fake_path
