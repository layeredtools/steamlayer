from __future__ import annotations

import abc
import pathlib
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from ..fileops import SteamAPIDll


class EmulatorConfig(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def set_account_name(self, new_account: str) -> Self: ...
    @abc.abstractmethod
    def set_language(self, new_language: str) -> Self: ...
    @abc.abstractmethod
    def set_dlcs(self, new_dlcs: dict[int | str, str]) -> Self: ...
    @abc.abstractmethod
    def write(self, dest: pathlib.Path) -> None: ...


class Emulator(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def config_files(self) -> list[str]: ...

    @property
    @abc.abstractmethod
    def settings_dir_name(self) -> str: ...

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
    def validate(self) -> None: ...

    @abc.abstractmethod
    def patch_game(self, *, dlls: list[SteamAPIDll]) -> list[SteamAPIDll]: ...

    @abc.abstractmethod
    def create_config_files(
        self,
        *,
        config: EmulatorConfig,
        appid: int | None,
        game_path: pathlib.Path,
        dll_paths: list[pathlib.Path],
        **kwargs: Any,
    ) -> None: ...
