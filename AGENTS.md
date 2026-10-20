# Zasady pracy w repozytorium b1-toolkit
- Odpowiadaj po polsku, maksymalnie 10 zdań.
- Kod i nazwy techniczne zgodnie ze specyfikacją, komentarze i docstringi po polsku.
- Źródłem prawdy jest docs/SPECYFIKACJA_API.md - nie zmieniaj kontraktu API bez zgody.
- Najpierw pokaż plan, potem zmieniaj pliki. Zmiany rób małymi krokami.
- Najpierw testy (python -m unittest), potem kod. Po zmianie uruchom testy.
- Nie instaluj niczego bez pytania. Nie dotykaj .env, .git, *.db.
- Dane tylko fikcyjne. Nie dodawaj haseł ani tokenów do plików.
- Zapytania SQL zawsze z parametrami (znaki ?), nigdy sklejanie tekstu z danych.
- Gdy nie jesteś pewien, powiedz to wprost.