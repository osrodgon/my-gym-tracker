"""Startup options read from the command line.

The desktop runner Flet generates for a packaged build treats *any* command
line argument as developer mode: it reads ``argv[0]`` as the URL of a running
server and never starts the bundled Python, so the window stays blank.
``build.sh`` therefore writes an ``AppRun`` that hands the AppImage's arguments
to the app through ``GYMTRACKER_ARGS`` (newline-separated) and execs the binary
without arguments; :func:`parse_args` reads both that variable and, for
``python main.py``/``flet run``, ``sys.argv``.
"""

import argparse
import os
import sys
from dataclasses import dataclass

import flet as ft

THEME_MODES = {
    "system": ft.ThemeMode.SYSTEM,
    "light": ft.ThemeMode.LIGHT,
    "dark": ft.ThemeMode.DARK,
}
"""Accepted ``--theme`` values. ``system`` follows the OS setting."""

DEFAULT_THEME = "system"
"""Theme used when ``--theme`` is omitted: follow the OS, as before."""

WINDOW_SIZES = {
    "pixel-7-pro": (412, 892),
    "pixel-10": (412, 923),
}
"""Logical (dp) viewport of each phone. The window reproduces the width the app
has on the device itself; the physical resolution (1440x3120 and 1080x2424
pixels) would be three times too big on the desktop."""

DEFAULT_WINDOW_SIZE = (540, 960)
"""Window used when ``--size`` is omitted: the app's original preview size,
which does not match any real phone."""

ARGS_ENV = "GYMTRACKER_ARGS"
"""Variable where the AppImage's ``AppRun`` leaves its arguments, one per line.
Newlines keep a value such as ``"Pixel 7 Pro"`` intact without shell quoting."""


@dataclass(frozen=True)
class AppOptions:
    """Resolved startup options, with every default already applied."""

    theme_mode: ft.ThemeMode
    window_width: int
    window_height: int


def _device_size(value: str) -> tuple[int, int]:
    """Map ``--size`` to a window size, ignoring case and separators."""
    key = value.strip().lower().replace(" ", "-").replace("_", "-")
    if key not in WINDOW_SIZES:
        raise argparse.ArgumentTypeError(
            f"'{value}' is not a valid size; choose from "
            + ", ".join(WINDOW_SIZES)
        )
    return WINDOW_SIZES[key]


def _app_argv() -> list[str]:
    """Arguments meant for the app, in development and packaged runs alike.

    ``python main.py`` and ``flet run`` keep the script at ``sys.argv[0]``, so
    it is dropped; the AppImage's launcher carries its arguments in
    ``GYMTRACKER_ARGS``, which comes first so an explicit argument on the
    command line still wins.
    """
    argv = [
        line
        for line in os.environ.get(ARGS_ENV, "").splitlines()
        if line.strip()
    ]
    cli = [arg for arg in sys.argv if arg]
    if cli and cli[0].endswith(".py"):
        cli = cli[1:]
    return argv + cli


def parse_args(argv: list[str] | None = None) -> AppOptions:
    """Parse the app's own arguments, ignoring the script path when present."""
    parser = argparse.ArgumentParser(
        prog="Mi Gimnasio",
        description="Mi Gimnasio startup options.",
    )
    parser.add_argument(
        "--theme",
        type=str.lower,
        choices=tuple(THEME_MODES),
        default=DEFAULT_THEME,
        help=(
            "UI theme: "
            + ", ".join(THEME_MODES)
            + f" (default: {DEFAULT_THEME})"
        ),
    )
    parser.add_argument(
        "--size",
        type=_device_size,
        metavar="phone",
        help=(
            "window sized as a phone's logical viewport: "
            + ", ".join(WINDOW_SIZES)
            + f" (default: {DEFAULT_WINDOW_SIZE[0]}x"
            + f"{DEFAULT_WINDOW_SIZE[1]})"
        ),
    )
    parsed = parser.parse_args(_app_argv() if argv is None else argv)
    width, height = parsed.size or DEFAULT_WINDOW_SIZE
    return AppOptions(THEME_MODES[parsed.theme], width, height)
