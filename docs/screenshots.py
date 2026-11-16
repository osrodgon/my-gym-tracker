"""Regenerate the screenshots used by the user manual (`docs/manual.md`).

The app is started in web mode against a throwaway SQLite database, so no real
data is touched, and every picture is taken from the running UI with a headless
Chromium at the logical size of a phone (412x892 dp, 2x pixel density, the same
viewport `--size pixel-7-pro` gives the window).

Usage::

    pip install playwright
    playwright install chromium
    python docs/screenshots.py            # writes docs/img/*.png
    python docs/screenshots.py --out DIR  # writes somewhere else

The clicks are expressed in the CSS pixels of that 412x892 viewport. They follow
the current layout (`ui/design.py` scale, list order of `get_machines()`, menu
row height), so a redesign of a tab means re-measuring the coordinates below:
take a screenshot, read the target position and update the `_*_Y` constants.
"""

import argparse
import os
import resource
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUT = PROJECT_DIR / "docs" / "img"

VIEWPORT = {"width": 412, "height": 892}
DEVICE_SCALE_FACTOR = 2
PORT = 8550
URL = f"http://localhost:{PORT}"

BOOT_SECONDS = 6
"""The Flutter web client paints after the Python side answers the websocket:
anything shorter than this catches a half-drawn first frame."""

SETTLE_SECONDS = 1.2
"""Pause after a click, so the ripple, the menu animation or the dialog entrance
have finished before the screenshot."""

MIN_PNG_BYTES = 40_000
"""Smallest plausible PNG for a real screen. Flet shows a blank page with a
"Working…" spinner while it is still connecting or while the Python side is
blocked, and that capture compresses to a few kilobytes; a screenshot that
small is retried instead of being written."""

CONTENT_WAIT_SECONDS = 20
"""How long to wait for the UI to replace that blank/"Working…" frame."""

# --- Layout coordinates (CSS px) -------------------------------------------
# Measured on the 412x892 viewport. The 3-destination bar is 100dp tall, the
# navigation bar labels sit near y=862 in each third of the width.
NAV_REGISTRAR = (68, 862)
NAV_HISTORY = (206, 862)
NAV_MACHINES = (343, 862)

MACHINE_DROPDOWN = (206, 58)
"""Registrar machine selector, top of the panel."""

WEIGHT_FIELD = (104, 660)
REPS_FIELD = (308, 660)
SAVE_BUTTON = (206, 752)
REGISTRAR_HEADER = (206, 120)
"""Neutral spot (the latest-record banner) used to drop the focused field."""

MENU_FIRST_ROW_Y = 118
MENU_ROW_HEIGHT = 40
"""First option and row pitch of an open dropdown menu."""

FAB = (368, 748)
"""Regular FAB at the end of the page, above the navigation bar."""

SHEET_EXPORT = (206, 782)
SHEET_IMPORT = (206, 832)

MACHINE_NAME_FIELD = (206, 112)
MACHINE_FORM_TITLE = (206, 45)
DELETE_FIRST_MACHINE = (377, 54)

FIRST_HISTORY_CARD = (206, 80)
"""Summary card of the most recent machine, which the shot expands."""

OVERWRITE_DIALOG_CANCEL = (158, 540)
"""`Cancelar` of the duplicate/overwrite dialog (the other button is
`Sobrescribir`, at x=281)."""

IMPORT_DIALOG_CANCEL = (178, 530)
"""`Cancelar` of the import confirmation, which sits further left because
`Continuar` is shorter than `Sobrescribir`."""

FORM_CANCEL = (206, 689)
"""`Cancelar` of the create/rename form, full width above `Crear máquina`."""

# --- Demo data -------------------------------------------------------------
# Names are picked from `machine_images.MACHINE_IMAGES`, so the drawings show up
# in the Registrar card, the machine preview and the history cards.
MACHINES = [
    "Press de pecho",
    "Jalón al pecho",
    "Press de piernas",
    "Extensión de piernas",
    "Curl de bíceps",
    "Press de hombros",
]

