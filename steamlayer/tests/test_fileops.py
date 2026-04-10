from steamlayer.fileops import SteamAPIDll


def test_vault_mirroring_logic(tmp_path):
    game_root = tmp_path / "FakeGame"
    dll_dir = game_root / "bin" / "win64"
    dll_dir.mkdir(parents=True)

    dll_file = dll_dir / "steam_api64.dll"
    dll_file.write_text("dummy_dll_content")

    dll_obj = SteamAPIDll(dll_file)

    relative_path = dll_file.relative_to(game_root)
    vault_dest = game_root / "__original_files__" / relative_path
    dll_obj.set_backup_destination(vault_dest)

    dll_obj.backup()

    assert vault_dest.exists()
    assert vault_dest.read_text() == "dummy_dll_content"
    assert "__original_files__/bin/win64" in str(vault_dest.as_posix())
