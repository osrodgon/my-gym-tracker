from io import BytesIO
from math import isfinite
from typing import Iterable, Sequence
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_DOCUMENT_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
_XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("", _MAIN_NS)
ET.register_namespace("r", _DOCUMENT_REL_NS)


def build_usage_history_workbook(
    rows: Iterable[Sequence[str | float | None]],
) -> bytes:
    workbook_bytes = BytesIO()

    worksheet = ET.Element(f"{{{_MAIN_NS}}}worksheet")
    sheet_data = ET.SubElement(worksheet, f"{{{_MAIN_NS}}}sheetData")
    _append_row(sheet_data, 1, ("Fecha", "Máquina", "Peso (kg)"))

    for row_number, row in enumerate(rows, start=2):
        _append_row(sheet_data, row_number, row)

    workbook = ET.Element(f"{{{_MAIN_NS}}}workbook")
    sheets = ET.SubElement(workbook, f"{{{_MAIN_NS}}}sheets")
    ET.SubElement(
        sheets,
        f"{{{_MAIN_NS}}}sheet",
        {
            "name": "Historial",
            "sheetId": "1",
            f"{{{_DOCUMENT_REL_NS}}}id": "rId1",
        },
    )

    root_relationships = ET.Element(
        f"{{{_PACKAGE_REL_NS}}}Relationships"
    )
    ET.SubElement(
        root_relationships,
        f"{{{_PACKAGE_REL_NS}}}Relationship",
        {
            "Id": "rId1",
            "Type": (
                "http://schemas.openxmlformats.org/officeDocument/2006/"
                "relationships/officeDocument"
            ),
            "Target": "xl/workbook.xml",
        },
    )

    workbook_relationships = ET.Element(
        f"{{{_PACKAGE_REL_NS}}}Relationships"
    )
    ET.SubElement(
        workbook_relationships,
        f"{{{_PACKAGE_REL_NS}}}Relationship",
        {
            "Id": "rId1",
            "Type": (
                "http://schemas.openxmlformats.org/officeDocument/2006/"
                "relationships/worksheet"
            ),
            "Target": "worksheets/sheet1.xml",
        },
    )

    content_types = ET.Element(f"{{{_CONTENT_TYPES_NS}}}Types")
    ET.SubElement(
        content_types,
        f"{{{_CONTENT_TYPES_NS}}}Default",
        {
            "Extension": "rels",
            "ContentType": "application/vnd.openxmlformats-package.relationships+xml",
        },
    )
    ET.SubElement(
        content_types,
        f"{{{_CONTENT_TYPES_NS}}}Default",
        {"Extension": "xml", "ContentType": "application/xml"},
    )
    ET.SubElement(
        content_types,
        f"{{{_CONTENT_TYPES_NS}}}Override",
        {
            "PartName": "/xl/workbook.xml",
            "ContentType": (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet.main+xml"
            ),
        },
    )
    ET.SubElement(
        content_types,
        f"{{{_CONTENT_TYPES_NS}}}Override",
        {
            "PartName": "/xl/worksheets/sheet1.xml",
            "ContentType": (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.worksheet+xml"
            ),
        },
    )

    with ZipFile(workbook_bytes, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            ET.tostring(content_types, encoding="utf-8", xml_declaration=True),
        )
        archive.writestr(
            "_rels/.rels",
            ET.tostring(root_relationships, encoding="utf-8", xml_declaration=True),
        )
        archive.writestr(
            "xl/workbook.xml",
            ET.tostring(workbook, encoding="utf-8", xml_declaration=True),
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            ET.tostring(workbook_relationships, encoding="utf-8", xml_declaration=True),
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            ET.tostring(worksheet, encoding="utf-8", xml_declaration=True),
        )

    return workbook_bytes.getvalue()


def _append_row(
    sheet_data: ET.Element,
    row_number: int,
    values: Sequence[str | float | None],
) -> None:
    row_element = ET.SubElement(
        sheet_data,
        f"{{{_MAIN_NS}}}row",
        {"r": str(row_number)},
    )

    for column, value in zip(("A", "B", "C"), values):
        if value is None:
            continue

        cell = ET.SubElement(
            row_element,
            f"{{{_MAIN_NS}}}c",
            {"r": f"{column}{row_number}"},
        )

        if isinstance(value, (int, float)):
            numeric_value = float(value)
            if not isfinite(numeric_value):
                raise ValueError("Excel cells cannot contain infinite or NaN values.")
            cell.set("t", "n")
            ET.SubElement(cell, f"{{{_MAIN_NS}}}v").text = str(value)
        else:
            cell.set("t", "inlineStr")
            text = ET.SubElement(
                ET.SubElement(cell, f"{{{_MAIN_NS}}}is"),
                f"{{{_MAIN_NS}}}t",
            )
            text.set(f"{{{_XML_NS}}}space", "preserve")
            text.text = value
