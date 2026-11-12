import re
import unicodedata
from pathlib import Path

# The keys are the filenames without extension and serve as stable 
# identifiers, independent of the machine name. Values are paths under
# assets/; every drawing is a WebP bitmap, so there is no light/dark variant.
MACHINE_IMAGES = {
    "abdominales": "machines/abs.webp",
    "abduccion": "machines/abduction.webp",
    "contraccion-abdominal": "machines/abdominal-crunch.webp",
    "curl-de-biceps": "machines/bicep-curl.webp",
    "curl-de-piernas": "machines/leg-curl.webp",
    "extension-de-espalda": "machines/back-extension.webp",
    "extension-de-gemelos": "machines/calf-extension.webp",
    "extension-de-piernas": "machines/leg-extension.webp",
    "extension-de-triceps": "machines/tricep-extension.webp",
    "jalon-al-pecho": "machines/lat-pulldown.webp",
    "mancuernas": "machines/dumbbells.webp",
    "press-de-hombros": "machines/shoulder-press.webp",
    "press-de-pecho": "machines/chest-press.webp",
    "press-de-piernas": "machines/leg-press.webp",
    "press-de-triceps": "machines/tricep-press.webp",
}

# Shown in the Registrar image card while no machine is selected. It is not a
# selectable machine image, so it stays out of MACHINE_IMAGES.
NO_SELECTION_IMAGE = "machines/no-selection.webp"

# Monochrome machine silhouette used as a small icon (the latest-record banner
# and the rows of the machines list). It is the only SVG in the app: being
# vector and single-colour, it is tinted with `ft.Image.color`.
PLACEHOLDER_IMAGE = "machines/machine.svg"


def _asset_path(relative_path: str) -> Path:
    return Path(__file__).resolve().parent / "assets" / relative_path


def get_machine_image(key: str) -> bytes:
    """WebP bytes of the drawing mapped to `key`, ready for `ft.Image.src`."""
    return _asset_path(MACHINE_IMAGES[key]).read_bytes()


def get_no_selection_image() -> bytes:
    """Generic gym picture shown before a machine is chosen."""
    return _asset_path(NO_SELECTION_IMAGE).read_bytes()


def get_placeholder_image() -> bytes:
    """Raw placeholder SVG, meant to be tinted with `ft.Image.color`."""
    return _asset_path(PLACEHOLDER_IMAGE).read_bytes()


def normalize_machine_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")


def get_machine_image_key(machine_name: str) -> str | None:
    key = normalize_machine_name(machine_name)
    return key if key in MACHINE_IMAGES else None
