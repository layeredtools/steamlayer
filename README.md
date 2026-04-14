<div align="center">

# steamlayer

  Patches Steam games to run through the [Goldberg emulator](https://github.com/Detanup01/gbe_fork).  
  Finds the AppID, grabs DLC info, swaps the DLLs, backs up the originals. One command.

<p>
    <a href="https://pypi.org/project/steamlayer/"><img src="https://img.shields.io/pypi/v/steamlayer?style=for-the-badge&color=blue" alt="PyPI version"></a>
    <a href="https://github.com/layeredtools/steamlayer/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/layeredtools/steamlayer/ci.yml?branch=main&style=for-the-badge" alt="Build Status"></a>
    <a href="https://pypi.org/project/steamlayer/"><img src="https://img.shields.io/pypi/pyversions/steamlayer?style=for-the-badge" alt="Python Versions"></a>
    <a href="https://github.com/layeredtools/steamlayer/blob/main/LICENSE"><img src="https://img.shields.io/github/license/layeredtools/steamlayer?style=for-the-badge" alt="License"></a>
  </p>

  <br>
  
  <a href="https://raw.githubusercontent.com/layeredtools/steamlayer/main/Animation.gif">
    <img src="https://raw.githubusercontent.com/layeredtools/steamlayer/main/Animation.gif" width="750" alt="steamlayer demo">
  </a>
</div>

<br>

> [!TIP]
> Point it at a game folder. It figures out the AppID, pulls DLC metadata, backs up the original `steam_api.dll` files, drops in Goldberg's replacements, and strips SteamStub DRM automatically.

## 📋 Table of Contents
- [🚀 What it does](#-what-it-does)
- [📦 Installation](#-installation)
- [🛠️ Usage](#️-usage)
- [⚙️ How it works](#️-how-it-works)
    - [🔍 AppID detection](#-appid-detection)
    - [📦 DLC metadata](#-dlc-metadata)
    - [🛡️ SteamStub detection](#️-steamstub-detection)
    - [🛠️ Patching](#️-patching)
    - [🩹 Restore](#-restore)
    - [📂 Storage & Caching](#-storage--caching)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [💻 Development](#-development)
- [⚖️ Disclaimer](#️-disclaimer)

## 🚀 What it does
`steamlayer` automates the tedious manual work of setting up game environments. It handles AppID discovery, DLC metadata fetching, DLL swapping, and SteamStub stripping in a single pass—all while keeping your original files safe in a managed vault.

* 🔍 **Smart Discovery:** Automatically filters out release tags (FitGirl, RUNE, etc.) and version numbers to find the correct AppID.
* 📦 **DLC Support:** Automatically generates DLC lists for the emulator.
* 🛡️ **SteamStub Stripping:** Detects and unwraps DRM using Steamless.
* 🔒 **Safe-by-Design:** Atomic restores ensure your game files can always be returned to their original state.

> [!WARNING]
> steamlayer is under active development and not yet production-ready. Expect rough edges, and always keep `--restore` in mind.


## 📦 Installation
**Requirements:**
* Python 3.13+
* Windows
* 7-Zip somewhere on your system for the very first run (after that steamlayer manages its own copy).

```bash
pip install steamlayer
```

## 🛠️ Usage

<details>
<summary><b>📋 View All CLI Options</b></summary>

| Flag | Description |
|---|---|
| `-a`, `--appid <id>` | Skip auto-detection and use this AppID |
| `-d`, `--dry-run` | Show what would happen, don't touch anything |
| `-n`, `--no-network` | Use cached data only, no requests |
| `-r`, `--restore` | Put the original DLLs back and clean up |
| `-u`, `--unpack` | Auto-strip SteamStub DRM via Steamless before patching |
| `-y`, `--yolo` | Accept lower-confidence AppID matches |
| `-v` / `-vv` | More output (`-v` = info, `-vv` = debug) |
| `--cache-dir <path>` | Override the cache location (default: `~/.steamlayer/.cache`) |
| `--no-defender-check` | Skip the Defender warning |
| `--version` | Print the version and exit |
</details>
<br>

```bash
# Standard automatic patch
steamlayer "C:\Games\Portal 2"

# Explicit AppID if auto-detection fails
steamlayer "C:\Games\Portal 2" --appid 620

# Strip SteamStub DRM automatically
steamlayer "C:\Games\Portal 2" --unpack

# Undo everything cleanly
steamlayer "C:\Games\Portal 2" --restore
```

## 🛡️ Windows Defender
> [!IMPORTANT] 
> If real-time protection is on, add a folder exclusion before running:
>
> **Windows Security → Virus & threat protection → Manage settings → Exclusions → Add an exclusion → Folder**
>
> ```
> C:\Users\<you>\.steamlayer\vendors
> ```
> Swapping Steam DLLs looks suspicious enough that Defender will sometimes quarantine Goldberg's or Steamless's files mid-download. The exclusion keeps that from happening. It only covers this one folder, nothing else on your system.

## ⚙️ How it works
### 🔍 AppID detection
checks for `steam_appid.txt` or `.acf` manifest files in the game folder first. If nothing's there, it searches a locally-cached community index, then falls back to the Steam store API. If two results look equally likely, it asks you to pick. Pass `--yolo` to lower the confidence threshold (useful for sequels or non-standard folder names).

---

### 📦 DLC metadata
fetches the DLC list from the Steam API and resolves names using the same community index. Anything missing from the index gets looked up individually. Results are cached for a week so repeat runs are fast. ⚡

---

### 🛡️ SteamStub detection
before patching, steamlayer scans every `.exe` in each DLL's directory for SteamStub DRM. It recognises v1.x (via `SteamDRMP.dll` import) and v3.x (via the `0xCAFEDEAD` header magic in the `.bind` section). If wrapped executables are found and `--unpack` wasn't passed, it warns you. With `--unpack`, Steamless strips the DRM automatically and the original executable is vaulted alongside the DLLs.

---

### 🛠️ Patching 
finds every `steam_api.dll` and `steam_api64.dll` in the game tree, vaults the originals to `<game>/__original_files__/`, and copies in the right Goldberg DLL (x32 or x64). Config files go in a `steam_settings/` folder next to each DLL, plus a `steam_appid.txt` at the game root. 🏗️

---

### 🩹 Restore
moves the vaulted DLLs (and any vaulted executables) back, deletes the `steam_settings/` directories, cleans up loose config files, and removes the vault once it's empty. Safe to re-run if it fails partway through. 🔄

---

### 📂 Storage & Caching
Confines all downloaded tools and caches to `~/.steamlayer/`.

`vendors/`: Managed portable installations of 7-Zip, Goldberg, and Steamless. 📥

`.cache/`: Stores Steam DLC metadata (7-day TTL) for instantaneous repeat runs. 🏎️


## 💻 Development
This project uses `uv` for dependency management.
```bash
# 📂 Clone the repository
git clone https://github.com/layeredtools/steamlayer.git
cd steamlayer

# 🛠️ Install dependencies and setup environment
uv sync --all-groups

# 🧪 Run the test suite
uv run pytest

# 🧹 Lint and format code
uv run ruff check .
uv run ruff format .
```

## 🛠️ Troubleshooting

📦 **7-Zip bootstrap fails** — steamlayer needs an existing `7z.exe` to pull in its own copy. Make sure it's in `PATH` or installed at the default location (`C:\Program Files\7-Zip\`).

🔍 **Wrong game detected** — use `--appid`. You can find the right ID on [SteamDB](https://www.steamdb.info) or in the store URL.

🛡️ **Defender quarantined something mid-install** — add the exclusion above and re-run. steamlayer will re-download and retry cleanly.

🔐 **SteamStub warning at runtime** — the game executable is wrapped with SteamDRM. Re-run with `--unpack` to strip it automatically, or unpack manually with [Steamless](https://github.com/atom0s/Steamless) first.

🩹 **Game broken after patching** — run `--restore`. If that also fails partway through, run it again — it picks up where it left off.

## ⚖️ Disclaimer
This tool is intended for use with software you legitimately own. Use responsibly.