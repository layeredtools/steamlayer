# SteamLayer

A toolkit for identifying Steam games, unlocking DLC, and managing game configurations.

## Packages

### [steamlayer-core](core/api/client.md)
The engine that powers everything. Handles Steam game identification, DRM patching, DLC hydration, and vault management. Available as a standalone library on [PyPI](https://pypi.org/project/steamlayer-core/).

### steamlayer-backend
A FastAPI HTTP/WebSocket server that wraps `steamlayer-core` and exposes it to the Electron frontend.

### steamlayer-app
The Electron + React GUI. Built on top of the backend, providing a modern interface for resolving and patching games.

## Architecture
```
app (Electron + React)
└── backend (FastAPI)
└── core (steamlayer-core)
```

## Contributing

Issues and pull requests are welcome. Please open an issue before starting significant work so we can discuss the approach.

## License

MIT
