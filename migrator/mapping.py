"""Wczytywanie i sprawdzanie pliku mapowania."""
import re

import yaml

IDENTIFIER_RE = re.compile(r"[a-z_][a-z0-9_]*")
VALID_TYPES = {"text", "int", "pesel", "email", "date"}


def load_mapping(path):
    """Wczytuje mapowanie z pliku YAML i sprawdza jego poprawność."""
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    validate_mapping(data)
    return data


def validate_mapping(data):
    """Zgłasza ValueError, gdy mapowanie jest niepoprawne.

    Nazwy tabeli i kolumn trafiają do SQL, więc muszą być bezpiecznymi identyfikatorami.
    """
    if not isinstance(data, dict) or "table" not in data or not data.get("fields"):
        raise ValueError("Mapowanie musi zawierać klucze table i fields")
    if not IDENTIFIER_RE.fullmatch(str(data["table"])):
        raise ValueError("Niepoprawna nazwa tabeli: " + str(data["table"]))
    targets = set()
    for rule in data["fields"]:
        for key in ("source", "target", "type"):
            if key not in rule:
                raise ValueError("Brak klucza " + key + " w regule: " + str(rule))
        if rule["type"] not in VALID_TYPES:
            raise ValueError("Nieznany typ pola: " + str(rule["type"]))
        if not IDENTIFIER_RE.fullmatch(str(rule["target"])):
            raise ValueError("Niepoprawna nazwa kolumny: " + str(rule["target"]))
        if rule["target"] in targets:
            raise ValueError("Powtórzona kolumna docelowa: " + str(rule["target"]))
        targets.add(rule["target"])
    for rule in data["fields"]:
        reference = rule.get("references")
        if reference and reference not in targets:
            raise ValueError("Pole references wskazuje nieistniejącą kolumnę: " + str(reference))