# (machine name, days ago, weight, reps); today's entry on "Press de pecho" is
# what the duplicate dialog screenshot overwrites.
USAGES = [
    ("Press de pecho", 0, 60.0, 12),
    ("Press de pecho", 2, 57.5, 12),
    ("Press de pecho", 5, 55.0, 12),
    ("Press de pecho", 9, 50.0, 10),
    ("Jalón al pecho", 1, 45.0, 12),
    ("Jalón al pecho", 3, 42.5, 12),
    ("Jalón al pecho", 7, 40.0, 10),
    ("Press de piernas", 1, 120.0, 10),
    ("Press de piernas", 4, 110.0, 10),
    ("Press de piernas", 8, 100.0, 12),
    ("Extensión de piernas", 2, 55.0, 12),
    ("Extensión de piernas", 6, 50.0, 12),
    ("Curl de bíceps", 2, 20.0, 12),
    ("Curl de bíceps", 7, 17.5, 12),
    ("Press de hombros", 3, 30.0, 10),
]

DEMO_MACHINE = "Press de pecho"
DEMO_WEIGHT = "62,5"
DEMO_REPS = "10"
NEW_MACHINE_NAME = "Abdominales"
"""Typed in the create form: it has a drawing, so the preview shows the
automatically suggested image and the dropdown picks it up."""


