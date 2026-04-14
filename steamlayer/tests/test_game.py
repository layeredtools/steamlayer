from __future__ import annotations

import pathlib
from unittest.mock import MagicMock

import pytest

from steamlayer.emulators import Emulator, EmulatorConfig
from steamlayer.game import VAULT_NAME, Game, GamePatcher, GameRestorer


def make_dll(path: pathlib.Path, name: str = "steam_api64.dll") -> pathlib.Path:
    dll = path / name
    dll.write_bytes(b"original_dll_bytes")
    return dll


def make_fake_emulator(vendors: pathlib.Path) -> Emulator:
    """Returns a mock Emulator that copies a tiny stub DLL on patch."""
    stub_x64 = vendors / "goldberg" / "regular" / "x64" / "steam_api64.dll"
    stub_x32 = vendors / "goldberg" / "regular" / "x32" / "steam_api.dll"
    stub_x64.parent.mkdir(parents=True, exist_ok=True)
    stub_x32.parent.mkdir(parents=True, exist_ok=True)
    stub_x64.write_bytes(b"goldberg_x64")
    stub_x32.write_bytes(b"goldberg_x32")

    emu = MagicMock(spec=Emulator)
    emu.settings_dir_name = "steam_settings"
    emu.config_files = ["steam_appid.txt", "DLC.txt", "configs.user.ini", "configs.app.ini"]

    def _patch_game(*, dlls):
        import shutil

        for dll in dlls:
            dll.backup()
            src = stub_x64 if dll.architecture == "x64" else stub_x32
            shutil.copy2(src, dll.file)
        return dlls

    emu.patch_game.side_effect = _patch_game
    emu.create_config_files.return_value = None
    return emu


@pytest.fixture
def tmp_game(tmp_path):
    game_dir = tmp_path / "FakeGame"
    game_dir.mkdir()
    return game_dir


@pytest.fixture
def vendors(tmp_path):
    return tmp_path / "vendors"


class TestGameFindDlls:
    def test_finds_x64_dll(self, tmp_game):
        make_dll(tmp_game, "steam_api64.dll")

        game = Game(path=tmp_game)
        dlls = game.find_steam_dlls()

        assert len(dlls) == 1
        assert dlls[0].architecture == "x64"

    def test_finds_x32_dll(self, tmp_game):
        make_dll(tmp_game, "steam_api.dll")

        game = Game(path=tmp_game)
        dlls = game.find_steam_dlls()

        assert len(dlls) == 1
        assert dlls[0].architecture == "x32"

    def test_finds_both_dlls(self, tmp_game):
        make_dll(tmp_game, "steam_api.dll")
        make_dll(tmp_game, "steam_api64.dll")

        game = Game(path=tmp_game)
        dlls = game.find_steam_dlls()
        assert len(dlls) == 2

    def test_finds_dll_in_subdirectory(self, tmp_game):
        sub = tmp_game / "bin" / "win64"
        sub.mkdir(parents=True)
        make_dll(sub, "steam_api64.dll")

        game = Game(path=tmp_game)
        dlls = game.find_steam_dlls()
        assert len(dlls) == 1

    def test_skips_vault_directory(self, tmp_game):
        make_dll(tmp_game, "steam_api64.dll")

        vault = tmp_game / VAULT_NAME / "bin"
        vault.mkdir(parents=True)
        make_dll(vault, "steam_api64.dll")

        game = Game(path=tmp_game)
        dlls = game.find_steam_dlls()
        assert len(dlls) == 1  # only the real one, not the vaulted one

    def test_returns_empty_when_no_dlls(self, tmp_game):
        game = Game(path=tmp_game)
        assert game.find_steam_dlls() == []


