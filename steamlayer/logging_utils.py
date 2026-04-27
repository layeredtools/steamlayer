from __future__ import annotations

import logging
from contextlib import contextmanager

from rich.console import Console
from rich.logging import RichHandler

console = Console(stderr=True)


def success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


@contextmanager
def spinner(message: str):
    with console.status(f"[dim]{message}[/dim]") as status:
        yield status


def configure_logging(*, level: int = logging.DEBUG) -> None:
    if level <= logging.DEBUG:
        fmt = "%(message)s"
        show_path = True
        show_time = True
    else:
        fmt = "%(message)s"
        show_path = False
        show_time = False

    handler = RichHandler(
        console=console,
        show_time=show_time,
        show_path=show_path,
        rich_tracebacks=True,
        markup=True,
    )
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers[:] = [handler]
    logging.getLogger("urllib3").setLevel(logging.WARNING)