def _port_is_free(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _port_owner(port: int) -> str:
    """Human-readable owner of `port`, for the error message. Best effort: `ss`
    is Linux-only and the script must still work without it."""
    try:
        output = subprocess.run(
            ["ss", "-ltnp", f"sport = :{port}"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    for line in output.splitlines()[1:]:
        if "pid=" in line:
            return " ".join(line.split())
    return ""


def _wait_port_free(timeout: float = 30) -> None:
    """Wait for the previous app to release the port.

    The light-theme run is stopped and the dark one started in the same process,
    and the socket does not free the instant the child exits. If it never frees,
    the port belongs to something else, and continuing would serve the
    screenshots from the wrong app, so the run stops with the owner's pid.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_is_free(PORT):
            return
        time.sleep(0.2)
    raise RuntimeError(
        f"Port {PORT} is still taken after {timeout:.0f}s: {_port_owner(PORT)}. "
        "Stop that process (an app left running by an interrupted screenshot "
        "run does this) and try again."
    )


def _wait_for_app(timeout: float = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.3)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.3)
    raise TimeoutError(f"The app did not open {URL} within {timeout:.0f}s")


def _die_with_parent():
    """`preexec_fn` that kills the app when this script dies.

    `timeout`, Ctrl-C or a cancelled run kill the script, not its children, and
    an orphaned app keeps port 8550 busy (the next run then reads the screenshots
    from the wrong process). Linux-only: elsewhere the app is only stopped by
    `App.stop()`. `PR_SET_PDEATHSIG` is 1.
    """
    if not sys.platform.startswith("linux"):
        return None

    def _set_pdeathsig() -> None:
        import ctypes
        import signal

        ctypes.CDLL("libc.so.6", use_errno=True).prctl(1, signal.SIGTERM)

    return _set_pdeathsig


class App:
    """The app running in web mode, against `self.workdir/gym.db`.

    `GYMTRACKER_ARGS` is not needed here: `main.py` parses its arguments from
    `sys.argv` when it is started with `python main.py`, so the flags go on the
    command line as usual.
    """

    def __init__(self, workdir: Path, args: tuple[str, ...] = ()):
        self.db_path = workdir / "gym.db"
        self.workdir = workdir
        self.args = list(args)
        self._process: subprocess.Popen | None = None
        self._log = workdir / "app.log"

    def seed(self) -> None:
        sys.path.insert(0, str(PROJECT_DIR))
        from database import GymDatabase
        from machine_images import get_machine_image_key

        if self.db_path.exists():
            self.db_path.unlink()

        db = GymDatabase(str(self.db_path))
        db.replace_data(
            [(name, get_machine_image_key(name)) for name in MACHINES], []
        )
        machine_ids = {name: mid for mid, name, _ in db.get_machines()}

        with sqlite3.connect(self.db_path) as conn:
            for name, days_ago, weight, reps in USAGES:
                conn.execute(
                    """
                    INSERT INTO usages (machine_id, weight, reps, date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        machine_ids[name],
                        weight,
                        reps,
                        (date.today() - timedelta(days=days_ago)).isoformat(),
                    ),
                )

    def __enter__(self) -> "App":
        _wait_port_free()
        env = dict(os.environ)
        # `main.py` imports the `ui` package and the assets path resolves from
        # the module, so only the import path has to point at the project.
        env["PYTHONPATH"] = str(PROJECT_DIR)
        self._process = subprocess.Popen(
            [sys.executable, str(PROJECT_DIR / "main.py"), *self.args],
            cwd=str(self.workdir),
            env=env,
            stdout=self._log.open("w"),
            stderr=subprocess.STDOUT,
            preexec_fn=_die_with_parent(),
        )
        try:
            _wait_for_app()
        except Exception:
            self.stop()
            raise
        return self

    def __exit__(self, *_exc) -> None:
        self.stop()

    def stop(self) -> None:
        if self._process is None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=10)
        self._process = None


class DarkApp(App):
    """Same app, forced to the dark theme from the command line (see
    `AppOptions`), which is what the manual's dark screenshot documents."""

    def __init__(self, workdir: Path):
        super().__init__(workdir, ("--theme", "dark"))


class Screenshotter:
    def __init__(self, browser, out_dir: Path, dark: bool = False):
        self.browser = browser
        self.out_dir = out_dir
        self.dark = dark
        self.page = None
        self._last_capture: bytes | None = None

    def __enter__(self) -> "Screenshotter":
        self.context = self.browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=DEVICE_SCALE_FACTOR,
            is_mobile=True,
            has_touch=True,
            color_scheme="dark" if self.dark else "light",
        )
        self.page = self.context.new_page()
        self.page.goto(URL, wait_until="networkidle")
        time.sleep(BOOT_SECONDS)
        return self

    def __exit__(self, *_exc) -> None:
        self.context.close()

    # -- helpers ---------------------------------------------------------

    def click(self, point: tuple[float, float]) -> None:
        self.page.mouse.click(*point)
        time.sleep(SETTLE_SECONDS)

    def type(self, point: tuple[float, float], text: str) -> None:
        self.click(point)
        self.page.keyboard.type(text)
        time.sleep(0.4)

    def save(self, name: str) -> None:
        """Capture the page and save it as `name`.

        Flet shows a blank page with a "Working…" spinner while it is still
        connecting or while the Python side is blocked, and that capture
        compresses to a few kilobytes, so anything that small is retried. A
        capture identical to the previous one means a click did not take effect,
        which would silently document the wrong screen.
        """
        path = self.out_dir / name
        deadline = time.time() + CONTENT_WAIT_SECONDS
        while True:
            raw = self._capture(name)
            if len(raw) >= MIN_PNG_BYTES:
                break
            if time.time() > deadline:
                raise RuntimeError(
                    f"{name} came out at {len(raw)} bytes: the page was still "
                    'blank or showing Flet\'s "Working…" overlay. Retry the run '
                    f"with port {PORT} served only by it."
                )
            time.sleep(0.5)

        if raw == self._last_capture:
            raise RuntimeError(
                f"{name} is identical to the previous screenshot: whatever the "
                "script clicked before it did not take effect (a mis-measured "
                "coordinate, usually a dialog button)."
            )
        self._last_capture = raw
        path.write_bytes(raw)
        print(f"  {path.relative_to(PROJECT_DIR)}")

    def _capture(self, name: str) -> bytes:
        """PNG bytes of the viewport, at the context's 2x device scale factor.

        Playwright's own screenshot is the only capture that honours the scale
        factor: CDP's `Page.captureScreenshot` returns 412x892, and forcing the
        factor with `Emulation.setDeviceMetricsOverride` makes Flutter lay the
        app out wider than the viewport. It very occasionally waits for a frame
        that the software compositor never presents, so it is retried a couple
        of times.
        """
        for attempt in range(3):
            try:
                return self.page.screenshot(timeout=15_000)
            except PlaywrightTimeoutError:
                if attempt == 2:
                    raise RuntimeError(
                        f"Chromium never painted a frame for {name}. Retry the "
                        "screenshots; if it repeats, restart the container (the "
                        "software compositor gets stuck)."
                    ) from None
                time.sleep(1)

    # -- screens ---------------------------------------------------------

    def select_machine(self) -> None:
        """Open the Registrar dropdown and pick the demo machine."""
        self.click(MACHINE_DROPDOWN)
        index = sorted(MACHINES).index(DEMO_MACHINE)
        y = MENU_FIRST_ROW_Y + index * MENU_ROW_HEIGHT
        self.click((MACHINE_DROPDOWN[0], y))

    def fill_series(self) -> None:
        self.type(WEIGHT_FIELD, DEMO_WEIGHT)
        self.type(REPS_FIELD, DEMO_REPS)
        self.click(REGISTRAR_HEADER)

    def go_to(self, destination: tuple[float, float]) -> None:
        self.click(destination)


