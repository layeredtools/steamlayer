from __future__ import annotations

import logging
import os
import sys


def _enable_windows_ansi_colors() -> None:
    if os.name != "nt":
        return

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-12)  # STD_ERROR_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        return


class ColorFormatter(logging.Formatter):
    RESET = "\x1b[0m"
    COLORS = {
        logging.DEBUG: "\x1b[35m",  # purple
        logging.INFO: "\x1b[34m",  # blue
        logging.WARNING: "\x1b[33m",  # yellow
        logging.ERROR: "\x1b[31m",  # red
        logging.CRITICAL: "\x1b[31;1m",  # bright red
    }

    def __init__(self, fmt: str, datefmt: str | None = None, *, use_colors: bool = True) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        if not self.use_colors:
            return msg
        color = self.COLORS.get(record.levelno)
        if not color:
            return msg
        return f"{color}{msg}{self.RESET}"


def configure_logging(*, level: int = logging.DEBUG) -> None:
    _enable_windows_ansi_colors()

    if level <= logging.DEBUG:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
    else:
        fmt = "[%(levelname)s] %(message)s"
        datefmt = None

    use_colors = sys.stderr.isatty()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(ColorFormatter(fmt=fmt, datefmt=datefmt, use_colors=use_colors))

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers[:] = [handler]

    logging.getLogger("urllib3").setLevel(logging.WARNING)
