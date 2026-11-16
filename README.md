# migration-validator

![Testy](https://github.com/xg0m/migration-validator/actions/workflows/tests.yml/badge.svg)

Narzędzie do walidacji i migracji danych pracowników z pliku CSV (eksport ze starego systemu kadrowego) do bazy SQLite. Projekt ćwiczy etap migracji danych we wdrożeniach systemów informatycznych. Dane w repozytorium są fikcyjne.

Powiązany projekt: [obieg-dokumentow-wdrozenie](https://github.com/xg0m/obieg-dokumentow-wdrozenie), czyli case study wdrożenia, w którym ta migracja dostarcza dane startowe.

## Co robi

1. Czyta plik CSV (separator `;`, kodowanie UTF-8).
2. Stosuje mapowanie z `config/mapping.yaml`: kolumna źródłowa, pole docelowe, typ, wymagalność, unikalność, słownik wartości.
3. Waliduje każdy wiersz i normalizuje wartości: spacje, wielkość liter w adresie e-mail, daty do formatu RRRR-MM-DD.
4. Ładuje poprawne wiersze do SQLite. Wiersze z błędem są odrzucane i opisane w raporcie.
5. Po imporcie uruchamia zapytania SQL z `sql/verification.sql`.
6. Zapisuje raport Excel z zakładkami Podsumowanie i Problemy.

## Szybki start

```bash
git clone https://github.com/xg0m/migration-validator.git
cd migration-validator
python -m venv venv
# Linux i macOS: source venv/bin/activate
# Windows (PowerShell): venv/Scripts/Activate.ps1
pip install -r requirements.txt
python main.py
pytest -v
```

Własne dane i mapowanie:

```bash
python main.py --input moje_dane.csv --mapping moje_mapowanie.yaml --report raport.xlsx
```

## Przykładowy wynik

Wynik działania na danych z `sample_data/legacy_employees.csv` (ten sam przebieg wykonuje GitHub Actions):

```text
Wiersze w pliku źródłowym: 22
Załadowane do bazy: 14
Odrzucone wiersze: 8
Błędy (ERROR): 9
Ostrzeżenia (WARNING): 2
SQL liczba_rekordow: 14
SQL duplikaty_pesel: 0
SQL duplikaty_email: 0
SQL puste_pola_wymagane: 0
SQL kierownik_bez_rekordu: 1
SQL data_zatrudnienia_w_przyszlosci: 1
```

Błędów jest 9, a wierszy odrzuconych 8, bo jeden wiersz (ID 19) ma dwa błędy. Liczba załadowanych rekordów w bazie (14) zgadza się z liczbą przyjętych wierszy: 22 - 8 = 14.

## Reguły walidacji

Błąd (ERROR) odrzuca wiersz. Ostrzeżenie (WARNING) nie odrzuca wiersza, ale trafia do raportu.

| Reguła w mapowaniu | Działanie | Kod | Poziom |
|---|---|---|---|
| required | Puste pole wymagane | REQUIRED | ERROR |
| type: int | Oczekiwana liczba całkowita | INT | ERROR |
| type: pesel | 11 cyfr i suma kontrolna (wagi 1-3-7-9) | PESEL | ERROR |
| type: email | Podstawowy format adresu, zamiana na małe litery | EMAIL | ERROR |
| type: date | Formaty RRRR-MM-DD, DD.MM.RRRR, DD/MM/RRRR, zapis w ISO | DATE | ERROR |
| unique | Wartość nie może się powtarzać | DUPLICATE | ERROR |
| allowed | Wartość musi należeć do słownika | ALLOWED | ERROR |
| not_future | Data z przyszłości | DATE_FUTURE | WARNING |
| references | Pole wskazuje rekord, którego nie ma w danych | REFERENCE | WARNING |

## Dane przykładowe

Plik zawiera 12 poprawnych wierszy i wiersze z celowo wstawionymi problemami:

| ID | Problem |
|---|---|
| 13 | Duplikat numeru PESEL (ten sam co ID 1) |
| 14 | Błędna suma kontrolna PESEL |
| 15 | Adres e-mail bez domeny |
| 16 | Brak numeru PESEL |
| 17 | Nieistniejąca data 31.02.2020 |
| 18 | Data zatrudnienia z przyszłości i kierownik o ID 99, którego nie ma. Ostrzeżenia, wiersz zostaje załadowany |
| 19 | Brak imienia i numeru PESEL |
| 20 | Duplikat adresu e-mail (ten sam co ID 2) |
| 21 | Jednostka spoza słownika |
| 22 | Zbędne spacje i wielkie litery w adresie e-mail. Poprawiane automatycznie |

## Weryfikacja SQL po imporcie

Zapytania są w `sql/verification.sql` i można je uruchomić ręcznie w dowolnym kliencie SQLite. Każde zwraca jedną liczbę.

| Zapytanie | Sprawdza | Oczekiwany wynik |
|---|---|---|
| liczba_rekordow | Liczbę rekordów w tabeli | Liczba przyjętych wierszy |
| duplikaty_pesel | Powtórzone numery PESEL | 0 |
| duplikaty_email | Powtórzone adresy e-mail | 0 |
| puste_pola_wymagane | Puste pola wymagane | 0 |
| kierownik_bez_rekordu | Kierownik wskazuje nieistniejącego pracownika | 0 (tu 1, to ostrzeżenie dla ID 18) |
| data_zatrudnienia_w_przyszlosci | Daty zatrudnienia z przyszłości | 0 (tu 1, to ostrzeżenie dla ID 18) |

## Struktura

```text
migration-validator/
  config/mapping.yaml          mapowanie kolumn i reguły pól
  sample_data/                 fikcyjny eksport ze starego systemu
  sql/verification.sql         zapytania weryfikujące po imporcie
  migrator/validators.py       PESEL, e-mail, daty, normalizacja tekstu
  migrator/mapping.py          wczytanie i sprawdzenie mapowania
  migrator/migrate.py          walidacja wierszy, import do SQLite, weryfikacja
  migrator/report.py           raport Excel
  tests/                       testy jednostkowe (pytest)
  main.py                      wiersz poleceń
```

## Decyzje i ograniczenia

- Każdy import tworzy tabelę od nowa (DROP i CREATE). Takie zachowanie pasuje do próbnych migracji na środowisku testowym. Migracja produkcyjna wymagałaby importu przyrostowego.
- Nazwy tabeli i kolumn pochodzą z mapowania i są sprawdzane (tylko bezpieczne identyfikatory). Wartości trafiają do bazy jako parametry zapytań.
- Walidacja PESEL obejmuje format i sumę kontrolną, bez sprawdzania zgodności z datą urodzenia.
- Narzędzie nie obsługuje synchronizacji z Active Directory ani integracji REST API.
- Poza PyYAML i openpyxl używa tylko biblioteki standardowej Pythona.

## Testy i CI

Testy (`pytest`) obejmują walidatory, przetwarzanie danych przykładowych, import do bazy i zapytania weryfikujące. GitHub Actions uruchamia testy oraz migrację na każdym pushu i zapisuje raport Excel jako artefakt przebiegu.

## Praca z narzędziami AI

Kod i dokumentacja powstawały z pomocą narzędzi AI. Weryfikuję je testami i czytam przed zatwierdzeniem. Reguły pracy z takimi narzędziami w tym repozytorium opisuje [AGENTS.md](AGENTS.md).

## Autor

Oliwier Sieniuc, [@xg0m](https://github.com/xg0m). Licencja MIT.
