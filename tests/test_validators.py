from datetime import date

import pytest

from migrator import validators as v


@pytest.mark.parametrize("pesel", ["44051401359", "85031512344", "90070812344"])
def test_poprawny_pesel(pesel):
    assert v.is_valid_pesel(pesel)


@pytest.mark.parametrize("pesel", ["", None, "123", "44051401358", "4405140135a", "12345678901"])
def test_niepoprawny_pesel(pesel):
    assert not v.is_valid_pesel(pesel)


@pytest.mark.parametrize("email", ["jan.kowalski@example.edu.pl", "a@b.pl"])
def test_poprawny_email(email):
    assert v.is_valid_email(email)


@pytest.mark.parametrize("email", ["", None, "brak-malpy", "jan@", "@example.pl", "jan@example"])
def test_niepoprawny_email(email):
    assert not v.is_valid_email(email)


def test_parse_date_obsluguje_trzy_formaty():
    assert v.parse_date("2020-02-29") == date(2020, 2, 29)
    assert v.parse_date("12.03.2018") == date(2018, 3, 12)
    assert v.parse_date("01/10/2021") == date(2021, 10, 1)


@pytest.mark.parametrize("value", ["", None, "31.02.2020", "2021-13-01", "abc"])
def test_parse_date_niepoprawna(value):
    assert v.parse_date(value) is None


def test_normalize_text():
    assert v.normalize_text("  Jan   Kowalski ") == "Jan Kowalski"
    assert v.normalize_text(None) == ""