def take_shots(browser, out_dir: Path, workdir: Path) -> None:
    # One page per theme: every shot continues where the previous one left off,
    # which is also how a user moves through the app. Opening a page per shot
    # multiplied the session handshakes, and one of them occasionally stayed on
    # Flet's blank "Working…" screen.
    #
    # The two apps cannot overlap in time: both listen on the same port, so the
    # light one is stopped before the dark one starts.
    print("Light theme")
    with App(workdir):
        with Screenshotter(browser, out_dir) as ui:
            # Registrar before choosing a machine: generic drawing and hint.
            ui.save("01-register-empty.png")

            # Registrar with a machine, its last record and a filled set.
            ui.select_machine()
            ui.fill_series()
            ui.save("02-register-set.png")

            # Saving a second set for the same day asks before overwriting.
            ui.click(SAVE_BUTTON)
            ui.save("04-register-overwrite-warning.png")
            ui.click(OVERWRITE_DIALOG_CANCEL)

            # Historial with the first machine expanded.
            ui.go_to(NAV_HISTORY)
            ui.click(FIRST_HISTORY_CARD)
            ui.save("05-history.png")

            # Excel actions live behind the Historial FAB.
            ui.click(FAB)
            ui.save("06-history-excel-options.png")

            # Importing replaces every machine and record: confirm first.
            ui.click(SHEET_IMPORT)
            ui.save("07-import-warning.png")
            ui.click(IMPORT_DIALOG_CANCEL)

            # Machine list with its per-row rename and delete actions.
            ui.go_to(NAV_MACHINES)
            ui.save("08-machine-list.png")

            # Create form: typing a known name suggests its drawing.
            ui.click(FAB)
            ui.type(MACHINE_NAME_FIELD, NEW_MACHINE_NAME)
            ui.click(MACHINE_FORM_TITLE)
            ui.save("09-create-machine.png")
            ui.click(FORM_CANCEL)

            # Deleting a machine warns that its records go with it.
            ui.click(DELETE_FIRST_MACHINE)
            ui.save("10-delete-machine.png")

    print("Dark theme")
    with DarkApp(workdir):
        with Screenshotter(browser, out_dir, dark=True) as ui:
            # The dark theme keeps the same layout, with a fainter drawing.
            ui.select_machine()
            ui.fill_series()
            ui.save("03-register-dark-theme.png")


def main() -> None:
    # A crashed Chromium leaves a core dump of close to a gigabyte in the
    # working directory, and one of those ended up committed. The child
    # processes inherit the limit, so nothing can write a core file.
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Screenshot folder (default: {DEFAULT_OUT.relative_to(PROJECT_DIR)})",
    )
    args = parser.parse_args()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="gymtracker-shots-") as tmp:
        workdir = Path(tmp)
        App(workdir).seed()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            take_shots(browser, out_dir, workdir)
            browser.close()

    print(f"\nDone: {len(list(out_dir.glob('*.png')))} screenshots in {out_dir}")


if __name__ == "__main__":
    main()
