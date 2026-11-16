"""Narzędzie wiersza poleceń: walidacja danych pracowników i import do SQLite."""
import argparse
from pathlib import Path

from migrator.mapping import load_mapping
from migrator.migrate import load_to_sqlite, process, read_csv, run_verification
from migrator.report import write_report

BASE_DIR = Path(__file__).resolve().parent


def build_parser():
    parser = argparse.ArgumentParser(description="Walidacja i migracja danych pracowników z CSV do SQLite.")
    parser.add_argument("--input", default=str(BASE_DIR / "sample_data" / "legacy_employees.csv"), help="plik CSV ze starego systemu")
    parser.add_argument("--mapping", default=str(BASE_DIR / "config" / "mapping.yaml"), help="plik mapowania YAML")
    parser.add_argument("--sql", default=str(BASE_DIR / "sql" / "verification.sql"), help="zapytania weryfikujące po imporcie")
    parser.add_argument("--db", default=str(BASE_DIR / "output" / "migration.db"), help="docelowa baza SQLite")
    parser.add_argument("--report", default=str(BASE_DIR / "output" / "raport_migracji.xlsx"), help="raport w Excelu")
    parser.add_argument("--delimiter", default=";", help="separator kolumn w CSV")
    parser.add_argument("--encoding", default="utf-8-sig", help="kodowanie pliku CSV")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    mapping = load_mapping(args.mapping)
    rows = read_csv(args.input, args.delimiter, args.encoding)
    result = process(rows, mapping)
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    load_to_sqlite(args.db, mapping, result.accepted)
    verification = run_verification(args.db, args.sql)
    errors = sum(1 for issue in result.issues if issue.severity == "ERROR")
    warnings = sum(1 for issue in result.issues if issue.severity == "WARNING")
    summary = {
        "Wiersze w pliku źródłowym": result.total,
        "Załadowane do bazy": len(result.accepted),
        "Odrzucone wiersze": len(result.rejected),
        "Błędy (ERROR)": errors,
        "Ostrzeżenia (WARNING)": warnings,
    }
    write_report(args.report, summary, result.issues, verification)
    for name, value in summary.items():
        print(f"{name}: {value}")
    for name, value in verification.items():
        print(f"SQL {name}: {value}")
    print(f"Baza: {args.db}")
    print(f"Raport: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
