from __future__ import annotations

import json
import logging
import threading
from typing import Any

from steamlayer import STATE_FILE

log = logging.getLogger("steamlayer.state")


class StateManager:
    _instance: StateManager | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._data = {}
                cls._instance.load()
        return cls._instance

    def load(self) -> None:
        if not STATE_FILE.exists():
            return
        try:
            self._data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            log.debug(f"Could not load state: {e}")
            self._data = {}

    def save(self) -> None:
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
            log.debug("State synchronized with disk at %s", STATE_FILE)
        except Exception as e:
            log.error(f"Failed to save state: {e}")

    def get_section(self, section: str) -> dict[str, Any]:
        return self._data.get(section, {})

    def update_section(self, section: str, **kwargs: Any) -> None:
        """Ex: state.update_section("goldberg", version="1.2.3", last_check="...")"""
        if section not in self._data or not isinstance(self._data[section], dict):
            self._data[section] = {}

        self._data[section].update(kwargs)
        self.save()

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self._data.get(section, {}).get(key, default)


state = StateManager()
