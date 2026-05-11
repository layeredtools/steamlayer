from pathlib import Path
from steamlayer_core import GoldbergLocalVendorProvider, GoldbergConfigWriter

# Points to the vendors/ directory bundled alongside the backend binary.
# When frozen by PyInstaller, sys._MEIPASS is the extraction directory.
import sys

_base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))

vendor = GoldbergLocalVendorProvider(_base / "vendors")
config_writer = GoldbergConfigWriter()