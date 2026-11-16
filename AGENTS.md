# Reguły pracy z narzędziami AI w tym repozytorium

Plik dla narzędzi AI w wierszu poleceń (Claude Code, Gemini CLI, Codex CLI) i dla osób współpracujących.

## Kontekst

Narzędzie w Pythonie 3.12 do walidacji danych pracowników z CSV i importu do SQLite. Dane w repozytorium są fikcyjne.

## Reguły

- Nie dodawaj prawdziwych danych osobowych do katalogu sample_data.
- Nazwy tabeli i kolumn bierz tylko ze zweryfikowanego mapowania. Wartości przekazuj zawsze jako parametry zapytania.
- Każda zmiana reguły walidacji wymaga testu w katalogu tests.
- Nie dodawaj zależności poza requirements.txt bez uzasadnienia.
- Komunikaty dla użytkownika pisz po polsku.

## Sposób pracy

1. Przeczytaj README i config/mapping.yaml.
2. Zaplanuj zmianę w krokach. Najpierw napisz test, potem kod.
3. Uruchom pytest -v oraz python main.py.
4. Sprawdź zmiany i wynik ręcznie przed zatwierdzeniem. Odpowiedzi AI traktuj jako szkic.

## Polecenia

- Testy: pytest -v
- Migracja na danych przykładowych: python main.py
