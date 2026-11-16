"""Generowanie raportu z migracji w formacie Excel."""
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF")
SEVERITY_FILL = {
    "ERROR": PatternFill("solid", fgColor="F8CBAD"),
    "WARNING": PatternFill("solid", fgColor="FFE699"),
}


def _style_header(sheet, row_number):
    for cell in sheet[row_number]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(vertical="center")


def _fit_columns(sheet):
    for column_cells in sheet.columns:
        longest = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        sheet.column_dimensions[get_column_letter(column_cells[0].column)].width = min(longest + 2, 80)


def write_report(path, summary, issues, verification):
    """Zapisuje raport z dwiema zakładkami: Podsumowanie i Problemy."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Podsumowanie"
    sheet.append(["Wskaźnik", "Wartość"])
    _style_header(sheet, 1)
    for name, value in summary.items():
        sheet.append([name, value])
    sheet.append([])
    sheet.append(["Weryfikacja SQL po imporcie", "Wynik"])
    _style_header(sheet, sheet.max_row)
    for name, value in verification.items():
        sheet.append([name, value])
    _fit_columns(sheet)

    problems = workbook.create_sheet("Problemy")
    problems.append(["Wiersz w pliku", "ID w źródle", "Pole", "Poziom", "Kod", "Opis"])
    _style_header(problems, 1)
    for issue in issues:
        problems.append([issue.row, issue.source_id, issue.column, issue.severity, issue.code, issue.message])
        fill = SEVERITY_FILL.get(issue.severity)
        if fill:
            for cell in problems[problems.max_row]:
                cell.fill = fill
    problems.freeze_panes = "A2"
    _fit_columns(problems)
    workbook.save(path)
