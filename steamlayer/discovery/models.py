from dataclasses import dataclass
from enum import Enum, auto


class DiscoverySource(Enum):
    MANUAL = auto()
    LOCAL = auto()
    WEB = auto()
    NONE = auto()


@dataclass
class DiscoveryResult:
    appid: int | None = None
    source: DiscoverySource = DiscoverySource.NONE
    confidence: float = 0.0
    game_name: str | None = None
    user_selected: bool = False
