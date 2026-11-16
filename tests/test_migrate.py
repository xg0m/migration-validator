from datetime import date
from pathlib import Path

import pytest

from migrator.mapping import load_mapping, validate_mapping
from migrator.migrate import load_to_sqlite, parse_queries, process, read_csv, run_verification

BASE_DIR = Path(__file__).resolve().parent.parent
TODAY = date(2026, 11, 20)


@pytest.fixture(scope="module")
def mapping():
    return load_mapping(BASE_DIR / "config" / "mapping.yaml")


@pytest.fixture(scope="module")
def result(mapping):
    rows = read_csv(BASE_DIR / "sample_data" / "legacy_employees.csv")
    return process(rows, mapping, today=TODAY)


def pairs(result, severity):
    return {(issue.source_id, issue.code) for issue in result.issues if issue.severity == severity}


def test_liczba_wierszy(result):
    assert result.total == 22
    assert len(result.accepted) == 14
    assert len(result.rejected) == 8


def test_bledy_w_danych_przykladowych(result):
    expected = {
        ("13", "DUPLICATE"),
        ("14", "PESEL"),
        ("15", "EMAIL"),
        ("16", "REQUIRED"),
        ("17", "DATE"),
        ("19", "REQUIRED"),
        ("20", "DUPLICATE"),
        ("21", "ALLOWED"),
    }
    assert pairs(result, "ERROR") == expected


def test_ostrzezenia(result):
    assert pairs(result, "WARNING") == {("18", "DATE_FUTURE"), ("18", "REFERENCE")}


def test_normalizacja_tekstu_i_adresu_email(result):
    henryk = next(record for record in result.accepted if record["id"] == 22)
    assert henryk["first_name"] == "Henryk"
    assert henryk["email"] == "henryk.duda@example.edu.pl"


def test_daty_zapisane_w_formacie_iso(result):
    by_id = {record["id"]: record for record in result.accepted}
    assert by_id[2]["hire_date"] == "2018-03-12"
    assert by_id[4]["hire_date"] == "2021-10-01"


def test_import_i_weryfikacja_sql(mapping, result, tmp_path):
    db_path = tmp_path / "test.db"
    load_to_sqlite(db_path, mapping, result.accepted)
    checks = run_verification(db_path, BASE_DIR / "sql" / "verification.sql")
    assert checks["liczba_rekordow"] == len(result.accepted)
    assert checks["duplikaty_pesel"] == 0
    assert checks["duplikaty_email"] == 0
    assert checks["puste_pola_wymagane"] == 0
    assert checks["kierownik_bez_rekordu"] == 1
    assert checks["data_zatrudnienia_w_przyszlosci"] == 1


def test_parse_queries():
    text = """-- name: a
SELECT 1;
-- name: b
SELECT 2;
"""
    assert parse_queries(text) == [("a", "SELECT 1;"), ("b", "SELECT 2;")]


def test_mapowanie_odrzuca_niebezpieczna_nazwe_tabeli():
    rule = {"source": "A", "target": "a", "type": "text"}
    with pytest.raises(ValueError):
        validate_mapping({"table": "x; DROP TABLE y", "fields": [rule]})


def test_mapowanie_odrzuca_nieznany_typ():
    rule = {"source": "A", "target": "a", "type": "xml"}
    with pytest.raises(ValueError):
        validate_mapping({"table": "t", "fields": [rule]})
