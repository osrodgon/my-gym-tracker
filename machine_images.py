import re
import unicodedata

# The keys are the filenames without extension and serve as stable 
# identifiers, independent of the machine name.
MACHINE_IMAGES = {
    "abdominales": "machines/abdominales.svg",
    "abduccion": "machines/abduccion.svg",
    "contraccion-abdominal": "machines/contraccion-abdominal.svg",
    "curl-de-biceps": "machines/curl-de-biceps.svg",
    "curl-de-piernas": "machines/curl-de-piernas.svg",
    "extension-de-espalda": "machines/extension-de-espalda.svg",
    "extension-de-gemelos": "machines/extension-de-gemelos.svg",
    "extension-de-piernas": "machines/extension-de-piernas.svg",
    "extension-de-triceps": "machines/extension-de-triceps.svg",
    "jalon-al-pecho": "machines/jalon-al-pecho.svg",
    "mancuernas": "machines/mancuernas.svg",
    "press-de-hombros": "machines/press-de-hombros.svg",
    "press-de-pecho": "machines/press-de-pecho.svg",
    "press-de-piernas": "machines/press-de-piernas.svg",
    "press-de-triceps": "machines/press-de-triceps.svg",
}


def normalize_machine_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")


def get_machine_image_key(machine_name: str) -> str | None:
    key = normalize_machine_name(machine_name)
    return key if key in MACHINE_IMAGES else None