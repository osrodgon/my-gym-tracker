import re
import unicodedata
import base64
from pathlib import Path

# The keys are the filenames without extension and serve as stable 
# identifiers, independent of the machine name.
MACHINE_IMAGES = {
    "abdominales": "machines/abs.svg",
    "abduccion": "machines/abduction.svg",
    "contraccion-abdominal": "machines/abdominal-crunch.svg",
    "curl-de-biceps": "machines/bicep-curl.svg",
    "curl-de-piernas": "machines/leg-curl.svg",
    "extension-de-espalda": "machines/back-extension.svg",
    "extension-de-gemelos": "machines/calf-extension.svg",
    "extension-de-piernas": "machines/leg-extension.svg",
    "extension-de-triceps": "machines/tricep-extension.svg",
    "jalon-al-pecho": "machines/lat-pulldown.svg",
    "mancuernas": "machines/dumbbells.svg",
    "press-de-hombros": "machines/shoulder-press.svg",
    "press-de-pecho": "machines/chest-press.svg",
    "press-de-piernas": "machines/leg-press.svg",
    "press-de-triceps": "machines/tricep-press.svg",
}

_INVERTED_COLORS = {
    "#000000": "#ffffff",
    "#000": "#fff",
    "#ffffff": "#000000",
    "#fff": "#000",
    "black": "white",
    "white": "black",
}

_COLOR_RE = re.compile(
    r"(?P<prefix>\b(?:fill|stroke)\s*[:=]\s*[\"']?)"
    r"(?P<color>#(?:ffffff|fff|000000|000)|white|black)"
    r"(?![a-z0-9])",
    re.IGNORECASE,
)

_EMPTY_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>'

def get_machine_image_svg(key: str | None, dark: bool) -> bytes:
    if key is None:
        return _EMPTY_SVG

    svg_path = Path(__file__).resolve().parent / "assets" / MACHINE_IMAGES[key]
    svg = svg_path.read_text(encoding="utf-8")

    if dark:
        svg = _COLOR_RE.sub(
            lambda match: (
                match.group("prefix")
                + _INVERTED_COLORS[match.group("color").lower()]
            ),
            svg,
        )

    return svg.encode("utf-8")


def normalize_machine_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")


def get_machine_image_key(machine_name: str) -> str | None:
    key = normalize_machine_name(machine_name)
    return key if key in MACHINE_IMAGES else None