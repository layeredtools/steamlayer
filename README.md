# steamlayer

Automatically patches Steam games to use the Goldberg Steam Emulator, replacing Steam API calls with a local compatibility layer and unlocking DLCs — minimal setup required.

---

## ⚠️ Before You Run

**If you have Windows Defender real-time protection enabled, add an exclusion before running this tool:**

1. Open **Windows Security** → **Virus & threat protection**
2. Click **Manage settings**
3. Scroll to **Exclusions**
4. Click **Add or remove exclusions**
5. Click **Add an exclusion** → **Folder**
6. Select (or type) this path:
   ```
   C:\Users\<you>\.steamlayer\vendors
   ```

**Why?**  
Replacing Steam API DLLs behaves similarly to how malware modifies executables. Defender may flag Goldberg as a false positive regardless of source.

This exclusion is scoped to a single folder and does not reduce your system-wide protection.

---

## Features

- **Auto-detects the game's AppID** from local files, a community app index, or the Steam store search API
- **Fetches DLC metadata** automatically and writes it to Goldberg's config
- **Bootstraps its own dependencies** (7-Zip and Goldberg) on first run
- **Safe patching** — original DLLs are backed up and fully restorable
- **Dry-run mode** — preview changes without modifying files
- **Offline mode** — works from cached data only

---

## Requirements

- Python 3.13+
- Windows
- An existing `7z.exe` on your system (either in PATH or installed in the default location) **for the very first run**

---

## Usage

```
steamlayer <game_path> [options]
```

### Arguments

| Argument | Description |
|---|---|
| `game` | Path to the game directory (or any file inside it) |
| `-a`, `--appid` | Manually specify the Steam AppID |
| `-d`, `--dry-run` | Preview changes without modifying files |
| `-n`, `--no-network` | Disable network access (use cached data only) |
| `-v`, `--verbose` | Increase verbosity (`-v` = info, `-vv` = debug) |
| `-r`, `--restore` | Restore original files |
| `-y`, `--yolo` | Accept lower-confidence AppID guesses |
| `--cache-dir` | Custom cache directory (default: `~/.steamlayer/.cache`) |
| `--no-defender-check` | Skip Defender warning |

---

### Examples

```bash
# Basic usage
steamlayer "C:\Games\Portal 2"

# Manual AppID
steamlayer "C:\Games\Portal 2" --appid 620

# Dry run
steamlayer "C:\Games\Portal 2" --dry-run

# Restore
steamlayer "C:\Games\Portal 2" --restore

# Offline mode
steamlayer "C:\Games\Portal 2" --no-network
```

---

## How It Works

### 1. Bootstrap

On first run, steamlayer installs dependencies into:

```
~/.steamlayer/vendors/
```

- **7-Zip** — downloaded and extracted using an existing system 7z
- **Goldberg Emulator** — downloaded from GitHub and extracted using the vendored 7-Zip

Subsequent runs skip this step if dependencies are already present.

---

### 2. AppID Discovery

Resolution order:

1. CLI argument
2. Local files (`steam_appid.txt`, Steam manifests)
3. Local community index
4. Steam store API

If multiple matches are found, you’ll be prompted to choose.

---

### 3. DLC Fetch

DLC metadata is fetched and cached locally. Missing entries are resolved individually.

---

### 4. Patching

For each `steam_api.dll` / `steam_api64.dll`:

1. Original DLL is backed up
2. Goldberg DLL replaces it
3. Configuration files are written:
   - `configs.app.ini`
   - `configs.user.ini`
   - `steam_appid.txt`

---

### 5. Restore

`--restore` will:

- Restore original DLLs
- Remove generated config
- Clean up vault directory

---

## Data & Cache

All data is stored in:

```
~/.steamlayer/
```

| Path | Contents |
|---|---|
| `vendors/7zip/` | 7-Zip binary |
| `vendors/goldberg/` | Goldberg emulator |
| `.cache/` | DLC cache |

---

## Troubleshooting

### 7-Zip bootstrap fails

Install 7-Zip and ensure it is:

- available in PATH, or
- installed in `C:\Program Files\7-Zip\`

---

### AppID not detected correctly

Run with:

```bash
steamlayer <game> --appid <id>
```

---

### Game issues after patching

Restore original files:

```bash
steamlayer <game> --restore
```

---

## Disclaimer

This tool is intended for use with software you legitimately own. Use responsibly.