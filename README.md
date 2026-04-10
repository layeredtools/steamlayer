<div align="center">

# steamlayer

Patches Steam games to run through the [Goldberg emulator](https://github.com/Detanup01/gbe_fork).  
Finds the AppID, grabs DLC info, swaps the DLLs, backs up the originals. One command.

![Python](https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

</div>

---

## What it does

You point it at a game folder. It figures out the AppID (or you tell it), pulls DLC metadata from Steam, backs up the original `steam_api.dll` files, drops in Goldberg's replacements, and writes the config. If something breaks or you just want your files back, `--restore` undoes everything cleanly.

7-Zip and Goldberg are downloaded automatically on first run — you don't install them manually.

---

> [!WARNING]
> steamlayer is under active development and not yet production-ready. Expect rough edges, and always keep `--restore` in mind.

---

## Installation

```bash
pip install steamlayer
```

Or with pipx if you want it isolated:

```bash
pipx install steamlayer
```

**Requirements:** 
* Python 3.13+
* Windows
* 7-Zip somewhere on your system for the very first run (after that steamlayer manages its own copy).

---

## Usage

```bash
steamlayer "C:\Games\Portal 2"
```

That's the common case. It'll do everything automatically. If the AppID detection gets it wrong, pass it explicitly:

```bash
steamlayer "C:\Games\Portal 2" --appid 620
```

Not sure what it's going to do? Run with `--dry-run` first:

```bash
steamlayer "C:\Games\Portal 2" --dry-run
```

Something broke, want your files back:

```bash
steamlayer "C:\Games\Portal 2" --restore
```

### All options

| Flag | Description |
|---|---|
| `-a`, `--appid <id>` | Skip auto-detection and use this AppID |
| `-d`, `--dry-run` | Show what would happen, don't touch anything |
| `-n`, `--no-network` | Use cached data only, no requests |
| `-r`, `--restore` | Put the original DLLs back and clean up |
| `-y`, `--yolo` | Accept lower-confidence AppID matches |
| `-v` / `-vv` | More output (`-v` = info, `-vv` = debug) |
| `--cache-dir <path>` | Override the cache location |
| `--no-defender-check` | Skip the Defender warning |
| `--version` | Print the version and exit |

---

## How it works

**AppID detection** — checks for `steam_appid.txt` or `.acf` manifest files in the game folder first. If nothing's there, it searches a locally-cached community index, then falls back to the Steam store API. If two results look equally likely, it asks you to pick.

**DLC metadata** — fetches the DLC list from the Steam API and resolves names using the same community index. Anything missing from the index gets looked up individually. Results are cached for a week so repeat runs are fast.

**Patching** — finds every `steam_api.dll` and `steam_api64.dll` in the game tree, vaults the originals to `<game>/__original_files__/`, and copies in the right Goldberg DLL (x32 or x64). Config files go in a `steam_settings/` folder next to each DLL, plus a `steam_appid.txt` at the game root.

**Restore** — moves the vaulted DLLs back, deletes the `steam_settings/` directories, cleans up loose config files, and removes the vault once it's empty. Safe to re-run if it fails partway through.

---

## Windows Defender

If real-time protection is on, add a folder exclusion before running:

**Windows Security → Virus & threat protection → Manage settings → Exclusions → Add an exclusion → Folder**

```
C:\Users\<you>\.steamlayer\vendors
```

Swapping Steam DLLs looks suspicious enough that Defender will sometimes quarantine Goldberg's files mid-download. The exclusion keeps that from happening. It only covers this one folder, nothing else on your system.

---

## Troubleshooting

**7-Zip bootstrap fails** — steamlayer needs an existing `7z.exe` to pull in its own copy. Make sure it's in `PATH` or installed at the default location (`C:\Program Files\7-Zip\`).

**Wrong game detected** — use `--appid`. You can find the right ID on [SteamDB](https://www.steamdb.info) or in the store URL.

**Defender quarantined something mid-install** — add the exclusion above and re-run. steamlayer will re-download and retry cleanly.

**Game broken after patching** — run `--restore`. If that also fails partway through, run it again — it picks up where it left off.

---

## Disclaimer

This tool is intended for use with software you legitimately own. Use responsibly.