"""Walidatory pól używane podczas migracji danych."""
import re
from datetime import datetime

PESEL_WEIGHTS = (1, 3, 7, 9, 1, 3, 7, 9, 1, 3)
PESEL_RE = re.compile(r"[0-9]{11}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+([.][A-Za-z0-9-]+)*[.][A-Za-z]{2,}")
DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y")


def normalize_text(value):
    """Usuwa skrajne spacje i zamienia ciągi białych znaków na jedną spację."""
    if value is None:
        return ""
    return " ".join(str(value).split())


def is_valid_pesel(value):
    """Sprawdza format i sumę kontrolną numeru PESEL (wagi 1-3-7-9)."""
    if not value or not PESEL_RE.fullmatch(value):
        return False
    digits = [int(char) for char in value]
    total = sum(weight * digit for weight, digit in zip(PESEL_WEIGHTS, digits[:10]))
    return (10 - total % 10) % 10 == digits[10]


def is_valid_email(value):
    """Sprawdza podstawowy format adresu e-mail."""
    return bool(value) and EMAIL_RE.fullmatch(value) is not None


def parse_date(value):
    """Zamienia tekst na datę. Obsługuje formaty RRRR-MM-DD, DD.MM.RRRR i DD/MM/RRRR. Zwraca None, gdy się nie da."""
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date()
        except (ValueError, TypeError):
            continue
    return None
