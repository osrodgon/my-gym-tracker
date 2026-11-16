from datetime import date, datetime, timedelta
from io import BytesIO
from math import isfinite
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from ui.texts import EXPORT, IMPORT
from machine_images import MACHINE_IMAGES, get_machine_image_key


_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_MAX_REPS = 999


def _cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.get("t")

    if cell_type == "inlineStr":
        return "".join(
            node.text or ""
            for node in cell.findall(f".//{{{_NS}}}t")
        )

    value_element = cell.find(f"{{{_NS}}}v")
    value = value_element.text or "" if value_element is not None else ""

    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (ValueError, IndexError) as exc:
            raise ValueError("El archivo contiene una cadena de Excel no válida.") from exc

    return value

def _parse_excel_date(value: str) -> str:
    value = value.strip()

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        pass

    try:
        serial = float(value)
        if not isfinite(serial) or serial < 1:
            raise ValueError
        return (datetime(1899, 12, 30) + timedelta(days=serial)).date().isoformat()
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"Fecha no válida: {value}") from exc


def _parse_reps(value: str, machine_name: str) -> int:
    """Parse the reps cell, accepting Excel's `12` and `12.0` spellings."""
    try:
        numeric = float(value)
    except ValueError as exc:
        raise ValueError(
            IMPORT["invalid_reps"].format(machine=machine_name)
        ) from exc

    if (
        not isfinite(numeric)
        or not numeric.is_integer()
        or not 1 <= int(numeric) <= _MAX_REPS
    ):
        raise ValueError(
            IMPORT["invalid_reps"].format(machine=machine_name)
        )

    return int(numeric)


def _resolve_image_key(
    image_text: str,
    machine_name: str,
    has_image_column: bool,
) -> str | None:
    """Drawing for an imported machine.

    Workbooks without the `Imagen` column keep the 2.2.0 behaviour of deriving
    the drawing from the name. An unknown key degrades to "Sin imagen" instead of
    failing the whole import.
    """
    if not has_image_column:
        return get_machine_image_key(machine_name)
    return image_text if image_text in MACHINE_IMAGES else None


def parse_usage_workbook(
    workbook_bytes: bytes,
) -> tuple[list[tuple[str, str | None]], list[tuple[str, str, float, int | None]]]:
    try:
        with ZipFile(BytesIO(workbook_bytes)) as archive:
            worksheet = ET.fromstring(
                archive.read("xl/worksheets/sheet1.xml")
            )

            shared_strings = []
            if "xl/sharedStrings.xml" in archive.namelist():
                shared_root = ET.fromstring(
                    archive.read("xl/sharedStrings.xml")
                )
                shared_strings = [
                    "".join(
                        node.text or ""
                        for node in item.findall(f".//{{{_NS}}}t")
                    )
                    for item in shared_root.findall(f"{{{_NS}}}si")
                ]
    except (BadZipFile, KeyError, ET.ParseError) as exc:
        raise ValueError(
            "El archivo no es un Excel válido exportado desde la aplicación."
        ) from exc

    sheet_data = worksheet.find(f"{{{_NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("El Excel no contiene una hoja de datos válida.")

    rows = sheet_data.findall(f"{{{_NS}}}row")
    if not rows:
        raise ValueError("El Excel está vacío.")

    def read_row(row: ET.Element) -> dict[str, str]:
        values = {}
        for cell in row.findall(f"{{{_NS}}}c"):
            reference = cell.get("r", "")
            column = "".join(char for char in reference if char.isalpha())
            if column in {"A", "B", "C", "D", "E"}:
                values[column] = _cell_text(cell, shared_strings)
        return values

    headers = read_row(rows[0])
    header_values = [headers.get(column, "").strip() for column in "ABCDE"]
    expected_headers = list(EXPORT["headers"])

    # 3.0.0 workbooks carry the Imagen column, 2.2.0 stops at Repeticiones and
    # older ones at Peso. Each older shape stays importable.
    if header_values == expected_headers:
        has_reps_column = True
        has_image_column = True
    elif header_values[:4] == expected_headers[:4] and not header_values[4]:
        has_reps_column = True
        has_image_column = False
    elif header_values[:3] == expected_headers[:3] and not any(header_values[3:]):
        has_reps_column = False
        has_image_column = False
    else:
        raise ValueError(
            IMPORT["invalid_headers"].format(
                columns=", ".join(expected_headers)
            )
        )

    machines: dict[str, str | None] = {}
    usages: list[tuple[str, str, float, int | None]] = []

    for row in rows[1:]:
        values = read_row(row)
        usage_date = values.get("A", "").strip()
        machine_name = values.get("B", "").strip()
        weight_text = values.get("C", "").strip()
        reps_text = values.get("D", "").strip() if has_reps_column else ""
        image_text = values.get("E", "").strip() if has_image_column else ""

        if (
            not usage_date
            and not machine_name
            and not weight_text
            and not reps_text
        ):
            continue

        if not machine_name:
            raise ValueError(
                IMPORT["missing_machine"]
            )

        # The export writes the drawing only on the machine's first row, so the
        # key is taken from whichever row of that machine carries it.
        image_key = _resolve_image_key(image_text, machine_name, has_image_column)
        if machine_name not in machines or image_key is not None:
            machines[machine_name] = image_key

        # A blank date and blank weight indicate a machine that has not been used.
        if not usage_date:
            if weight_text or reps_text:
                raise ValueError(
                    IMPORT["usage_without_date"].format(machine=machine_name)
                )
            continue

        if not weight_text:
            raise ValueError(
                IMPORT["usage_without_weight"].format(machine=machine_name)
            )

        try:
            normalized_date = _parse_excel_date(usage_date)
            weight = float(weight_text)
        except ValueError as exc:
            raise ValueError(
                IMPORT["invalid_date_or_weight"].format(machine=machine_name)
            ) from exc

        if not isfinite(weight):
            raise ValueError(
                IMPORT["invalid_weight"].format(machine=machine_name)
            )

        reps = _parse_reps(reps_text, machine_name) if reps_text else None

        usages.append((normalized_date, machine_name, weight, reps))

    if not machines:
        raise ValueError(IMPORT["no_machines"])

    return list(machines.items()), usages
