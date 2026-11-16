-- Zapytania weryfikujące po imporcie. Każde zapytanie zwraca jedną liczbę.
-- Program czyta ten plik i dodaje wyniki do raportu. Nazwę zapytania podaje komentarz name.

-- name: liczba_rekordow
SELECT COUNT(*) FROM employees;

-- name: duplikaty_pesel
SELECT COUNT(*) FROM (SELECT pesel FROM employees GROUP BY pesel HAVING COUNT(*) > 1);

-- name: duplikaty_email
SELECT COUNT(*) FROM (SELECT email FROM employees GROUP BY email HAVING COUNT(*) > 1);

-- name: puste_pola_wymagane
SELECT COUNT(*) FROM employees WHERE first_name IS NULL OR LENGTH(first_name) = 0 OR last_name IS NULL OR LENGTH(last_name) = 0 OR pesel IS NULL OR email IS NULL OR hire_date IS NULL;

-- name: kierownik_bez_rekordu
SELECT COUNT(*) FROM employees e WHERE e.manager_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM employees m WHERE m.id = e.manager_id);

-- name: data_zatrudnienia_w_przyszlosci
SELECT COUNT(*) FROM employees WHERE hire_date > CURRENT_DATE;

-- Zapytania do ręcznego uruchomienia (zwracają wiele wierszy):
-- SELECT unit, COUNT(*) FROM employees GROUP BY unit ORDER BY 2 DESC;
-- SELECT manager_id, COUNT(*) FROM employees WHERE manager_id IS NOT NULL GROUP BY manager_id;
