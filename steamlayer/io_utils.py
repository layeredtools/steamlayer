from __future__ import annotations

from typing import Protocol


class IOInterface(Protocol):
    def write(self, message: str) -> None: ...

    def read(self, prompt: str = "") -> str: ...


class ConsoleIO:
    def write(self, message: str) -> None:
        print(message)

    def read(self, prompt: str = "") -> str:
        return input(prompt).strip()
