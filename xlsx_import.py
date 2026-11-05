from datetime import date, datetime, timedelta
from io import BytesIO
from math import isfinite
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


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


def parse_usage_workbook(
    workbook_bytes: bytes,
) -> tuple[list[str], list[tuple[str, str, float]]]:
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
            if column in {"A", "B", "C"}:
                values[column] = _cell_text(cell, shared_strings)
        return values

    headers = read_row(rows[0])
    if [headers.get(column, "") for column in ("A", "B", "C")] != [
        "Fecha",
        "Máquina",
        "Peso (kg)",
    ]:
        raise ValueError(
            "Las columnas deben ser: Fecha, Máquina y Peso (kg)."
        )

    machines: dict[str, None] = {}
    usages: list[tuple[str, str, float]] = []

    for row in rows[1:]:
        values = read_row(row)
        usage_date = values.get("A", "").strip()
        machine_name = values.get("B", "").strip()
        weight_text = values.get("C", "").strip()

        if not usage_date and not machine_name and not weight_text:
            continue

        if not machine_name:
            raise ValueError("Hay una fila con datos pero sin nombre de máquina.")

        machines.setdefault(machine_name, None)

        # A blank date and blank weight indicate a machine that has not been used.
        if not usage_date:
            if weight_text:
                raise ValueError(
                    f"La máquina «{machine_name}» tiene peso pero no fecha."
                )
            continue

        if not weight_text:
            raise ValueError(
                f"La máquina «{machine_name}» tiene fecha pero no peso."
            )

        try:
            normalized_date = _parse_excel_date(usage_date)
            weight = float(weight_text)
        except ValueError as exc:
            raise ValueError(
                f"Fecha o peso no válido para la máquina «{machine_name}»."
            ) from exc

        if not isfinite(weight):
            raise ValueError(
                f"El peso de «{machine_name}» debe ser un número válido."
            )

        usages.append((normalized_date, machine_name, weight))

    if not machines:
        raise ValueError("El Excel no contiene ninguna máquina.")

    return list(machines), usages
