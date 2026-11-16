"""Logika migracji: czytanie CSV, walidacja wierszy, import do SQLite i weryfikacja."""
import csv
import sqlite3
from contextlib import closing
from dataclasses import dataclass, field
from datetime import date

from . import validators as v
from .mapping import validate_mapping

ERROR = "ERROR"
WARNING = "WARNING"


@dataclass
class Issue:
    """Pojedynczy problem znaleziony w danych."""

    row: int
    source_id: str
    column: str
    severity: str
    code: str
    message: str


@dataclass
class Result:
    """Wynik walidacji: rekordy gotowe do importu, odrzucone wiersze i problemy."""

    total: int
    accepted: list = field(default_factory=list)
    rejected: list = field(default_factory=list)
    issues: list = field(default_factory=list)


def read_csv(path, delimiter=";", encoding="utf-8-sig"):
    """Czyta plik CSV i zwraca listę słowników. Pierwszy wiersz pliku to nagłówek."""
    with open(path, newline="", encoding=encoding) as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def _convert(rule, text, today):
    """Zamienia tekst na wartość docelową. Zwraca (wartość, lista problemów).

    Problem to krotka (poziom, kod, opis).
    """
    kind = rule["type"]
    if text == "":
        if rule.get("required"):
            return None, [(ERROR, "REQUIRED", "Pole wymagane jest puste")]
        return None, []
    if kind == "int":
        if not (text.isascii() and text.isdigit()):
            return None, [(ERROR, "INT", "Oczekiwano liczby całkowitej: " + text)]
        value = int(text)
    elif kind == "pesel":
        if not v.is_valid_pesel(text):
            return None, [(ERROR, "PESEL", "Błędny format lub suma kontrolna PESEL: " + text)]
        value = text
    elif kind == "email":
        value = text.lower()
        if not v.is_valid_email(value):
            return None, [(ERROR, "EMAIL", "Błędny adres e-mail: " + text)]
    elif kind == "date":
        parsed = v.parse_date(text)
        if parsed is None:
            return None, [(ERROR, "DATE", "Nie rozpoznano daty: " + text)]
        problems = []
        if rule.get("not_future") and parsed > today:
            problems.append((WARNING, "DATE_FUTURE", "Data z przyszłości: " + parsed.isoformat()))
        return parsed.isoformat(), problems
    else:
        value = text
    allowed = rule.get("allowed")
    if allowed and value not in allowed:
        return None, [(ERROR, "ALLOWED", "Wartość spoza słownika: " + str(value))]
    return value, []


def process(rows, mapping, today=None):
    """Waliduje wiersze. Błąd (ERROR) odrzuca wiersz, ostrzeżenie (WARNING) nie."""
    today = today or date.today()
    rules = mapping["fields"]
    result = Result(total=len(rows))
    seen = {rule["target"]: {} for rule in rules if rule.get("unique")}
    candidates = []
    for index, raw in enumerate(rows):
        row_no = index + 2
        source_id = v.normalize_text(raw.get(rules[0]["source"]))
        record = {}
        row_issues = []
        for rule in rules:
            target = rule["target"]
            text = v.normalize_text(raw.get(rule["source"]))
            value, problems = _convert(rule, text, today)
            record[target] = value
            for severity, code, message in problems:
                row_issues.append(Issue(row_no, source_id, target, severity, code, message))
            if value is not None and target in seen:
                first_row = seen[target].setdefault(value, row_no)
                if first_row != row_no:
                    message = f"Duplikat wartości {value}, pierwszy raz w wierszu {first_row}"
                    row_issues.append(Issue(row_no, source_id, target, ERROR, "DUPLICATE", message))
        result.issues.extend(row_issues)
        if any(issue.severity == ERROR for issue in row_issues):
            result.rejected.append(row_no)
        else:
            candidates.append((row_no, source_id, record))
    _check_references(rules, candidates, result)
    result.accepted = [record for _, _, record in candidates]
    result.issues.sort(key=lambda issue: (issue.row, issue.column))
    return result


def _check_references(rules, candidates, result):
    """Dodaje ostrzeżenie, gdy pole wskazuje rekord, którego nie ma wśród przyjętych."""
    for rule in rules:
        reference = rule.get("references")
        if not reference:
            continue
        known = {record[reference] for _, _, record in candidates}
        for row_no, source_id, record in candidates:
            value = record[rule["target"]]
            if value is not None and value not in known:
                message = f"Brak rekordu z {reference} równym {value}"
                result.issues.append(Issue(row_no, source_id, rule["target"], WARNING, "REFERENCE", message))


def load_to_sqlite(db_path, mapping, records):
    """Tworzy tabelę od nowa i ładuje rekordy. Nazwy pochodzą ze zweryfikowanego mapowania."""
    validate_mapping(mapping)
    table = mapping["table"]
    rules = mapping["fields"]
    names = [rule["target"] for rule in rules]
    definitions = []
    for rule in rules:
        definition = rule["target"] + (" INTEGER" if rule["type"] == "int" else " TEXT")
        if rule.get("required"):
            definition += " NOT NULL"
        if rule.get("unique"):
            definition += " UNIQUE"
        definitions.append(definition)
    column_list = ", ".join(names)
    placeholders = ", ".join(["?"] * len(names))
    rows = [tuple(record[name] for name in names) for record in records]
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("DROP TABLE IF EXISTS " + table)
        conn.execute("CREATE TABLE " + table + " (" + ", ".join(definitions) + ")")
        conn.executemany("INSERT INTO " + table + " (" + column_list + ") VALUES (" + placeholders + ")", rows)
        conn.commit()


def parse_queries(text):
    """Dzieli plik SQL na zapytania. Każde poprzedza komentarz -- name: nazwa."""
    queries = []
    name = None
    lines = []
    for line in text.splitlines():
        if line.startswith("-- name:"):
            if name and lines:
                queries.append((name, " ".join(lines)))
            name = line.split(":", 1)[1].strip()
            lines = []
        elif name and line.strip() and not line.startswith("--"):
            lines.append(line.strip())
    if name and lines:
        queries.append((name, " ".join(lines)))
    return queries


def run_verification(db_path, sql_path):
    """Uruchamia zapytania weryfikujące z pliku SQL i zwraca słownik nazwa -> liczba."""
    with open(sql_path, encoding="utf-8") as handle:
        queries = parse_queries(handle.read())
    results = {}
    with closing(sqlite3.connect(db_path)) as conn:
        for name, sql in queries:
            results[name] = conn.execute(sql).fetchone()[0]
    return results
