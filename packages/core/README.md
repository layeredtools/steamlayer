<div align="center">

# steamlayer-core

[![PyPI](https://img.shields.io/pypi/v/steamlayer-core)](https://pypi.org/project/steamlayer-core/)
[![Python](https://img.shields.io/pypi/pyversions/steamlayer-core)](https://pypi.org/project/steamlayer-core/)
[![CI](https://img.shields.io/github/actions/workflow/status/layeredtools/steamlayer/ci.yml?branch=main&label=ci)](https://github.com/layeredtools/steamlayer/actions)
[![License](https://img.shields.io/github/license/layeredtools/steamlayer)](https://github.com/layeredtools/steamlayer/blob/main/LICENSE)

The emulator-agnostic engine behind SteamLayer. Handles Steam game identification,
DRM patching, and DLC hydration — with no opinion about which emulator you use.
</div>

> Part of the [SteamLayer monorepo](https://github.com/layeredtools/steamlayer).

---

## Installation

```bash
pip install steamlayer-core
```

Python 3.13+ required.

## Quick start

```python
from pathlib import Path
from steamlayer_core.api import SteamLayerClient

with SteamLayerClient(vendor=vendor, config_writer=writer) as client:
    game = client.resolve(Path("C:/games/Hollow Knight"))
    dlcs = client.fetch_dlcs(game.appid)
    result = client.patch(game, Path("C:/games/Hollow Knight"))
```

## Core concepts

### Resolution waterfall

When you call `resolve()`, the engine tries each strategy in order, stopping as soon as a confident match is found:
```
Game directory
      │
      ▼
Local file inspection    (steam_appid.txt, appmanifest_*.acf, ...)
      │ no match
      ▼
App index lookup         (offline index bootstrapped on first run)
      │ no match / low confidence
      ▼
Steam store search       (live web query, skipped if allow_network=False)
      │ ambiguous
      ▼
Disambiguation callback  (your on_disambiguation handler, or AmbiguousMatchError)
```

### Emulator agnosticism

`steamlayer-core` never references a specific emulator. It interacts with two protocols that you implement (or get from an emulator-specific package):

| Protocol | Responsibility |
|---|---|
| `VendorProvider` | Supplies the emulator DLL binaries to be written into the game directory |
| `ConfigWriter` | Defines what config files to write and where (AppID, DLC list, etc.) |

The same core library can drive Goldberg, or any future emulator, just by swapping the injected implementations.

### Backup vault

Before any file is overwritten, `patch()` creates a local vault inside the game directory. `unpatch()` reads exclusively from this vault — it does not need to know which emulator was used. `purge_vault=True` (default) deletes the vault after a successful restore.

### DLC caching

`fetch_dlcs()` caches results to `~/.steamlayer/.cache/dlcs_{appid}.json`. Subsequent calls within the TTL window never touch the network. The cache path and TTL are configurable via `SteamlayerOptions`.

## Handling disambiguation

Resolution may suspend and ask for a decision in two cases:

```python
with SteamLayerClient(
    on_disambiguation=my_disambiguation_handler,
    on_confirmation=my_confirmation_handler,
) as client:
    game = client.resolve(path)
```

| Callback | Triggered when |
|---|---|
| `on_disambiguation` | Multiple candidates found with similar confidence |
| `on_confirmation` | A single candidate found below the confidence threshold |

Both callbacks receive an event and must return a `DiscoveryResult`. If no handler is provided, the engine raises `AmbiguousMatchError` or `LowConfidenceError` instead.

## Contributing

Open an issue before starting significant work so we can discuss the approach.

```bash
git clone https://github.com/layeredtools/steamlayer
cd steamlayer
uv sync
```

## License

[MIT](../../LICENSE)