class TestGamePatcher:
    def test_dry_run_does_not_modify_files(self, tmp_game, vendors):
        dll_path = make_dll(tmp_game, "steam_api64.dll")
        original_bytes = dll_path.read_bytes()

        game = Game(path=tmp_game, appid=620)
        emu = make_fake_emulator(vendors)
        config = MagicMock(spec=EmulatorConfig)
        patcher = GamePatcher(game=game, emulator=emu, config=config, dry_run=True)
        patcher.run()

        assert dll_path.read_bytes() == original_bytes
        assert not (tmp_game / VAULT_NAME).exists()
        emu.patch_game.assert_not_called()  # type: ignore

    def test_patching_replaces_dll_and_creates_vault(self, tmp_game, vendors):
        dll_path = make_dll(tmp_game, "steam_api64.dll")

        game = Game(path=tmp_game, appid=620)
        emu = make_fake_emulator(vendors)
        config = MagicMock(spec=EmulatorConfig)
        patcher = GamePatcher(game=game, emulator=emu, config=config, dry_run=False)
        patcher.run()

        assert dll_path.read_bytes() == b"goldberg_x64"
        vault_file = tmp_game / VAULT_NAME / "steam_api64.dll"
        assert vault_file.exists()
        assert vault_file.read_bytes() == b"original_dll_bytes"

    def test_raises_when_no_dlls_found(self, tmp_game, vendors):
        game = Game(path=tmp_game, appid=620)
        emu = make_fake_emulator(vendors)
        config = MagicMock(spec=EmulatorConfig)
        patcher = GamePatcher(game=game, emulator=emu, config=config)

        with pytest.raises(FileNotFoundError):
            patcher.run()

    def test_warns_on_existing_vault(self, tmp_game, vendors, caplog):
        import logging

        make_dll(tmp_game, "steam_api64.dll")

        vault = tmp_game / VAULT_NAME
        vault.mkdir()
        (vault / "something.dll").write_bytes(b"old")

        game = Game(path=tmp_game, appid=620)
        emu = make_fake_emulator(vendors)
        config = MagicMock(spec=EmulatorConfig)
        patcher = GamePatcher(game=game, emulator=emu, config=config)

        with caplog.at_level(logging.WARNING):
            patcher.run()

        assert "Previous backup detected" in caplog.text

    def test_existing_backup_is_not_overwritten(self, tmp_game, vendors):
        dll_path = make_dll(tmp_game, "steam_api64.dll")

        game = Game(path=tmp_game, appid=620)
        emu = make_fake_emulator(vendors)
        config = MagicMock(spec=EmulatorConfig)
        GamePatcher(game=game, emulator=emu, config=config).run()

        vault_file = tmp_game / VAULT_NAME / "steam_api64.dll"
        original_vault_bytes = vault_file.read_bytes()

        dll_path.write_bytes(b"tampered")

        emu2 = make_fake_emulator(vendors)
        GamePatcher(game=game, emulator=emu2, config=config).run()

        assert vault_file.read_bytes() == original_vault_bytes

    def test_config_failure_does_not_crash_patcher(self, tmp_game, vendors):
        make_dll(tmp_game, "steam_api64.dll")

        game = Game(path=tmp_game, appid=620)
        emu = make_fake_emulator(vendors)
        emu.create_config_files.side_effect = RuntimeError("config boom")  # type: ignore
        config = MagicMock(spec=EmulatorConfig)

        # Should not raise — config failure is logged but not fatal
        patcher = GamePatcher(game=game, emulator=emu, config=config)
        patcher.run()


class TestGameRestorer:
    def _patch_game(self, tmp_game, vendors):
        """Helper: patch a game and return the game object."""
        make_dll(tmp_game, "steam_api64.dll")
        game = Game(path=tmp_game, appid=620)
        emu = make_fake_emulator(vendors)
        config = MagicMock(spec=EmulatorConfig)
        GamePatcher(game=game, emulator=emu, config=config).run()
        return game, emu

    def test_restore_puts_original_dll_back(self, tmp_game, vendors):
        dll_path = tmp_game / "steam_api64.dll"
        game, emu = self._patch_game(tmp_game, vendors)
        assert dll_path.read_bytes() == b"goldberg_x64"

        GameRestorer(game=game, emulator=emu).run()

        assert dll_path.read_bytes() == b"original_dll_bytes"

    def test_restore_removes_vault(self, tmp_game, vendors):
        game, emu = self._patch_game(tmp_game, vendors)
        GameRestorer(game=game, emulator=emu).run()
        assert not (tmp_game / VAULT_NAME).exists()

    def test_restore_removes_steam_settings(self, tmp_game, vendors):
        game, emu = self._patch_game(tmp_game, vendors)

        settings = tmp_game / "steam_settings"
        settings.mkdir(exist_ok=True)
        (settings / "configs.app.ini").write_text("[app::dlcs]\n")

        GameRestorer(game=game, emulator=emu).run()

        assert not settings.exists()

    def test_restore_dry_run_does_not_modify_files(self, tmp_game, vendors):
        dll_path = tmp_game / "steam_api64.dll"
        game, emu = self._patch_game(tmp_game, vendors)
        patched_bytes = dll_path.read_bytes()

        GameRestorer(game=game, emulator=emu, dry_run=True).run()

        assert dll_path.read_bytes() == patched_bytes
        assert (tmp_game / VAULT_NAME).exists()

    def test_restore_fails_gracefully_with_no_vault(self, tmp_game, vendors, caplog):
        import logging

        game = Game(path=tmp_game, appid=620)
        emu = make_fake_emulator(vendors)

        with caplog.at_level(logging.ERROR):
            GameRestorer(game=game, emulator=emu).run()

        assert "No vault found" in caplog.text

    def test_restore_fails_gracefully_with_empty_vault(self, tmp_game, vendors, caplog):
        import logging

        game = Game(path=tmp_game, appid=620)
        emu = make_fake_emulator(vendors)
        (tmp_game / VAULT_NAME).mkdir()

        with caplog.at_level(logging.ERROR):
            GameRestorer(game=game, emulator=emu).run()

        assert "no files to restore" in caplog.text
