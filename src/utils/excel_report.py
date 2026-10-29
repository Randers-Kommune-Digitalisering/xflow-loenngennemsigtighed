"""Filter hourly-paid employee sheets from Excel reports."""

import logging
from io import BytesIO
from xml.etree import ElementTree
from zipfile import ZipFile
from openpyxl import load_workbook

logger = logging.getLogger(__name__)


def _repair_sheet_visibility(excel_bytes: bytes) -> BytesIO:
    """
    Repair invalid sheet visibility metadata in an Excel workbook.

    :param excel_bytes: Excel workbook as bytes.
    :return: A readable byte stream containing the repaired or original workbook.
    """
    source = BytesIO(excel_bytes)
    with ZipFile(source) as archive:
        workbook_xml = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        invalid_states = 0
        for sheet in workbook_xml.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet"):
            if sheet.get("state", "visible") not in {"visible", "hidden", "veryHidden"}:
                sheet.attrib.pop("state")
                invalid_states += 1

        if not invalid_states:
            source.seek(0)
            return source

        repaired = BytesIO()
        with ZipFile(repaired, "w") as copy:
            for entry in archive.infolist():
                contents = (
                    ElementTree.tostring(workbook_xml, encoding="utf-8")
                    if entry.filename == "xl/workbook.xml"
                    else archive.read(entry)
                )
                copy.writestr(entry, contents)

    logger.debug("Excel workbook: ignored invalid sheet visibility metadata on %s sheets", invalid_states)
    repaired.seek(0)
    return repaired


def filter_monthly_paid_sheets(excel_bytes: bytes) -> bytes | None:
    """
    Remove hourly-paid employee sheets from an Excel report.

    :param excel_bytes: Excel workbook as bytes.
    :return: Filtered workbook bytes, original bytes if no sheets are removed,
        or None if all sheets belong to hourly-paid employees.
    :raises ValueError: If the workbook has no sheets or contains invalid employee data.
    """
    workbook = load_workbook(_repair_sheet_visibility(excel_bytes=excel_bytes))
    try:
        if not workbook.worksheets:
            raise ValueError("Excel report has no sheets")

        hourly_sheets = []
        for sheet in workbook.worksheets:
            header = sheet["Q2"].value  # "Medarbejdernummer" in Q2 for monthly-paid employees
            if not isinstance(header, str) or header.strip().casefold() != "medarbejdernummer":
                raise ValueError("Excel report is missing Medarbejdernummer in Q2")

            value = sheet["Q3"].value  # The employee number in Q3 for monthly-paid employees
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise ValueError("Excel report has no valid employee number in Q3")

            number = str(int(value)) if isinstance(value, float) and value.is_integer() else str(value).strip()
            if not number.isdigit():
                raise ValueError("Excel report has no valid employee number in Q3")

            if number.startswith(("7", "8", "9")):  # Hourly-paid employee numbers start with 7, 8, or 9
                hourly_sheets.append(sheet)

        if len(hourly_sheets) == len(workbook.worksheets):
            return None

        if not hourly_sheets:
            return excel_bytes

        for sheet in hourly_sheets:
            workbook.remove(sheet)

        filtered = BytesIO()
        workbook.save(filtered)
        return filtered.getvalue()
    finally:
        workbook.close()
