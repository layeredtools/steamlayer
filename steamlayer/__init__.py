from importlib.metadata import PackageNotFoundError, version

from .constants import STATE_FILE as STATE_FILE
from .constants import TOOL_HOME as TOOL_HOME
from .constants import VENDORS_PATH as VENDORS_PATH
from .state import state as state

try:
    __version__ = version("steamlayer")
except PackageNotFoundError:
    __version__ = "dev"
